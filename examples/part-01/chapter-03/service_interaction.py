"""
Temporal Service Interaction Example

Chapter: 3 - Architektur des Temporal Service
Demonstrates: Interaction with Temporal service components
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path for shared utilities
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from temporalio import workflow
from temporalio.client import Client, WorkflowHistory
from shared.temporal_helpers import create_temporal_client
from shared.examples_common import setup_logging
import logging


@workflow.defn
class ServiceArchitectureWorkflow:
    """
    Workflow demonstrating service architecture concepts.

    This workflow shows:
    - Event history creation
    - Workflow execution tracking
    - Interaction with Temporal service components
    """

    @workflow.run
    async def run(self) -> dict:
        """Execute workflow to demonstrate service architecture."""
        workflow.logger.info("Workflow started - event logged in history")

        # Simulate some workflow logic
        steps = ["Frontend processing", "History service update", "Task scheduling"]

        for i, step in enumerate(steps, 1):
            workflow.logger.info(f"Step {i}: {step}")

        workflow.logger.info("Workflow completed - final event in history")

        return {
            "message": "Architecture demonstration complete",
            "steps_completed": len(steps)
        }


async def demonstrate_service_architecture():
    """
    Demonstrate Temporal service architecture concepts.

    Shows:
    - Client → Frontend interaction
    - History service event logging
    - Workflow execution lifecycle
    """
    setup_logging()
    logging.info("=== Temporal Service Architecture Demonstration ===\n")

    # Connect to Temporal (Client → Frontend)
    logging.info("1. Client connecting to Temporal Frontend...")
    client = await create_temporal_client()
    logging.info("   ✓ Connected to Temporal service\n")

    # Start workflow (Frontend → History Service)
    workflow_id = "architecture-demo-001"
    logging.info(f"2. Starting workflow (ID: {workflow_id})")
    logging.info("   Frontend schedules task...")
    logging.info("   History service creates event log...")

    handle = await client.start_workflow(
        ServiceArchitectureWorkflow.run,
        id=workflow_id,
        task_queue="book-examples",
    )
    logging.info("   ✓ Workflow started\n")

    # Wait for completion
    logging.info("3. Waiting for workflow completion...")
    logging.info("   Worker polls task queue...")
    logging.info("   Worker executes workflow code...")
    logging.info("   History service logs each event...")

    result = await handle.result()
    logging.info("   ✓ Workflow completed\n")

    # Demonstrate history access
    logging.info("4. Accessing workflow history...")
    history = await handle.fetch_history()

    event_count = len(list(history.events))
    logging.info(f"   ✓ Retrieved {event_count} events from history service\n")

    logging.info("=== Architecture Components Demonstrated ===")
    logging.info("✓ Client - Initiated workflow")
    logging.info("✓ Frontend - Accepted workflow request")
    logging.info("✓ History Service - Stored event log")
    logging.info("✓ Task Queue - Delivered tasks to worker")
    logging.info("✓ Worker - Executed workflow code")

    print(f"\n🎉 Result: {result}\n")


if __name__ == "__main__":
    asyncio.run(demonstrate_service_architecture())
