"""
Update Example - Shopping Cart mit Validierung

Chapter: 6 - Kommunikation (Signale und Queries)
Demonstrates: Updates mit Validator für synchrone State Changes
"""

import asyncio
import sys
from pathlib import Path
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from datetime import timedelta

# Add project root to path for shared utilities
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.exceptions import WorkflowUpdateFailedError
from shared.temporal_helpers import create_temporal_client
from shared.examples_common import setup_logging
import logging


@dataclass
class CartItem:
    """Item für Shopping Cart"""
    sku: str
    name: str
    quantity: int
    price: Decimal


@activity.defn
async def check_inventory(item: CartItem) -> bool:
    """Prüfe Inventory-Verfügbarkeit"""
    activity.logger.info(f"Checking inventory for {item.sku}")
    # Simuliert Inventory-Check
    await asyncio.sleep(0.2)
    # Für Demo: "OUT-OF-STOCK" Items sind nicht verfügbar
    return "OUT-OF-STOCK" not in item.sku


@workflow.defn
class ShoppingCartWorkflow:
    """Shopping Cart mit Update-basierter Item-Verwaltung"""

    @workflow.init
    def __init__(self) -> None:
        self.items: List[CartItem] = []
        self.total = Decimal("0.00")
        self.lock = asyncio.Lock()

    @workflow.query
    def get_total(self) -> str:
        """Aktueller Total-Betrag"""
        return str(self.total)

    @workflow.query
    def get_item_count(self) -> int:
        """Anzahl Items im Cart"""
        return len(self.items)

    @workflow.update
    async def add_item(self, item: CartItem) -> dict:
        """Item hinzufügen (mit Inventory-Check und Validierung)"""
        async with self.lock:
            # Inventory prüfen via Activity
            available = await workflow.execute_activity(
                check_inventory,
                item,
                start_to_close_timeout=timedelta(seconds=10),
            )

            if not available:
                raise ValueError(f"Item {item.sku} is out of stock")

            # Item hinzufügen
            self.items.append(item)
            item_total = item.price * item.quantity
            self.total += item_total

            workflow.logger.info(
                f"Added {item.quantity}x {item.name} - "
                f"Item total: ${item_total}, Cart total: ${self.total}"
            )

            return {
                "items": len(self.items),
                "total": str(self.total),
                "item_added": item.name
            }

    @add_item.validator
    def validate_add_item(self, item: CartItem) -> None:
        """Validator: Frühe Ablehnung ungültiger Items"""
        # SKU validieren
        if not item.sku or len(item.sku) == 0:
            raise ValueError("Item SKU is required")

        # Quantity validieren
        if item.quantity <= 0:
            raise ValueError("Quantity must be positive")

        if item.quantity > 99:
            raise ValueError("Maximum quantity per item is 99")

        # Price validieren
        if item.price <= 0:
            raise ValueError("Price must be positive")

        # Cart-Limits
        if len(self.items) >= 50:
            raise ValueError("Cart is full (maximum 50 items)")

        # Duplikat-Check
        if any(i.sku == item.sku for i in self.items):
            raise ValueError(f"Item {item.sku} already in cart")

    @workflow.update
    def remove_item(self, sku: str) -> dict:
        """Item entfernen"""
        # Item finden
        item_to_remove = None
        for item in self.items:
            if item.sku == sku:
                item_to_remove = item
                break

        if not item_to_remove:
            raise ValueError(f"Item {sku} not found in cart")

        # Entfernen
        self.items.remove(item_to_remove)
        item_total = item_to_remove.price * item_to_remove.quantity
        self.total -= item_total

        workflow.logger.info(
            f"Removed {item_to_remove.name} - "
            f"New total: ${self.total}"
        )

        return {
            "items": len(self.items),
            "total": str(self.total),
            "item_removed": item_to_remove.name
        }

    @workflow.run
    async def run(self, customer_id: str) -> str:
        """Cart läuft 24h, dann automatischer Checkout oder Timeout"""
        workflow.logger.info(f"Shopping cart created for customer {customer_id}")

        # Warte 24 Stunden auf Items
        await asyncio.sleep(timedelta(hours=24))

        # Automatischer Checkout wenn Items vorhanden
        if len(self.items) > 0:
            workflow.logger.info(
                f"Auto-checkout: {len(self.items)} items, total ${self.total}"
            )
            return f"Cart checked out: {len(self.items)} items, ${self.total}"
        else:
            workflow.logger.info("Cart expired empty")
            return "Cart expired - no items added"


async def run_update_example():
    """Update-Beispiel: Shopping Cart mit Validierung"""
    setup_logging()
    logging.info("=== Update Example: Shopping Cart ===\n")

    client = await create_temporal_client()

    # Workflow starten
    customer_id = "customer-123"
    workflow_id = f"cart-{customer_id}"

    logging.info(f"1. Starting shopping cart for {customer_id}...")
    handle = await client.start_workflow(
        ShoppingCartWorkflow.run,
        customer_id,
        id=workflow_id,
        task_queue="book-examples",
    )
    logging.info(f"   Cart started: {workflow_id}\n")

    # Items hinzufügen (Update mit Validierung)
    logging.info("2. Adding items to cart (with validation)...\n")

    # Valid item
    try:
        result = await handle.execute_update(
            ShoppingCartWorkflow.add_item,
            CartItem(
                sku="LAPTOP-001",
                name="Gaming Laptop",
                quantity=1,
                price=Decimal("1299.99")
            )
        )
        logging.info(f"   ✓ {result['item_added']} added")
        logging.info(f"     Items: {result['items']}, Total: ${result['total']}\n")
    except WorkflowUpdateFailedError as e:
        logging.error(f"   ✗ Failed to add item: {e}\n")

    # Another valid item
    try:
        result = await handle.execute_update(
            ShoppingCartWorkflow.add_item,
            CartItem(
                sku="MOUSE-001",
                name="Wireless Mouse",
                quantity=2,
                price=Decimal("29.99")
            )
        )
        logging.info(f"   ✓ {result['item_added']} added")
        logging.info(f"     Items: {result['items']}, Total: ${result['total']}\n")
    except WorkflowUpdateFailedError as e:
        logging.error(f"   ✗ Failed to add item: {e}\n")

    # Invalid item: Validator rejection (negative price)
    logging.info("3. Attempting to add invalid item (negative price)...")
    try:
        result = await handle.execute_update(
            ShoppingCartWorkflow.add_item,
            CartItem(
                sku="INVALID-001",
                name="Invalid Item",
                quantity=1,
                price=Decimal("-10.00")  # Invalid!
            )
        )
    except WorkflowUpdateFailedError as e:
        logging.info(f"   ✓ Validator rejected: {e}\n")

    # Invalid item: Out of stock (Activity failure)
    logging.info("4. Attempting to add out-of-stock item...")
    try:
        result = await handle.execute_update(
            ShoppingCartWorkflow.add_item,
            CartItem(
                sku="OUT-OF-STOCK-001",
                name="Out of Stock Item",
                quantity=1,
                price=Decimal("99.99")
            )
        )
    except WorkflowUpdateFailedError as e:
        logging.info(f"   ✓ Update failed (out of stock): {e}\n")

    # Duplicate item (Validator rejection)
    logging.info("5. Attempting to add duplicate item...")
    try:
        result = await handle.execute_update(
            ShoppingCartWorkflow.add_item,
            CartItem(
                sku="LAPTOP-001",  # Already in cart!
                name="Gaming Laptop",
                quantity=1,
                price=Decimal("1299.99")
            )
        )
    except WorkflowUpdateFailedError as e:
        logging.info(f"   ✓ Validator rejected (duplicate): {e}\n")

    # Query final state
    logging.info("6. Querying final cart state...")
    total = await handle.query(ShoppingCartWorkflow.get_total)
    count = await handle.query(ShoppingCartWorkflow.get_item_count)
    logging.info(f"   Cart: {count} items, Total: ${total}\n")

    # Remove an item
    logging.info("7. Removing item from cart...")
    try:
        result = await handle.execute_update(
            ShoppingCartWorkflow.remove_item,
            "MOUSE-001"
        )
        logging.info(f"   ✓ {result['item_removed']} removed")
        logging.info(f"     New total: ${result['total']}\n")
    except WorkflowUpdateFailedError as e:
        logging.error(f"   ✗ Failed to remove item: {e}\n")

    # Final state
    total = await handle.query(ShoppingCartWorkflow.get_total)
    count = await handle.query(ShoppingCartWorkflow.get_item_count)
    print(f"\n🎉 Final cart: {count} items, Total: ${total}\n")

    # Note: Workflow läuft 24h - für Demo nicht warten
    logging.info("Note: Workflow runs for 24h (not waiting in demo)\n")


if __name__ == "__main__":
    asyncio.run(run_update_example())
