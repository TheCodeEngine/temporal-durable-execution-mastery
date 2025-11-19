"""
Temporal helper utilities for book examples.

Provides common functions for connecting to Temporal,
creating workers, and configuring clients.
"""

from temporalio.client import Client
from temporalio.worker import Worker
from typing import Optional, List, Type, Any
import asyncio


async def create_temporal_client(
    target_host: str = "localhost:7233",
    namespace: str = "default"
) -> Client:
    """
    Create and return a Temporal client connection.

    Args:
        target_host: Temporal server address (default: localhost:7233)
        namespace: Temporal namespace (default: "default")

    Returns:
        Connected Temporal client instance

    Example:
        ```python
        client = await create_temporal_client()
        # Use client to start workflows
        ```
    """
    return await Client.connect(target_host, namespace=namespace)


def get_default_namespace() -> str:
    """
    Return the default namespace for examples.

    Returns:
        Default namespace string ("default")
    """
    return "default"


async def create_worker(
    client: Client,
    task_queue: str,
    workflows: List[Type],
    activities: Optional[List[Any]] = None
) -> Worker:
    """
    Create and configure a Temporal worker.

    Args:
        client: Connected Temporal client
        task_queue: Name of the task queue to listen on
        workflows: List of workflow classes to register
        activities: Optional list of activity functions/classes to register

    Returns:
        Configured Worker instance

    Example:
        ```python
        client = await create_temporal_client()
        worker = await create_worker(
            client,
            "my-task-queue",
            [MyWorkflow],
            [my_activity]
        )
        await worker.run()
        ```
    """
    return Worker(
        client,
        task_queue=task_queue,
        workflows=workflows,
        activities=activities or []
    )
