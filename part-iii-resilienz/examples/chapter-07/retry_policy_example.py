"""
Retry Policy Example

Chapter: 7 - Error Handling und Retry Policies
Demonstrates: Verschiedene Retry-Strategien
"""

import asyncio
import sys
from pathlib import Path
from datetime import timedelta
import random

sys.path.append(str(Path(__file__).parent.parent.parent.parent / "shared"))

from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError, ActivityError
from shared.temporal_helpers import create_temporal_client
from shared.examples_common import setup_logging
import logging


# ==================== Activities ====================

@activity.defn
async def flaky_operation(fail_probability: float = 0.7) -> str:
    """Activity die mit bestimmter Wahrscheinlichkeit fehlschlägt"""
    attempt = activity.info().attempt

    activity.logger.info(f"Attempt {attempt}: fail_probability={fail_probability}")

    if random.random() < fail_probability:
        raise ApplicationError(
            f"Random failure on attempt {attempt}",
            type="TransientError"
        )

    return f"Success on attempt {attempt}"


@activity.defn
async def non_retryable_operation() -> str:
    """Activity mit non-retryable error"""
    raise ApplicationError(
        "This error should not be retried",
        type="ValidationError",
        non_retryable=True
    )


# ==================== Workflows ====================

@workflow.defn
class RetryPolicyDemoWorkflow:
    """Demonstriert verschiedene Retry Policies"""

    @workflow.run
    async def run(self) -> dict:
        results = {}

        # 1. Default Retry (unbegrenzt)
        workflow.logger.info("=== Test 1: Default Retry ===")
        try:
            result = await workflow.execute_activity(
                flaky_operation,
                args=[0.3],  # 30% failure rate
                start_to_close_timeout=timedelta(seconds=5)
                # Kein retry_policy = Default (unbegrenzt)
            )
            results["default_retry"] = f"Success: {result}"
        except ActivityError as e:
            results["default_retry"] = f"Failed: {e}"

        # 2. Limited Retries
        workflow.logger.info("\n=== Test 2: Limited Retries (max 3) ===")
        try:
            result = await workflow.execute_activity(
                flaky_operation,
                args=[0.9],  # 90% failure rate
                start_to_close_timeout=timedelta(seconds=5),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            results["limited_retry"] = f"Success: {result}"
        except ActivityError as e:
            results["limited_retry"] = f"Failed after 3 attempts"

        # 3. Custom Backoff
        workflow.logger.info("\n=== Test 3: Custom Backoff ===")
        try:
            result = await workflow.execute_activity(
                flaky_operation,
                args=[0.5],
                start_to_close_timeout=timedelta(seconds=5),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(milliseconds=100),
                    backoff_coefficient=1.5,
                    maximum_interval=timedelta(seconds=2),
                    maximum_attempts=5
                )
            )
            results["custom_backoff"] = f"Success: {result}"
        except ActivityError as e:
            results["custom_backoff"] = f"Failed: {e}"

        # 4. Non-Retryable Error
        workflow.logger.info("\n=== Test 4: Non-Retryable Error ===")
        try:
            result = await workflow.execute_activity(
                non_retryable_operation,
                start_to_close_timeout=timedelta(seconds=5),
                retry_policy=RetryPolicy(maximum_attempts=5)
            )
            results["non_retryable"] = f"Success: {result}"
        except ActivityError as e:
            results["non_retryable"] = f"Failed immediately (non-retryable)"
            workflow.logger.info(f"Error was not retried: {e.cause}")

        return results


async def run_retry_example():
    """Retry Policy Example ausführen"""
    setup_logging()
    logging.info("=== Retry Policy Example ===\n")

    client = await create_temporal_client()

    # Workflow ausführen
    result = await client.execute_workflow(
        RetryPolicyDemoWorkflow.run,
        id="retry-policy-demo",
        task_queue="book-examples"
    )

    print("\n" + "="*50)
    print("Results:")
    print("="*50)
    for test_name, test_result in result.items():
        print(f"{test_name}: {test_result}")
    print("="*50 + "\n")


if __name__ == "__main__":
    asyncio.run(run_retry_example())
