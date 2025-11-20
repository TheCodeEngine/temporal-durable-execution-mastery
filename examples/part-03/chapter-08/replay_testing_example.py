"""
Replay Testing Example

Chapter: 8 - Workflow Evolution und Versioning
Demonstrates: Replay Testing für Workflow-Kompatibilität
"""

import asyncio
import sys
from pathlib import Path
from datetime import timedelta
from dataclasses import dataclass
import json

# Add project root to path for shared utilities
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.testing import WorkflowEnvironment
from shared.temporal_helpers import create_temporal_client
from shared.examples_common import setup_logging
import logging


# ==================== Data Models ====================

@dataclass
class UserData:
    user_id: str
    name: str
    email: str


# ==================== Activities ====================

@activity.defn
async def validate_user(user: UserData) -> bool:
    """Validate user data"""
    activity.logger.info(f"Validating user: {user.user_id}")
    await asyncio.sleep(0.2)
    return bool(user.email and "@" in user.email)

@activity.defn
async def create_account(user: UserData) -> str:
    """Create user account"""
    activity.logger.info(f"Creating account for: {user.user_id}")
    await asyncio.sleep(0.3)
    return f"account_{user.user_id}"

@activity.defn
async def send_welcome_email(email: str) -> None:
    """Send welcome email"""
    activity.logger.info(f"Sending welcome email to: {email}")
    await asyncio.sleep(0.2)


# ==================== Workflow V1 (OLD) ====================

@workflow.defn
class UserSignupWorkflowV1:
    """
    Version 1: Simple user signup
    - validate_user
    - create_account
    """

    @workflow.run
    async def run(self, user: UserData) -> dict:
        workflow.logger.info(f"Signup workflow v1 for {user.user_id}")

        # Step 1: Validate
        is_valid = await workflow.execute_activity(
            validate_user,
            user,
            start_to_close_timeout=timedelta(seconds=10)
        )

        if not is_valid:
            return {"success": False, "error": "Invalid user data"}

        # Step 2: Create account
        account_id = await workflow.execute_activity(
            create_account,
            user,
            start_to_close_timeout=timedelta(seconds=10)
        )

        return {
            "success": True,
            "account_id": account_id,
            "version": "v1"
        }


# ==================== Workflow V2 (NEW - with patch) ====================

@workflow.defn
class UserSignupWorkflowV2:
    """
    Version 2: Enhanced signup with welcome email
    - validate_user
    - create_account
    - send_welcome_email (NEW)
    """

    @workflow.run
    async def run(self, user: UserData) -> dict:
        workflow.logger.info(f"Signup workflow v2 for {user.user_id}")

        # Step 1: Validate
        is_valid = await workflow.execute_activity(
            validate_user,
            user,
            start_to_close_timeout=timedelta(seconds=10)
        )

        if not is_valid:
            return {"success": False, "error": "Invalid user data"}

        # Step 2: Create account
        account_id = await workflow.execute_activity(
            create_account,
            user,
            start_to_close_timeout=timedelta(seconds=10)
        )

        # Step 3: Send welcome email (NEW in v2)
        if workflow.patched("send-welcome-email"):
            workflow.logger.info("Sending welcome email (v2)")
            await workflow.execute_activity(
                send_welcome_email,
                user.email,
                start_to_close_timeout=timedelta(seconds=10)
            )
            welcome_sent = True
        else:
            workflow.logger.info("Skipping welcome email (v1 replay)")
            welcome_sent = False

        return {
            "success": True,
            "account_id": account_id,
            "welcome_sent": welcome_sent,
            "version": "v2"
        }


# ==================== Replay Testing ====================

async def test_workflow_replay():
    """
    Test that v2 workflow can replay v1 workflow history

    This simulates:
    1. Recording a workflow execution with v1 code
    2. Replaying it with v2 code to ensure compatibility
    """
    setup_logging()
    logging.info("=== Replay Testing Example ===\n")

    # Use WorkflowEnvironment for replay testing
    async with await WorkflowEnvironment.start_time_skipping() as env:

        # ========== Step 1: Record v1 Workflow History ==========
        logging.info("--- Step 1: Execute v1 workflow (recording history) ---")

        test_user = UserData(
            user_id="user-test-001",
            name="Test User",
            email="test@example.com"
        )

        # Start worker with v1 workflow
        async with Worker(
            env.client,
            task_queue="replay-test-queue",
            workflows=[UserSignupWorkflowV1],
            activities=[validate_user, create_account, send_welcome_email]
        ):
            # Execute v1 workflow
            handle = await env.client.start_workflow(
                UserSignupWorkflowV1.run,
                test_user,
                id="replay-test-v1",
                task_queue="replay-test-queue"
            )

            result_v1 = await handle.result()
            logging.info(f"v1 result: {result_v1}")

            # Get workflow history for replay
            history = await handle.fetch_history()
            logging.info(f"✓ Captured workflow history ({len(history.events)} events)")

        # ========== Step 2: Replay with v2 Workflow ==========
        logging.info("\n--- Step 2: Replay history with v2 workflow ---")

        try:
            # Create replayer with v2 workflow
            from temporalio.worker import Replayer

            replayer = Replayer(
                workflows=[UserSignupWorkflowV2],
                activities=[validate_user, create_account, send_welcome_email]
            )

            # Replay v1 history with v2 code
            await replayer.replay_workflow(history)

            logging.info("✓ Replay successful! v2 is compatible with v1 history")
            print("\n" + "="*60)
            print("✅ REPLAY TEST PASSED")
            print("="*60)
            print("The v2 workflow correctly replayed v1 history.")
            print("This proves that the patching is deterministic.")
            print("="*60 + "\n")

            replay_success = True

        except Exception as e:
            logging.error(f"❌ Replay failed: {e}")
            print("\n" + "="*60)
            print("❌ REPLAY TEST FAILED")
            print("="*60)
            print(f"Error: {e}")
            print("This indicates a non-deterministic change!")
            print("="*60 + "\n")

            replay_success = False

        # ========== Step 3: Execute v2 Workflow (fresh execution) ==========
        logging.info("\n--- Step 3: Execute v2 workflow (fresh execution) ---")

        async with Worker(
            env.client,
            task_queue="replay-test-queue",
            workflows=[UserSignupWorkflowV2],
            activities=[validate_user, create_account, send_welcome_email]
        ):
            # Execute v2 workflow fresh
            handle_v2 = await env.client.start_workflow(
                UserSignupWorkflowV2.run,
                UserData(
                    user_id="user-test-002",
                    name="Test User 2",
                    email="test2@example.com"
                ),
                id="replay-test-v2-fresh",
                task_queue="replay-test-queue"
            )

            result_v2 = await handle_v2.result()
            logging.info(f"v2 fresh result: {result_v2}")

            print("\nComparison:")
            print(f"  v1 result: {result_v1}")
            print(f"  v2 replayed: Compatible ✓" if replay_success else "  v2 replayed: Failed ✗")
            print(f"  v2 fresh: {result_v2}")
            print()

    return replay_success


# ==================== Advanced: Breaking Change Detection ====================

@workflow.defn
class UserSignupWorkflowV2Bad:
    """
    BAD Version 2: Breaks determinism by reordering activities
    This WILL FAIL replay testing!
    """

    @workflow.run
    async def run(self, user: UserData) -> dict:
        workflow.logger.info(f"Signup workflow v2-bad for {user.user_id}")

        # WRONG: Create account BEFORE validation (order changed!)
        account_id = await workflow.execute_activity(
            create_account,
            user,
            start_to_close_timeout=timedelta(seconds=10)
        )

        # Validate after (WRONG ORDER)
        is_valid = await workflow.execute_activity(
            validate_user,
            user,
            start_to_close_timeout=timedelta(seconds=10)
        )

        if not is_valid:
            return {"success": False, "error": "Invalid user data"}

        return {
            "success": True,
            "account_id": account_id,
            "version": "v2-bad"
        }


async def test_breaking_change():
    """Test that demonstrates how replay catches breaking changes"""
    setup_logging()
    logging.info("\n=== Breaking Change Detection Example ===\n")

    async with await WorkflowEnvironment.start_time_skipping() as env:

        # Record v1 history
        logging.info("--- Recording v1 history ---")

        test_user = UserData(
            user_id="user-break-test",
            name="Break Test",
            email="break@example.com"
        )

        async with Worker(
            env.client,
            task_queue="break-test-queue",
            workflows=[UserSignupWorkflowV1],
            activities=[validate_user, create_account]
        ):
            handle = await env.client.start_workflow(
                UserSignupWorkflowV1.run,
                test_user,
                id="break-test-v1",
                task_queue="break-test-queue"
            )

            await handle.result()
            history = await handle.fetch_history()
            logging.info(f"✓ Captured history")

        # Try to replay with BAD v2 (should fail)
        logging.info("\n--- Attempting replay with breaking change ---")

        try:
            from temporalio.worker import Replayer

            replayer = Replayer(
                workflows=[UserSignupWorkflowV2Bad],
                activities=[validate_user, create_account]
            )

            await replayer.replay_workflow(history)

            logging.error("❌ Replay should have failed but didn't!")

        except Exception as e:
            logging.info(f"✓ Replay correctly failed: {type(e).__name__}")
            print("\n" + "="*60)
            print("✅ BREAKING CHANGE DETECTED")
            print("="*60)
            print(f"Error: {type(e).__name__}")
            print("The activity order change broke determinism.")
            print("Replay testing caught this before production!")
            print("="*60 + "\n")


# ==================== Main ====================

async def run_replay_example():
    """Run all replay testing examples"""

    # Test 1: Compatible change (with patching)
    print("\n" + "="*70)
    print("TEST 1: Compatible Change (with workflow.patched)")
    print("="*70)
    await test_workflow_replay()

    # Test 2: Breaking change detection
    print("\n" + "="*70)
    print("TEST 2: Breaking Change Detection")
    print("="*70)
    await test_breaking_change()

    print("\n" + "="*70)
    print("Summary:")
    print("  ✓ Replay testing verifies workflow compatibility")
    print("  ✓ workflow.patched() enables safe evolution")
    print("  ✓ Breaking changes are caught before production")
    print("  ✓ Always test replay after workflow changes")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(run_replay_example())
