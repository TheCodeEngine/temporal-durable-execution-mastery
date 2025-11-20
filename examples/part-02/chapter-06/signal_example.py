"""
Signal Example - Approval Workflow

Chapter: 6 - Kommunikation (Signale und Queries)
Demonstrates: Asynchrone Signal-basierte Genehmigung
"""

import asyncio
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from datetime import timedelta, datetime, timezone

# Add project root to path for shared utilities
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from temporalio import workflow
from temporalio.client import Client
from shared.temporal_helpers import create_temporal_client
from shared.examples_common import setup_logging
import logging


@dataclass
class ApprovalInput:
    """Typsichere Signal-Daten"""
    approver_name: str
    approved: bool
    comment: str = ""


@workflow.defn
class ApprovalWorkflow:
    """Workflow mit Signal-basierter Genehmigung"""

    @workflow.init
    def __init__(self, request_id: str) -> None:
        # WICHTIG: @workflow.init garantiert Ausführung vor Signal Handlern
        self.request_id = request_id
        self.approved: Optional[bool] = None
        self.approver_name: Optional[str] = None
        self.comment: str = ""
        self.start_time = datetime.now(timezone.utc)

    @workflow.signal
    def approve(self, input: ApprovalInput) -> None:
        """Signal Handler - ändert Workflow-Zustand"""
        self.approved = input.approved
        self.approver_name = input.approver_name
        self.comment = input.comment

        workflow.logger.info(
            f"Approval decision received from {input.approver_name}: "
            f"{'approved' if input.approved else 'rejected'}"
        )

    @workflow.run
    async def run(self, request_id: str) -> str:
        """Wartet auf Signal via wait_condition"""
        workflow.logger.info(f"Waiting for approval on request {self.request_id}")

        # Warten bis Signal empfangen wurde (max 7 Tage)
        try:
            await workflow.wait_condition(
                lambda: self.approved is not None,
                timeout=timedelta(days=7)
            )
        except asyncio.TimeoutError:
            # Auto-Reject nach Timeout
            return f"Request {self.request_id} auto-rejected after timeout"

        if self.approved:
            return f"Request {self.request_id} approved by {self.approver_name}"
        else:
            return f"Request {self.request_id} rejected by {self.approver_name}: {self.comment}"


async def run_signal_example():
    """Signal-Beispiel: Workflow starten und Signal senden"""
    setup_logging()
    logging.info("=== Signal Example: Approval Workflow ===\n")

    # Client erstellen
    client = await create_temporal_client()

    # Workflow starten
    request_id = "REQ-001"
    workflow_id = f"approval-{request_id}"

    logging.info(f"1. Starting approval workflow for {request_id}...")
    handle = await client.start_workflow(
        ApprovalWorkflow.run,
        request_id,
        id=workflow_id,
        task_queue="book-examples",
    )
    logging.info(f"   Workflow started: {workflow_id}\n")

    # Kurz warten (simuliert Zeit bis Approver reagiert)
    await asyncio.sleep(2)

    # Approval Signal senden
    logging.info("2. Sending approval signal...")
    await handle.signal(
        ApprovalWorkflow.approve,
        ApprovalInput(
            approver_name="Alice Johnson",
            approved=True,
            comment="Budget approved, looks good!"
        )
    )
    logging.info("   Signal sent (fire-and-forget)\n")

    # Auf Workflow-Ergebnis warten
    logging.info("3. Waiting for workflow result...")
    result = await handle.result()
    logging.info(f"   ✓ Workflow completed\n")

    print(f"\n🎉 Result: {result}\n")


async def run_rejection_example():
    """Signal-Beispiel: Ablehnung"""
    setup_logging()
    logging.info("=== Signal Example: Rejection Workflow ===\n")

    client = await create_temporal_client()

    request_id = "REQ-002"
    workflow_id = f"approval-{request_id}"

    logging.info(f"Starting approval workflow for {request_id}...")
    handle = await client.start_workflow(
        ApprovalWorkflow.run,
        request_id,
        id=workflow_id,
        task_queue="book-examples",
    )

    await asyncio.sleep(1)

    # Rejection Signal senden
    logging.info("Sending rejection signal...")
    await handle.signal(
        ApprovalWorkflow.approve,
        ApprovalInput(
            approver_name="Bob Smith",
            approved=False,
            comment="Budget exceeded - request denied"
        )
    )

    result = await handle.result()
    print(f"\n🎉 Result: {result}\n")


if __name__ == "__main__":
    # Approval-Beispiel
    asyncio.run(run_signal_example())

    # Uncomment für Rejection-Beispiel:
    # asyncio.run(run_rejection_example())
