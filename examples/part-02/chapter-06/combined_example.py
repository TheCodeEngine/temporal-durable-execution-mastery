"""
Combined Example - E-Commerce Order mit Signals, Queries und Updates

Chapter: 6 - Kommunikation (Signale und Queries)
Demonstrates: Alle drei Kommunikationsmechanismen zusammen
"""

import asyncio
import sys
from pathlib import Path
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from datetime import timedelta
from enum import Enum

# Add project root to path for shared utilities
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.exceptions import WorkflowUpdateFailedError
from shared.temporal_helpers import create_temporal_client
from shared.examples_common import setup_logging
import logging


# ==================== Data Models ====================

class OrderStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass
class OrderItem:
    sku: str
    name: str
    quantity: int
    price: Decimal


@dataclass
class PaymentInfo:
    payment_method: str
    amount: Decimal


@dataclass
class ShippingInfo:
    carrier: str
    tracking_number: str


@dataclass
class OrderProgress:
    """Query Response"""
    status: str
    items_count: int
    total_amount: str
    payment_status: str
    shipping_status: str


# ==================== Activities ====================

@activity.defn
async def check_inventory(item: OrderItem) -> bool:
    """Prüfe Inventory"""
    activity.logger.info(f"Checking inventory for {item.sku}")
    return True


@activity.defn
async def charge_payment(payment: PaymentInfo) -> str:
    """Verarbeite Payment"""
    activity.logger.info(f"Charging ${payment.amount} via {payment.payment_method}")
    await asyncio.sleep(0.5)
    return f"txn_{payment.payment_method[:4]}_123"


@activity.defn
async def send_confirmation(order_id: str, customer_id: str) -> None:
    """Sende Delivery Confirmation"""
    activity.logger.info(f"Sending confirmation to {customer_id} for {order_id}")


# ==================== Workflow ====================

@workflow.defn
class OrderWorkflow:
    """E-Commerce Order mit Signals, Queries und Updates"""

    @workflow.init
    def __init__(self) -> None:
        self.lock = asyncio.Lock()
        self.order_id: str = ""
        self.customer_id: str = ""
        self.status = OrderStatus.PENDING
        self.items: List[OrderItem] = []
        self.total = Decimal("0.00")
        self.payment_transaction_id: Optional[str] = None
        self.shipping_info: Optional[ShippingInfo] = None

    # ========== Queries: Read-Only State Access ==========

    @workflow.query
    def get_status(self) -> str:
        """Aktueller Order Status"""
        return self.status.value

    @workflow.query
    def get_total(self) -> str:
        """Total-Betrag"""
        return str(self.total)

    @workflow.query
    def get_progress(self) -> OrderProgress:
        """Detaillierter Progress"""
        return OrderProgress(
            status=self.status.value,
            items_count=len(self.items),
            total_amount=str(self.total),
            payment_status="paid" if self.payment_transaction_id else "pending",
            shipping_status=(
                f"shipped via {self.shipping_info.carrier}"
                if self.shipping_info else "not shipped"
            )
        )

    # ========== Updates: Validated State Changes ==========

    @workflow.update
    async def add_item(self, item: OrderItem) -> dict:
        """Item hinzufügen (mit Validierung)"""
        async with self.lock:
            # Inventory prüfen
            available = await workflow.execute_activity(
                check_inventory,
                item,
                start_to_close_timeout=timedelta(seconds=10),
            )

            if not available:
                raise ValueError(f"Item {item.sku} out of stock")

            # Item hinzufügen
            self.items.append(item)
            self.total += item.price * item.quantity

            workflow.logger.info(
                f"Added {item.quantity}x {item.name} - Total: ${self.total}"
            )

            return {"items": len(self.items), "total": str(self.total)}

    @add_item.validator
    def validate_add_item(self, item: OrderItem) -> None:
        """Validator: Items nur wenn pending"""
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"Cannot add items in status: {self.status.value}")
        if item.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if len(self.items) >= 20:
            raise ValueError("Maximum 20 items per order")

    @workflow.update
    async def process_payment(self, payment: PaymentInfo) -> str:
        """Payment verarbeiten"""
        async with self.lock:
            # Validate amount
            if payment.amount != self.total:
                raise ValueError(
                    f"Payment amount {payment.amount} != order total {self.total}"
                )

            # Charge payment
            transaction_id = await workflow.execute_activity(
                charge_payment,
                payment,
                start_to_close_timeout=timedelta(seconds=30),
            )

            self.payment_transaction_id = transaction_id
            self.status = OrderStatus.PAID

            workflow.logger.info(f"Payment successful: {transaction_id}")
            return transaction_id

    @process_payment.validator
    def validate_payment(self, payment: PaymentInfo) -> None:
        """Validator: Payment nur wenn pending"""
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"Cannot process payment in status: {self.status.value}")
        if len(self.items) == 0:
            raise ValueError("Cannot pay for empty order")

    # ========== Signals: Async Notifications ==========

    @workflow.signal
    def mark_shipped(self, shipping: ShippingInfo) -> None:
        """Order als shipped markieren"""
        if self.status != OrderStatus.PAID:
            workflow.logger.warn(f"Cannot ship order in status: {self.status.value}")
            return

        self.shipping_info = shipping
        self.status = OrderStatus.SHIPPED

        workflow.logger.info(
            f"Order shipped via {shipping.carrier} - Tracking: {shipping.tracking_number}"
        )

    @workflow.signal
    def cancel_order(self, reason: str) -> None:
        """Order canceln"""
        if self.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            workflow.logger.warn(f"Cannot cancel order in status: {self.status.value}")
            return

        self.status = OrderStatus.CANCELLED
        workflow.logger.info(f"Order cancelled: {reason}")

    # ========== Main Workflow ==========

    @workflow.run
    async def run(self, order_id: str, customer_id: str) -> str:
        """Order Workflow Main Logic"""
        self.order_id = order_id
        self.customer_id = customer_id

        workflow.logger.info(f"Order {order_id} created for customer {customer_id}")

        # Warte auf Payment (max 7 Tage)
        try:
            await workflow.wait_condition(
                lambda: self.status == OrderStatus.PAID,
                timeout=timedelta(days=7)
            )
        except asyncio.TimeoutError:
            self.status = OrderStatus.CANCELLED
            return f"Order {order_id} cancelled - payment timeout"

        # Warte auf Shipment (max 30 Tage)
        try:
            await workflow.wait_condition(
                lambda: self.status == OrderStatus.SHIPPED,
                timeout=timedelta(days=30)
            )
        except asyncio.TimeoutError:
            workflow.logger.error("Shipment timeout!")
            return f"Order {order_id} paid but not shipped"

        # Simuliere Delivery
        await asyncio.sleep(timedelta(seconds=2))

        # Mark als delivered
        self.status = OrderStatus.DELIVERED

        # Confirmation senden
        await workflow.execute_activity(
            send_confirmation,
            self.order_id,
            self.customer_id,
            start_to_close_timeout=timedelta(seconds=30),
        )

        workflow.logger.info(f"Order {order_id} delivered successfully")
        return f"Order {order_id} completed - ${self.total} charged"


# ==================== Client Demo ====================

async def run_combined_example():
    """Vollständiges Order-Beispiel mit Signals, Queries und Updates"""
    setup_logging()
    logging.info("=== Combined Example: E-Commerce Order ===\n")

    client = await create_temporal_client()

    # Order starten
    order_id = "ORDER-001"
    customer_id = "customer-456"
    workflow_id = order_id

    logging.info(f"1. Creating order {order_id} for {customer_id}...")
    handle = await client.start_workflow(
        OrderWorkflow.run,
        order_id,
        customer_id,
        id=workflow_id,
        task_queue="book-examples",
    )
    logging.info(f"   Order created\n")

    # Items hinzufügen (UPDATE)
    logging.info("2. Adding items to order (Updates)...\n")

    try:
        result = await handle.execute_update(
            OrderWorkflow.add_item,
            OrderItem(sku="LAPTOP-001", name="Gaming Laptop", quantity=1, price=Decimal("1299.99"))
        )
        logging.info(f"   ✓ Laptop added - Items: {result['items']}, Total: ${result['total']}")

        result = await handle.execute_update(
            OrderWorkflow.add_item,
            OrderItem(sku="MOUSE-001", name="Wireless Mouse", quantity=2, price=Decimal("29.99"))
        )
        logging.info(f"   ✓ Mouse added - Items: {result['items']}, Total: ${result['total']}\n")

    except WorkflowUpdateFailedError as e:
        logging.error(f"   ✗ Failed to add item: {e}\n")
        return

    # Progress abfragen (QUERY)
    logging.info("3. Querying order progress (Query)...")
    progress = await handle.query(OrderWorkflow.get_progress)
    logging.info(f"   Status: {progress.status}")
    logging.info(f"   Items: {progress.items_count}")
    logging.info(f"   Total: ${progress.total_amount}")
    logging.info(f"   Payment: {progress.payment_status}\n")

    # Payment verarbeiten (UPDATE)
    logging.info("4. Processing payment (Update with validation)...")
    total = await handle.query(OrderWorkflow.get_total)

    try:
        txn_id = await handle.execute_update(
            OrderWorkflow.process_payment,
            PaymentInfo(payment_method="credit_card", amount=Decimal(total))
        )
        logging.info(f"   ✓ Payment processed: {txn_id}\n")
    except WorkflowUpdateFailedError as e:
        logging.error(f"   ✗ Payment failed: {e}\n")
        return

    # Status prüfen (QUERY)
    status = await handle.query(OrderWorkflow.get_status)
    logging.info(f"5. Order status after payment: {status}\n")

    # Shipment markieren (SIGNAL)
    logging.info("6. Marking order as shipped (Signal)...")
    await handle.signal(
        OrderWorkflow.mark_shipped,
        ShippingInfo(carrier="UPS", tracking_number="1Z999AA10123456784")
    )
    logging.info(f"   ✓ Shipment signal sent\n")

    # Final Progress (QUERY)
    logging.info("7. Querying final progress...")
    progress = await handle.query(OrderWorkflow.get_progress)
    logging.info(f"   Status: {progress.status}")
    logging.info(f"   Shipping: {progress.shipping_status}\n")

    # Auf Completion warten
    logging.info("8. Waiting for order completion...")
    result = await handle.result()
    logging.info(f"   ✓ Order completed\n")

    print(f"\n🎉 {result}\n")
    print("Demonstrated:")
    print("  ✓ Updates - add_item, process_payment (with validators)")
    print("  ✓ Queries - get_status, get_total, get_progress")
    print("  ✓ Signals - mark_shipped, cancel_order\n")


if __name__ == "__main__":
    asyncio.run(run_combined_example())
