"""
Versioning Patching Example

Chapter: 8 - Workflow Evolution und Versioning
Demonstrates: Patching API (workflow.patched) für sichere Workflow-Evolution
"""

import asyncio
import sys
from pathlib import Path
from datetime import timedelta
from dataclasses import dataclass
from typing import Optional

sys.path.append(str(Path(__file__).parent.parent.parent.parent / "shared"))

from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.common import RetryPolicy
from shared.temporal_helpers import create_temporal_client
from shared.examples_common import setup_logging
import logging


# ==================== Data Models ====================

@dataclass
class Order:
    order_id: str
    amount: float
    customer_id: str

@dataclass
class PaymentResult:
    success: bool
    transaction_id: str

@dataclass
class FraudCheckResult:
    is_safe: bool
    risk_score: float
    reason: Optional[str] = None


# ==================== Activities ====================

@activity.defn
async def process_payment(order: Order) -> PaymentResult:
    """Process payment for order"""
    activity.logger.info(f"Processing payment for order {order.order_id}: ${order.amount}")
    await asyncio.sleep(0.5)

    return PaymentResult(
        success=True,
        transaction_id=f"txn_{order.order_id}"
    )

@activity.defn
async def check_fraud(order: Order) -> FraudCheckResult:
    """Check for fraud (NEW ACTIVITY added in v2)"""
    activity.logger.info(f"Checking fraud for order {order.order_id}")
    await asyncio.sleep(0.3)

    # Simple fraud check logic
    risk_score = 0.1 if order.amount < 1000 else 0.8
    is_safe = risk_score < 0.5

    return FraudCheckResult(
        is_safe=is_safe,
        risk_score=risk_score,
        reason=None if is_safe else "High amount transaction"
    )

@activity.defn
async def send_confirmation(order_id: str, transaction_id: str) -> None:
    """Send order confirmation"""
    activity.logger.info(f"Sending confirmation for order {order_id}")
    await asyncio.sleep(0.2)

@activity.defn
async def send_notification(order_id: str, message: str) -> None:
    """Send notification (NEW ACTIVITY added in v3)"""
    activity.logger.info(f"Sending notification for order {order_id}: {message}")
    await asyncio.sleep(0.2)


# ==================== Versioned Workflow ====================

@workflow.defn
class OrderWorkflowVersioned:
    """
    Demonstriert Workflow Versioning mit Patching API

    Version History:
    - v1: Basis-Workflow (process_payment + send_confirmation)
    - v2: Added fraud check (patch: "add-fraud-check-v1")
    - v3: Added customer notification (patch: "add-notification-v1")
    """

    @workflow.run
    async def run(self, order: Order) -> dict:
        result = {
            "order_id": order.order_id,
            "version": "v1",  # Base version
            "fraud_checked": False,
            "notification_sent": False
        }

        workflow.logger.info(f"Starting order workflow for {order.order_id}")

        # ========== Version 1: Basic Payment Processing ==========
        workflow.logger.info("→ Step 1: Processing payment (v1)")
        payment = await workflow.execute_activity(
            process_payment,
            order,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        result["transaction_id"] = payment.transaction_id
        workflow.logger.info(f"✓ Payment processed: {payment.transaction_id}")

        # ========== Version 2: Add Fraud Check (Patched) ==========
        if workflow.patched("add-fraud-check-v1"):
            # NEW CODE PATH - executed after v2 deployment
            workflow.logger.info("→ Step 2: Fraud check (v2+)")
            result["version"] = "v2"

            fraud_result = await workflow.execute_activity(
                check_fraud,
                order,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )

            result["fraud_checked"] = True
            result["risk_score"] = fraud_result.risk_score

            if not fraud_result.is_safe:
                workflow.logger.warning(f"⚠ Fraud detected: {fraud_result.reason}")
                result["status"] = "FRAUD_REJECTED"
                return result

            workflow.logger.info(f"✓ Fraud check passed (risk: {fraud_result.risk_score})")
        else:
            # OLD CODE PATH - for replaying old workflow executions from v1
            workflow.logger.info("⏭ Skipping fraud check (v1 execution)")

        # ========== Version 3: Add Customer Notification (Patched) ==========
        if workflow.patched("add-notification-v1"):
            # NEW CODE PATH - executed after v3 deployment
            workflow.logger.info("→ Step 3: Customer notification (v3+)")
            result["version"] = "v3"

            await workflow.execute_activity(
                send_notification,
                args=[order.order_id, f"Your order ${order.amount} has been confirmed!"],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )

            result["notification_sent"] = True
            workflow.logger.info("✓ Notification sent")
        else:
            # OLD CODE PATH - for replaying old workflow executions from v1/v2
            workflow.logger.info("⏭ Skipping notification (v1/v2 execution)")

        # ========== Final Step: Send Confirmation ==========
        workflow.logger.info("→ Final step: Sending confirmation")
        await workflow.execute_activity(
            send_confirmation,
            args=[order.order_id, payment.transaction_id],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )

        result["status"] = "COMPLETED"
        workflow.logger.info(f"🎉 Order completed: {order.order_id}")

        return result


# ==================== Client Demo ====================

async def run_patching_example():
    """Patching API Example"""
    setup_logging()
    logging.info("=== Versioning Patching Example ===\n")

    client = await create_temporal_client()

    # Test 1: Small order (passes fraud check)
    logging.info("--- Test 1: Small Order (v3 behavior) ---")
    result1 = await client.execute_workflow(
        OrderWorkflowVersioned.run,
        Order(
            order_id="order-001",
            amount=500.0,
            customer_id="customer-123"
        ),
        id="order-small-v3",
        task_queue="book-examples"
    )

    print(f"\nTest 1 Result:")
    print(f"  Order ID: {result1['order_id']}")
    print(f"  Version: {result1['version']}")
    print(f"  Transaction: {result1['transaction_id']}")
    print(f"  Fraud Checked: {result1['fraud_checked']}")
    print(f"  Risk Score: {result1.get('risk_score', 'N/A')}")
    print(f"  Notification Sent: {result1['notification_sent']}")
    print(f"  Status: {result1['status']}\n")

    # Test 2: Large order (triggers fraud rejection)
    logging.info("\n--- Test 2: Large Order (fraud rejection) ---")
    result2 = await client.execute_workflow(
        OrderWorkflowVersioned.run,
        Order(
            order_id="order-002",
            amount=5000.0,
            customer_id="customer-456"
        ),
        id="order-large-fraud",
        task_queue="book-examples"
    )

    print(f"\nTest 2 Result:")
    print(f"  Order ID: {result2['order_id']}")
    print(f"  Version: {result2['version']}")
    print(f"  Fraud Checked: {result2['fraud_checked']}")
    print(f"  Risk Score: {result2.get('risk_score', 'N/A')}")
    print(f"  Status: {result2['status']}\n")

    print("="*60)
    print("Patching API demonstrated:")
    print("  ✓ workflow.patched() for safe evolution")
    print("  ✓ New code path for new executions")
    print("  ✓ Old code path for replay compatibility")
    print("  ✓ Multiple patches (v2 + v3)")
    print("="*60)
    print("\nNext steps:")
    print("  1. Deploy v2: Add 'add-fraud-check-v1' patch")
    print("  2. Wait for old workflows to complete")
    print("  3. Deploy v3: Add 'add-notification-v1' patch")
    print("  4. Later: Use workflow.deprecate_patch() to clean up")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(run_patching_example())
