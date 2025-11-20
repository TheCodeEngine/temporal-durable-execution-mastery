"""
Worker Setup and Execution

Chapter: 2 - Kernbausteine
Demonstrates: Worker configuration and startup
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path for shared utilities
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from temporalio.worker import Worker
from shared.temporal_helpers import create_temporal_client
import logging

# Import workflow and activities
from workflow import DataProcessingWorkflow
from activities import process_data, send_notification


async def main():
    """
    Create and run a Temporal worker.

    This demonstrates:
    - Worker initialization
    - Registering workflows and activities
    - Running the worker
    """
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting Temporal Worker...")

    # Connect to Temporal
    client = await create_temporal_client()

    # Create worker
    worker = Worker(
        client,
        task_queue="book-examples",
        workflows=[DataProcessingWorkflow],
        activities=[process_data, send_notification],
    )

    logging.info("Worker registered workflows and activities:")
    logging.info(f"  - Workflows: {[DataProcessingWorkflow.__name__]}")
    logging.info(f"  - Activities: {[process_data.__name__, send_notification.__name__]}")
    logging.info("\nWorker is running and polling for tasks...")
    logging.info("Press Ctrl+C to stop\n")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
