"""
Workflow Definition Example

Chapter: 2 - Kernbausteine
Demonstrates: Workflow definition with activity calls
"""

import asyncio
import sys
from pathlib import Path
from datetime import timedelta

# Add project root to path for shared utilities
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from temporalio import workflow
from temporalio.common import RetryPolicy
from shared.temporal_helpers import create_temporal_client
import logging

# Import activities
with workflow.unsafe.imports_passed_through():
    from activities import process_data, send_notification


@workflow.defn
class DataProcessingWorkflow:
    """
    Workflow that processes data and sends notifications.

    This demonstrates:
    - Calling activities from workflows
    - Activity retry policies
    - Activity timeouts
    """

    @workflow.run
    async def run(self, data: str) -> dict:
        """
        Process data and send notification.

        Args:
            data: Data to process

        Returns:
            Dictionary with processing results
        """
        # Call activity to process data
        processed = await workflow.execute_activity(
            process_data,
            data,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
            ),
        )

        # Send notification
        await workflow.execute_activity(
            send_notification,
            f"Processed: {processed}",
            start_to_close_timeout=timedelta(seconds=10),
        )

        return {
            "input": data,
            "output": processed,
            "status": "completed"
        }


async def main():
    """Start the workflow."""
    logging.basicConfig(level=logging.INFO)
    client = await create_temporal_client()

    result = await client.execute_workflow(
        DataProcessingWorkflow.run,
        "Sample Data",
        id="data-processing-001",
        task_queue="book-examples",
    )

    print(f"\n✅ Workflow Result: {result}\n")


if __name__ == "__main__":
    asyncio.run(main())
