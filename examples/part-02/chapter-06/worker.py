"""
Worker for Chapter 6 Examples

Runs a single worker that can execute all Chapter 6 workflow types.
Listens on task queue: book-examples
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path for shared utilities
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from temporalio.worker import Worker
from shared.temporal_helpers import create_temporal_client
from shared.examples_common import setup_logging
import logging

# Import all workflow classes from examples
from signal_example import ApprovalWorkflow
from query_example import DataProcessingWorkflow as QueryWorkflow
from update_example import ShoppingCartWorkflow
from combined_example import OrderWorkflow


async def main():
    """Run worker for all Chapter 6 workflows"""
    setup_logging()
    logging.info("Starting Chapter 6 Worker...")

    # Connect to Temporal
    client = await create_temporal_client()

    # Create worker with all workflow types
    worker = Worker(
        client,
        task_queue="book-examples",
        workflows=[
            ApprovalWorkflow,
            QueryWorkflow,
            ShoppingCartWorkflow,
            OrderWorkflow,
        ],
    )

    logging.info("Worker registered workflows:")
    logging.info("  - ApprovalWorkflow (signal_example.py)")
    logging.info("  - DataProcessingWorkflow (query_example.py)")
    logging.info("  - ShoppingCartWorkflow (update_example.py)")
    logging.info("  - OrderWorkflow (combined_example.py)")
    logging.info("")
    logging.info("Worker is running and polling for tasks...")
    logging.info("Press Ctrl+C to stop")
    logging.info("")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
