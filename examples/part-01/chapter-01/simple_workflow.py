"""
Simple Temporal Workflow Example

Chapter: 1 - Einführung in Temporal
Complexity: Basic
Requires: Temporal server running

This example demonstrates the most basic Temporal workflow:
- Defining a workflow
- Starting a workflow execution
- Getting workflow results
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path for shared utilities
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from temporalio import workflow
from temporalio.client import Client
from shared.temporal_helpers import create_temporal_client
from shared.examples_common import setup_logging
import logging


@workflow.defn
class GreetingWorkflow:
    """
    A simple workflow that greets a person.

    This workflow demonstrates:
    - Workflow definition using @workflow.defn
    - Workflow run method
    - Deterministic execution
    """

    @workflow.run
    async def run(self, name: str) -> str:
        """
        Execute the workflow logic.

        Args:
            name: Name of the person to greet

        Returns:
            Greeting message
        """
        return f"Hello, {name}! Welcome to Temporal."


async def main():
    """Main function to start and execute the workflow."""
    setup_logging()
    logging.info("Starting Simple Workflow Example...")

    # Connect to Temporal server
    logging.info("Connecting to Temporal server at localhost:7233")
    client = await create_temporal_client()

    # Start the workflow
    workflow_id = "greeting-workflow-001"
    logging.info(f"Starting workflow with ID: {workflow_id}")

    handle = await client.start_workflow(
        GreetingWorkflow.run,
        "Temporal User",
        id=workflow_id,
        task_queue="book-examples",
    )

    # Wait for workflow to complete and get result
    logging.info("Waiting for workflow to complete...")
    result = await handle.result()

    logging.info(f"Workflow completed successfully!")
    logging.info(f"Result: {result}")
    print(f"\n✅ {result}\n")


if __name__ == "__main__":
    asyncio.run(main())
