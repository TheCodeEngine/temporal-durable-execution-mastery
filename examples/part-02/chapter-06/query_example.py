"""
Query Example - Progress Tracking

Chapter: 6 - Kommunikation (Signale und Queries)
Demonstrates: Read-only Queries für Progress Monitoring
"""

import asyncio
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List
from datetime import timedelta
from enum import Enum

sys.path.append(str(Path(__file__).parent.parent.parent.parent / "shared"))

from temporalio import workflow, activity
from temporalio.client import Client
from shared.temporal_helpers import create_temporal_client
from shared.examples_common import setup_logging
import logging


class ProcessingStatus(Enum):
    INITIALIZING = "initializing"
    PROCESSING = "processing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"


@dataclass
class ProcessingProgress:
    """Query-Rückgabewert mit vollständiger Info"""
    status: ProcessingStatus
    items_processed: int
    total_items: int
    percent_complete: float
    current_step: str
    errors: int


@activity.defn
async def process_item(item_id: int) -> str:
    """Simuliert Item-Verarbeitung"""
    activity.logger.info(f"Processing item {item_id}")
    await asyncio.sleep(0.5)  # Simuliert Arbeit
    return f"result-{item_id}"


@workflow.defn
class DataProcessingWorkflow:
    """Workflow mit Query-basiertem Progress Tracking"""

    @workflow.init
    def __init__(self) -> None:
        self.status = ProcessingStatus.INITIALIZING
        self.items_processed = 0
        self.total_items = 0
        self.current_step = "Initialization"
        self.errors = 0
        self.results: List[str] = []

    @workflow.query
    def get_status(self) -> str:
        """Einfacher Status-Query"""
        return self.status.value

    @workflow.query
    def get_progress(self) -> ProcessingProgress:
        """Detaillierter Progress-Query"""
        return ProcessingProgress(
            status=self.status,
            items_processed=self.items_processed,
            total_items=self.total_items,
            percent_complete=(
                (self.items_processed / self.total_items * 100)
                if self.total_items > 0 else 0
            ),
            current_step=self.current_step,
            errors=self.errors
        )

    @workflow.query
    def get_items_remaining(self) -> int:
        """Berechneter Query-Wert"""
        return self.total_items - self.items_processed

    @workflow.query
    def get_results(self) -> List[str]:
        """Alle verarbeiteten Results"""
        return self.results

    @workflow.run
    async def run(self, total_items: int) -> str:
        """Verarbeite Items mit Progress Tracking"""
        self.total_items = total_items
        self.status = ProcessingStatus.PROCESSING

        workflow.logger.info(f"Starting processing of {total_items} items")

        # Items verarbeiten
        for i in range(total_items):
            self.current_step = f"Processing item {i+1}/{total_items}"

            try:
                result = await workflow.execute_activity(
                    process_item,
                    i,
                    start_to_close_timeout=timedelta(seconds=10),
                )
                self.results.append(result)
                self.items_processed = i + 1

            except Exception as e:
                workflow.logger.error(f"Error processing item {i}: {e}")
                self.errors += 1

            # Log Progress bei jedem 10. Item
            if (i + 1) % 10 == 0:
                workflow.logger.info(
                    f"Progress: {self.items_processed}/{self.total_items} "
                    f"({self.items_processed/self.total_items*100:.0f}%)"
                )

        # Finalisierung
        self.status = ProcessingStatus.FINALIZING
        self.current_step = "Finalizing results"
        await asyncio.sleep(timedelta(seconds=1))

        self.status = ProcessingStatus.COMPLETED
        self.current_step = "Completed"

        workflow.logger.info(
            f"Processing completed: {self.items_processed} items, "
            f"{self.errors} errors"
        )

        return f"Processed {self.items_processed} items with {self.errors} errors"


async def run_query_example():
    """Query-Beispiel: Progress Monitoring"""
    setup_logging()
    logging.info("=== Query Example: Progress Tracking ===\n")

    client = await create_temporal_client()

    # Workflow starten
    workflow_id = "data-processing-001"
    total_items = 50

    logging.info(f"1. Starting data processing workflow ({total_items} items)...")
    handle = await client.start_workflow(
        DataProcessingWorkflow.run,
        total_items,
        id=workflow_id,
        task_queue="book-examples",
    )
    logging.info(f"   Workflow started: {workflow_id}\n")

    # Progress Monitoring mit Queries
    logging.info("2. Monitoring progress with queries...")
    last_percent = 0

    while True:
        try:
            # Detaillierter Progress-Query
            progress = await handle.query(DataProcessingWorkflow.get_progress)

            # Nur loggen bei Fortschritt
            current_percent = int(progress.percent_complete)
            if current_percent > last_percent and current_percent % 10 == 0:
                logging.info(
                    f"   Progress: {progress.percent_complete:.1f}% - "
                    f"{progress.current_step}"
                )
                last_percent = current_percent

            # Status-Check
            status = await handle.query(DataProcessingWorkflow.get_status)
            if status == "completed":
                logging.info("   ✓ Processing completed\n")
                break

            # Prüfe ob Workflow fertig (mit kurzem Timeout)
            result = await handle.result(timeout=0.1)
            break

        except asyncio.TimeoutError:
            # Workflow läuft noch
            await asyncio.sleep(1)

    # Final Progress abfragen
    logging.info("3. Querying final results...")
    final_progress = await handle.query(DataProcessingWorkflow.get_progress)
    results = await handle.query(DataProcessingWorkflow.get_results)

    logging.info(f"   Items processed: {final_progress.items_processed}")
    logging.info(f"   Errors: {final_progress.errors}")
    logging.info(f"   Results count: {len(results)}\n")

    print(f"\n🎉 Processing completed: {final_progress.items_processed} items processed\n")


async def run_query_on_completed_workflow():
    """Query auf abgeschlossenem Workflow (innerhalb Retention)"""
    setup_logging()
    logging.info("=== Query Example: Query on Completed Workflow ===\n")

    client = await create_temporal_client()

    # Workflow starten und abschließen
    workflow_id = "data-processing-002"
    handle = await client.start_workflow(
        DataProcessingWorkflow.run,
        20,  # Wenige Items für schnelles Testen
        id=workflow_id,
        task_queue="book-examples",
    )

    # Auf Completion warten
    result = await handle.result()
    logging.info(f"Workflow completed: {result}\n")

    # Query NACH Workflow-Ende (funktioniert innerhalb Retention!)
    logging.info("Querying workflow AFTER completion...")
    final_progress = await handle.query(DataProcessingWorkflow.get_progress)
    results = await handle.query(DataProcessingWorkflow.get_results)

    logging.info(f"   Final status: {final_progress.status.value}")
    logging.info(f"   Results: {len(results)} items\n")

    print(f"\n✓ Query on completed workflow successful!\n")


if __name__ == "__main__":
    # Progress Monitoring Beispiel
    asyncio.run(run_query_example())

    # Uncomment für Query-on-Completed Beispiel:
    # asyncio.run(run_query_on_completed_workflow())
