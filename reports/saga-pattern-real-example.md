# Saga Pattern & Real-World Payment Processing mit Temporal

**Autor**: Claude Code
**Datum**: 2025-11-19
**Thema**: Praxisnahe Implementierung von Payment-Workflows mit Zeitlimits, Batch-Processing und Compensation

---

## Inhaltsverzeichnis

1. [Problemstellung](#problemstellung)
2. [Pattern 1: Stündliche Payment-Checks](#pattern-1-stündliche-payment-checks)
3. [Pattern 2: 14-Tage Timeout mit Rollback](#pattern-2-14-tage-timeout-mit-rollback)
4. [Pattern 3: Batch Processing statt parallele Checks](#pattern-3-batch-processing-statt-parallele-checks)
5. [Vollständiges Beispiel: E-Commerce Payment Flow](#vollständiges-beispiel-e-commerce-payment-flow)
6. [Best Practices & Production Considerations](#best-practices--production-considerations)
7. [Weiterführende Ressourcen](#weiterführende-ressourcen)

---

## Problemstellung

### Typisches E-Commerce Szenario

Ein Online-Shop nimmt Bestellungen entgegen, bei denen Kunden per Vorkasse bezahlen können. Die Herausforderungen:

1. **Zeitverzögerte Zahlung**: Kunde bestellt, zahlt aber erst später (Stunden bis Tage)
2. **Periodische Checks**: System muss regelmäßig prüfen, ob Zahlung eingegangen ist
3. **Deadline**: Nach 14 Tagen ohne Zahlung → Bestellung stornieren
4. **Skalierung**: Bei hunderten offenen Bestellungen nicht für jede einzeln das Payment-API abfragen

### Traditioneller Ansatz (problematisch)

```python
# ❌ PROBLEME:
# - Cron-Job alle 5 Minuten für ALLE Orders → API-Überlastung
# - State in Datenbank manuell tracken
# - Race Conditions bei parallelen Checks
# - Keine garantierte Kompensation bei Fehlern
# - Schwierig zu debuggen

def cron_check_payments():
    orders = db.query("SELECT * FROM orders WHERE status='pending_payment'")
    for order in orders:
        # Jede Order = ein API-Call!
        payment = payment_api.check_payment(order.id)
        if payment.status == "paid":
            db.execute("UPDATE orders SET status='approved' WHERE id=?", order.id)
            inventory.reserve(order.id)
            shipping.schedule(order.id)
        elif order.created_at < now() - timedelta(days=14):
            db.execute("UPDATE orders SET status='cancelled' WHERE id=?", order.id)
            # Was ist mit Rollback von bereits reserviertem Inventory?
```

### Temporal Lösung (elegant)

Mit Temporal verschwinden diese Probleme:
- **Durable Execution**: Workflow läuft zuverlässig über Wochen
- **Native Sleep**: `workflow.sleep(hours=1)` ohne CPU-Verbrauch
- **Automatische Wiederherstellung**: Bei Worker-Crash einfach fortsetzen
- **Saga Pattern**: Strukturierte Compensation bei Timeouts
- **Batch Processing**: Effiziente API-Nutzung

---

## Pattern 1: Stündliche Payment-Checks

### Variante A: Loop mit Sleep (für einzelne Orders)

```python
from temporalio import workflow, activity
from datetime import timedelta
from typing import Optional

@activity.defn
async def check_payment_status(order_id: str) -> Optional[str]:
    """
    Prüft bei Payment-Provider ob Zahlung eingegangen ist.

    Returns:
        - "paid" wenn Zahlung eingegangen
        - "pending" wenn noch ausstehend
        - "failed" bei Zahlungsfehler
    """
    activity.logger.info(f"Checking payment for order {order_id}")

    # Realer API-Call
    payment_result = await payment_api.get_payment_status(order_id)

    return payment_result.status


@workflow.defn
class OrderPaymentMonitorWorkflow:
    """
    Wartet auf Zahlung mit stündlichen Checks für bis zu 14 Tage.
    """

    def __init__(self):
        self.payment_status = "pending"

    @workflow.run
    async def run(self, order_id: str, max_days: int = 14) -> dict:
        max_attempts = max_days * 24  # 14 Tage * 24 Stunden = 336 Checks

        workflow.logger.info(
            f"Starting payment monitoring for order {order_id} "
            f"(max {max_days} days, hourly checks)"
        )

        for attempt in range(max_attempts):
            hours_elapsed = attempt + 1

            # Check payment status via Activity
            status = await workflow.execute_activity(
                check_payment_status,
                order_id,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(minutes=1),
                    maximum_attempts=3,
                )
            )

            if status == "paid":
                workflow.logger.info(
                    f"Payment received after {hours_elapsed} hours "
                    f"({hours_elapsed / 24:.1f} days)"
                )
                return {
                    "status": "payment_confirmed",
                    "hours_waited": hours_elapsed,
                    "order_id": order_id
                }

            elif status == "failed":
                workflow.logger.warning(f"Payment failed for order {order_id}")
                return {
                    "status": "payment_failed",
                    "hours_waited": hours_elapsed,
                    "order_id": order_id
                }

            # Status ist "pending" - warte 1 Stunde
            workflow.logger.info(
                f"Payment still pending after {hours_elapsed} hours. "
                f"Next check in 1 hour ({max_attempts - hours_elapsed} checks remaining)"
            )

            # Warte 1 Stunde (KEINE CPU-Nutzung während des Sleeps!)
            await workflow.sleep(timedelta(hours=1))

        # Nach 14 Tagen: Timeout
        workflow.logger.warning(
            f"Payment timeout for order {order_id} after {max_days} days"
        )
        return {
            "status": "timeout",
            "hours_waited": max_attempts,
            "order_id": order_id
        }
```

**Vorteile dieser Variante:**
- ✅ Einfach zu verstehen
- ✅ Pro Order ein eigener Workflow → perfekte Isolation
- ✅ Volle Observability in Temporal Web UI
- ✅ Kann jederzeit mit Signal abgebrochen werden

**Nachteile:**
- ❌ Bei 1000 Orders → 1000 Workflows → 1000 API-Calls pro Stunde

### Variante B: Temporal Schedules (für wiederkehrende Batch-Jobs)

```python
from temporalio.client import Client, Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleIntervalSpec

async def setup_hourly_payment_batch_check():
    """
    Richtet einen stündlichen Batch-Check für ALLE offenen Orders ein.
    """
    client = await Client.connect("localhost:7233")

    await client.create_schedule(
        "hourly-payment-batch-check",
        Schedule(
            action=ScheduleActionStartWorkflow(
                BatchPaymentCheckWorkflow.run,
                id="payment-batch-{datetime}",  # Eindeutige ID pro Run
                task_queue="payment-checks",
            ),
            spec=ScheduleSpec(
                # Option 1: Interval
                intervals=[ScheduleIntervalSpec(every=timedelta(hours=1))],

                # Option 2: Cron Expression (jeden Tag um 9:00 UTC)
                # cron_expressions=["0 9 * * *"]

                # Option 3: Mehrere Zeiten kombinieren
                # cron_expressions=["0 9,15,21 * * *"]  # 9:00, 15:00, 21:00
            ),
        ),
    )

    print("✓ Hourly payment batch check schedule created")


@workflow.defn
class BatchPaymentCheckWorkflow:
    """
    Wird stündlich ausgeführt, checkt alle offenen Orders in einem Batch.
    """

    @workflow.run
    async def run(self) -> dict:
        # Hole alle offenen Orders (via Activity)
        open_orders = await workflow.execute_activity(
            get_pending_payment_orders,
            start_to_close_timeout=timedelta(minutes=5)
        )

        workflow.logger.info(f"Batch checking {len(open_orders)} pending orders")

        # Siehe Pattern 3 für effiziente Batch-Verarbeitung
        results = await self.process_orders_in_batches(open_orders)

        return {
            "total_checked": len(open_orders),
            "paid": results["paid"],
            "pending": results["pending"],
            "timeout": results["timeout"]
        }
```

**Schedule Management:**

```python
# Schedule pausieren
await client.pause_schedule("hourly-payment-batch-check")

# Schedule wieder aktivieren
await client.unpause_schedule("hourly-payment-batch-check")

# Schedule löschen
await client.delete_schedule("hourly-payment-batch-check")

# Schedule Status abfragen
handle = client.get_schedule_handle("hourly-payment-batch-check")
description = await handle.describe()
print(f"Next run at: {description.info.next_action_times[0]}")
```

---

## Pattern 2: 14-Tage Timeout mit Rollback

### Das Saga Pattern mit Compensation

```python
from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError, ApplicationError
from datetime import timedelta
from typing import Optional

# ============================================================================
# ACTIVITIES: Business Logic
# ============================================================================

@activity.defn
async def reserve_inventory(order_id: str, items: list) -> str:
    """Reserviert Lagerbestand für die Bestellung."""
    activity.logger.info(f"Reserving inventory for order {order_id}")

    reservation_id = await inventory_service.reserve(order_id, items)

    activity.logger.info(f"Inventory reserved: {reservation_id}")
    return reservation_id


@activity.defn
async def release_inventory(reservation_id: str) -> None:
    """COMPENSATION: Gibt reservierten Lagerbestand frei."""
    activity.logger.warning(f"COMPENSATION: Releasing inventory {reservation_id}")

    await inventory_service.release(reservation_id)

    activity.logger.info(f"Inventory released: {reservation_id}")


@activity.defn
async def create_payment_hold(order_id: str, amount: float) -> str:
    """Blockiert Betrag auf Kundenkonto (Pre-Authorization)."""
    activity.logger.info(f"Creating payment hold for order {order_id}: ${amount}")

    hold_id = await payment_service.create_hold(order_id, amount)

    activity.logger.info(f"Payment hold created: {hold_id}")
    return hold_id


@activity.defn
async def release_payment_hold(hold_id: str) -> None:
    """COMPENSATION: Gibt Pre-Authorization wieder frei."""
    activity.logger.warning(f"COMPENSATION: Releasing payment hold {hold_id}")

    await payment_service.release_hold(hold_id)

    activity.logger.info(f"Payment hold released: {hold_id}")


@activity.defn
async def capture_payment(hold_id: str) -> str:
    """Zieht Zahlung endgültig ein (Capture)."""
    activity.logger.info(f"Capturing payment {hold_id}")

    payment_id = await payment_service.capture(hold_id)

    activity.logger.info(f"Payment captured: {payment_id}")
    return payment_id


@activity.defn
async def refund_payment(payment_id: str) -> None:
    """COMPENSATION: Erstattet bereits eingezogene Zahlung."""
    activity.logger.warning(f"COMPENSATION: Refunding payment {payment_id}")

    await payment_service.refund(payment_id)

    activity.logger.info(f"Payment refunded: {payment_id}")


@activity.defn
async def schedule_shipping(order_id: str) -> str:
    """Beauftragt Versanddienstleister."""
    activity.logger.info(f"Scheduling shipping for order {order_id}")

    shipment_id = await shipping_service.create_shipment(order_id)

    activity.logger.info(f"Shipping scheduled: {shipment_id}")
    return shipment_id


@activity.defn
async def cancel_shipping(shipment_id: str) -> None:
    """COMPENSATION: Storniert Versand."""
    activity.logger.warning(f"COMPENSATION: Cancelling shipment {shipment_id}")

    await shipping_service.cancel(shipment_id)

    activity.logger.info(f"Shipment cancelled: {shipment_id}")


@activity.defn
async def send_confirmation_email(order_id: str, email_type: str) -> None:
    """Sendet Bestätigungs-E-Mail an Kunden."""
    activity.logger.info(f"Sending {email_type} email for order {order_id}")

    await email_service.send(order_id, email_type)


# ============================================================================
# WORKFLOW: Saga Orchestrierung mit Compensation
# ============================================================================

@workflow.defn
class OrderSagaWorkflow:
    """
    Saga Pattern für E-Commerce Order mit automatischem Rollback.

    Flow:
    1. Reserve Inventory
    2. Create Payment Hold
    3. Wait for Payment Confirmation (max 14 Tage)
    4. Capture Payment
    5. Schedule Shipping
    6. Send Confirmation

    Bei Fehler/Timeout: Compensation aller completed steps (LIFO-Reihenfolge)
    """

    def __init__(self):
        self.completed_steps: list[str] = []  # Track für Compensation
        self.reservation_id: Optional[str] = None
        self.hold_id: Optional[str] = None
        self.payment_id: Optional[str] = None
        self.shipment_id: Optional[str] = None
        self.payment_confirmed = False

    @workflow.run
    async def run(self, order_id: str, items: list, amount: float) -> dict:
        """
        Hauptlogik der Saga.
        """
        workflow.logger.info(f"Starting Order Saga for {order_id} (Amount: ${amount})")

        try:
            # ================================================================
            # STEP 1: Reserve Inventory
            # ================================================================
            workflow.logger.info("Step 1/6: Reserving inventory...")
            self.reservation_id = await workflow.execute_activity(
                reserve_inventory,
                args=[order_id, items],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            self.completed_steps.append("inventory")
            workflow.logger.info(f"✓ Inventory reserved: {self.reservation_id}")

            # ================================================================
            # STEP 2: Create Payment Hold (Pre-Auth)
            # ================================================================
            workflow.logger.info("Step 2/6: Creating payment hold...")
            self.hold_id = await workflow.execute_activity(
                create_payment_hold,
                args=[order_id, amount],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            self.completed_steps.append("payment_hold")
            workflow.logger.info(f"✓ Payment hold created: {self.hold_id}")

            # ================================================================
            # STEP 3: Wait for Payment Confirmation (max 14 Tage)
            # ================================================================
            workflow.logger.info("Step 3/6: Waiting for payment confirmation...")

            # Signal-basiertes Warten mit Timeout
            try:
                await workflow.wait_condition(
                    lambda: self.payment_confirmed,
                    timeout=timedelta(days=14)  # 14-TAGE DEADLINE!
                )
                workflow.logger.info("✓ Payment confirmed by customer")

            except asyncio.TimeoutError:
                raise ApplicationError(
                    f"Payment timeout: No payment received within 14 days for order {order_id}",
                    non_retryable=True
                )

            # ================================================================
            # STEP 4: Capture Payment (endgültiger Einzug)
            # ================================================================
            workflow.logger.info("Step 4/6: Capturing payment...")
            self.payment_id = await workflow.execute_activity(
                capture_payment,
                self.hold_id,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=5)  # Wichtig!
            )
            self.completed_steps.append("payment_captured")
            workflow.logger.info(f"✓ Payment captured: {self.payment_id}")

            # ================================================================
            # STEP 5: Schedule Shipping
            # ================================================================
            workflow.logger.info("Step 5/6: Scheduling shipping...")
            self.shipment_id = await workflow.execute_activity(
                schedule_shipping,
                order_id,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            self.completed_steps.append("shipping")
            workflow.logger.info(f"✓ Shipping scheduled: {self.shipment_id}")

            # ================================================================
            # STEP 6: Send Confirmation Email
            # ================================================================
            workflow.logger.info("Step 6/6: Sending confirmation email...")
            await workflow.execute_activity(
                send_confirmation_email,
                args=[order_id, "order_confirmed"],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=5)
            )
            workflow.logger.info("✓ Confirmation email sent")

            # SUCCESS!
            workflow.logger.info(f"✅ Order Saga completed successfully: {order_id}")
            return {
                "status": "completed",
                "order_id": order_id,
                "payment_id": self.payment_id,
                "shipment_id": self.shipment_id
            }

        except Exception as e:
            # ================================================================
            # FEHLER → COMPENSATION (Rollback)
            # ================================================================
            workflow.logger.error(
                f"❌ Order Saga failed for {order_id}: {e}. "
                f"Starting compensation for steps: {self.completed_steps}"
            )

            await self.compensate(order_id)

            return {
                "status": "cancelled",
                "order_id": order_id,
                "reason": str(e),
                "compensated_steps": self.completed_steps
            }

    @workflow.signal
    async def confirm_payment(self):
        """
        Signal von externem System wenn Zahlung eingegangen ist.
        """
        workflow.logger.info("Payment confirmation signal received!")
        self.payment_confirmed = True

    async def compensate(self, order_id: str):
        """
        Rollback aller completed steps in LIFO-Reihenfolge (Last In, First Out).

        WICHTIG: Compensation Activities müssen IDEMPOTENT sein und
                 aggressive Retry Policies haben!
        """
        workflow.logger.warning(f"🔄 Starting compensation for order {order_id}")

        # LIFO: Neueste Steps zuerst rückgängig machen
        compensation_retry = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=5),
            backoff_coefficient=2.0,
            maximum_attempts=10  # Compensation MUSS erfolgreich sein!
        )

        # Schritt 5 Rollback: Shipping stornieren
        if "shipping" in self.completed_steps and self.shipment_id:
            workflow.logger.info("Compensating: Cancelling shipping...")
            try:
                await workflow.execute_activity(
                    cancel_shipping,
                    self.shipment_id,
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=compensation_retry
                )
                workflow.logger.info("✓ Shipping cancelled")
            except Exception as e:
                workflow.logger.error(f"Failed to cancel shipping: {e}")

        # Schritt 4 Rollback: Payment refunden (falls bereits captured)
        if "payment_captured" in self.completed_steps and self.payment_id:
            workflow.logger.info("Compensating: Refunding payment...")
            try:
                await workflow.execute_activity(
                    refund_payment,
                    self.payment_id,
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=compensation_retry
                )
                workflow.logger.info("✓ Payment refunded")
            except Exception as e:
                workflow.logger.error(f"Failed to refund payment: {e}")

        # Schritt 2 Rollback: Payment Hold freigeben (falls noch nicht captured)
        if "payment_hold" in self.completed_steps and self.hold_id:
            workflow.logger.info("Compensating: Releasing payment hold...")
            try:
                await workflow.execute_activity(
                    release_payment_hold,
                    self.hold_id,
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=compensation_retry
                )
                workflow.logger.info("✓ Payment hold released")
            except Exception as e:
                workflow.logger.error(f"Failed to release payment hold: {e}")

        # Schritt 1 Rollback: Inventory freigeben
        if "inventory" in self.completed_steps and self.reservation_id:
            workflow.logger.info("Compensating: Releasing inventory...")
            try:
                await workflow.execute_activity(
                    release_inventory,
                    self.reservation_id,
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=compensation_retry
                )
                workflow.logger.info("✓ Inventory released")
            except Exception as e:
                workflow.logger.error(f"Failed to release inventory: {e}")

        # Sende Storno-E-Mail
        workflow.logger.info("Sending cancellation email...")
        try:
            await workflow.execute_activity(
                send_confirmation_email,
                args=[order_id, "order_cancelled"],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=5)
            )
        except Exception as e:
            workflow.logger.error(f"Failed to send cancellation email: {e}")

        workflow.logger.warning(f"✓ Compensation completed for order {order_id}")
```

### Workflow Starten mit Execution Timeout

```python
from temporalio.client import Client

async def start_order_saga():
    client = await Client.connect("localhost:7233")

    # WICHTIG: Execution Timeout MUSS länger sein als:
    # - Max. Wartezeit (14 Tage)
    # - Zeit für Compensation (z.B. 1 Stunde)
    execution_timeout = timedelta(days=14, hours=1)

    handle = await client.start_workflow(
        OrderSagaWorkflow.run,
        args=["order-123", ["item1", "item2"], 99.99],
        id=f"order-saga-order-123",
        task_queue="orders",
        execution_timeout=execution_timeout,
    )

    print(f"✓ Order Saga started: {handle.id}")

    # Optional: Warte auf Ergebnis (oder lasse Worker im Hintergrund laufen)
    # result = await handle.result()
    # print(f"Result: {result}")
```

### Payment bestätigen (von externem System)

```python
async def confirm_payment_received(order_id: str):
    """
    Wird aufgerufen wenn Payment-Provider Zahlung meldet (z.B. via Webhook).
    """
    client = await Client.connect("localhost:7233")

    handle = client.get_workflow_handle(f"order-saga-{order_id}")

    # Sende Signal an Workflow
    await handle.signal(OrderSagaWorkflow.confirm_payment)

    print(f"✓ Payment confirmation signal sent to order {order_id}")
```

---

## Pattern 3: Batch Processing statt parallele Checks

### Problem: Naiver Ansatz

```python
# ❌ SCHLECHT: 1000 Orders → 1000 parallele API-Calls
@workflow.defn
class BadPaymentCheckWorkflow:
    @workflow.run
    async def run(self, order_ids: list[str]):
        # Problem 1: Bloated Event History (1000+ Events)
        # Problem 2: Payment API Rate Limit exceeded
        # Problem 3: Schwierige Fehlerbehandlung

        tasks = [
            workflow.execute_activity(
                check_payment_status,
                order_id,
                start_to_close_timeout=timedelta(minutes=5)
            )
            for order_id in order_ids
        ]

        # 1000 gleichzeitige API-Calls → 💥
        results = await asyncio.gather(*tasks)
        return results
```

### Lösung A: Batch Activity (Eine API-Anfrage für viele Orders)

```python
@activity.defn
async def check_payments_batch(order_ids: list[str]) -> dict[str, str]:
    """
    Effiziente Batch-Prüfung: EINE API-Anfrage für alle Orders.

    Returns:
        Dict mapping order_id → payment_status
    """
    activity.logger.info(f"Batch-checking {len(order_ids)} payment statuses")

    # EINE API-Anfrage holt alle Payments der letzten Stunde
    recent_payments = await payment_api.get_recent_payments(
        since=datetime.now() - timedelta(hours=1),
        limit=1000
    )

    # Match Orders zu Payments
    results = {}
    payment_map = {p.order_id: p.status for p in recent_payments}

    for order_id in order_ids:
        if order_id in payment_map:
            results[order_id] = payment_map[order_id]
        else:
            results[order_id] = "pending"

    activity.logger.info(
        f"Batch check complete: "
        f"{sum(1 for s in results.values() if s == 'paid')} paid, "
        f"{sum(1 for s in results.values() if s == 'pending')} pending"
    )

    return results


@workflow.defn
class BatchPaymentCheckWorkflow:
    """
    Batch-Processing von vielen Orders mit Chunking.
    """

    @workflow.run
    async def run(self, order_ids: list[str]) -> dict:
        total_orders = len(order_ids)
        chunk_size = 100  # Max. 100 Orders pro Batch Activity

        workflow.logger.info(
            f"Starting batch payment check for {total_orders} orders "
            f"(chunks of {chunk_size})"
        )

        all_results = {}
        chunks_processed = 0

        # Verarbeite in Chunks um Event History klein zu halten
        for i in range(0, total_orders, chunk_size):
            chunk = order_ids[i:i + chunk_size]
            chunk_num = (i // chunk_size) + 1
            total_chunks = (total_orders + chunk_size - 1) // chunk_size

            workflow.logger.info(
                f"Processing chunk {chunk_num}/{total_chunks} ({len(chunk)} orders)"
            )

            # Batch-Check für diesen Chunk
            chunk_results = await workflow.execute_activity(
                check_payments_batch,
                chunk,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )

            all_results.update(chunk_results)
            chunks_processed += 1

            # Optional: Continue-as-new bei sehr vielen Orders (>1000)
            if chunks_processed >= 10:  # Nach 10 Chunks (1000 Orders)
                remaining = order_ids[i + chunk_size:]
                if remaining:
                    workflow.logger.info(
                        f"Continue-as-new with {len(remaining)} remaining orders"
                    )
                    workflow.continue_as_new(remaining)

        # Aggregiere Ergebnisse
        stats = {
            "total": total_orders,
            "paid": sum(1 for s in all_results.values() if s == "paid"),
            "pending": sum(1 for s in all_results.values() if s == "pending"),
            "failed": sum(1 for s in all_results.values() if s == "failed")
        }

        workflow.logger.info(
            f"Batch check complete: {stats['paid']} paid, "
            f"{stats['pending']} pending, {stats['failed']} failed"
        )

        return {
            "stats": stats,
            "results": all_results
        }
```

### Lösung B: Child Workflows (bessere Observability)

```python
@workflow.defn
class PaymentCheckCoordinator:
    """
    Parent Workflow koordiniert viele Order-Workflows als Children.

    Vorteile:
    - Jeder Order hat eigenen Workflow → bessere Observability
    - Workflow History bleibt klein (kein Bloat)
    - Kann einzelne Orders gezielt manipulieren (Signal, Cancel)
    """

    @workflow.run
    async def run(self, order_ids: list[str]) -> dict:
        workflow.logger.info(
            f"Starting payment coordinator for {len(order_ids)} orders"
        )

        # Starte Child Workflow pro Order (non-blocking)
        child_handles = []
        for order_id in order_ids:
            handle = await workflow.start_child_workflow(
                OrderPaymentMonitorWorkflow.run,
                args=[order_id, 14],  # max_days=14
                id=f"payment-monitor-{order_id}",
                task_queue="payment-monitors"
            )
            child_handles.append((order_id, handle))

        workflow.logger.info(f"✓ Started {len(child_handles)} child workflows")

        # Optional: Warte auf alle Children (oder lasse sie asynchron laufen)
        results = {}
        for order_id, handle in child_handles:
            try:
                result = await handle.result()
                results[order_id] = result
            except Exception as e:
                workflow.logger.error(f"Child workflow failed for {order_id}: {e}")
                results[order_id] = {"status": "error", "error": str(e)}

        # Aggregiere Ergebnisse
        stats = {
            "total": len(order_ids),
            "confirmed": sum(1 for r in results.values() if r.get("status") == "payment_confirmed"),
            "timeout": sum(1 for r in results.values() if r.get("status") == "timeout"),
            "failed": sum(1 for r in results.values() if r.get("status") == "payment_failed"),
            "error": sum(1 for r in results.values() if r.get("status") == "error"),
        }

        return {"stats": stats, "results": results}
```

### Hybrid-Ansatz: Batch Activity + Child Workflows

```python
@workflow.defn
class HybridPaymentCheckWorkflow:
    """
    Best of Both Worlds:
    - Batch Activity für effizienten API-Check
    - Child Workflows für Orders die spezielle Behandlung brauchen
    """

    @workflow.run
    async def run(self, order_ids: list[str]) -> dict:
        # Phase 1: Schneller Batch-Check aller Orders
        batch_results = await workflow.execute_activity(
            check_payments_batch,
            order_ids,
            start_to_close_timeout=timedelta(minutes=5)
        )

        # Phase 2: Segmentiere Ergebnisse
        paid_orders = [oid for oid, status in batch_results.items() if status == "paid"]
        pending_orders = [oid for oid, status in batch_results.items() if status == "pending"]

        # Phase 3: Orders mit Zahlung → Child Workflows für Fulfillment
        fulfillment_handles = []
        for order_id in paid_orders:
            handle = await workflow.start_child_workflow(
                OrderFulfillmentWorkflow.run,
                order_id,
                id=f"fulfillment-{order_id}"
            )
            fulfillment_handles.append(handle)

        workflow.logger.info(
            f"Batch complete: {len(paid_orders)} paid (starting fulfillment), "
            f"{len(pending_orders)} still pending"
        )

        return {
            "paid": len(paid_orders),
            "pending": len(pending_orders),
            "fulfillment_started": len(fulfillment_handles)
        }
```

---

## Vollständiges Beispiel: E-Commerce Payment Flow

### Szenario

Ein Online-Shop mit folgenden Requirements:

1. Kunde bestellt, kann aber auch später zahlen
2. Stündliche Payment-Checks
3. Nach 14 Tagen ohne Zahlung → Automatische Stornierung
4. Bei hunderten Orders → Effizienter Batch-Check
5. Bei Zahlung → Automatischer Fulfillment-Prozess
6. Bei Stornierung → Vollständiger Rollback (Saga)

### System-Architektur

```python
# ============================================================================
# main.py - Temporal Worker Setup
# ============================================================================

import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

async def main():
    # Connect to Temporal
    client = await Client.connect("localhost:7233")

    # Worker 1: Order Sagas
    order_worker = Worker(
        client,
        task_queue="orders",
        workflows=[OrderSagaWorkflow],
        activities=[
            reserve_inventory,
            release_inventory,
            create_payment_hold,
            release_payment_hold,
            capture_payment,
            refund_payment,
            schedule_shipping,
            cancel_shipping,
            send_confirmation_email,
        ],
    )

    # Worker 2: Payment Monitoring
    payment_worker = Worker(
        client,
        task_queue="payment-checks",
        workflows=[
            BatchPaymentCheckWorkflow,
            OrderPaymentMonitorWorkflow,
            PaymentCheckCoordinator,
        ],
        activities=[
            check_payment_status,
            check_payments_batch,
            get_pending_payment_orders,
        ],
    )

    # Starte Workers
    print("🚀 Starting Temporal Workers...")
    await asyncio.gather(
        order_worker.run(),
        payment_worker.run(),
    )

if __name__ == "__main__":
    asyncio.run(main())
```

### Client Code: Order erstellen

```python
# ============================================================================
# create_order.py - Neue Bestellung erstellen
# ============================================================================

async def create_new_order(order_id: str, items: list, amount: float):
    """
    Erstellt neue Bestellung mit automatischem Payment-Monitoring.
    """
    client = await Client.connect("localhost:7233")

    # Start Order Saga Workflow
    saga_handle = await client.start_workflow(
        OrderSagaWorkflow.run,
        args=[order_id, items, amount],
        id=f"order-saga-{order_id}",
        task_queue="orders",
        execution_timeout=timedelta(days=14, hours=1),
    )

    print(f"✓ Order Saga started: {order_id}")
    print(f"  Workflow ID: {saga_handle.id}")
    print(f"  Web UI: http://localhost:8233/namespaces/default/workflows/{saga_handle.id}")

    return saga_handle


# Beispiel-Nutzung
if __name__ == "__main__":
    asyncio.run(create_new_order(
        order_id="ORD-2025-001",
        items=["laptop-123", "mouse-456"],
        amount=1299.99
    ))
```

### Webhook Handler: Payment Confirmation

```python
# ============================================================================
# payment_webhook.py - Webhook von Payment-Provider
# ============================================================================

from fastapi import FastAPI, BackgroundTasks

app = FastAPI()

@app.post("/webhooks/payment")
async def payment_webhook(
    payload: dict,
    background_tasks: BackgroundTasks
):
    """
    Webhook-Endpoint für Payment-Provider (z.B. Stripe).
    """
    order_id = payload.get("order_id")
    status = payload.get("status")

    if status == "paid":
        # Sende Signal an Temporal Workflow (im Background)
        background_tasks.add_task(send_payment_confirmation, order_id)

        return {"status": "accepted"}

    return {"status": "ignored"}


async def send_payment_confirmation(order_id: str):
    """
    Sendet Payment-Confirmation Signal an Temporal Workflow.
    """
    client = await Client.connect("localhost:7233")

    try:
        handle = client.get_workflow_handle(f"order-saga-{order_id}")
        await handle.signal(OrderSagaWorkflow.confirm_payment)

        print(f"✓ Payment confirmation sent to {order_id}")
    except Exception as e:
        print(f"❌ Failed to send payment confirmation: {e}")
```

### Scheduled Batch Check

```python
# ============================================================================
# setup_schedules.py - Einmalig: Schedules einrichten
# ============================================================================

async def setup_payment_monitoring_schedules():
    """
    Richtet automatische Batch-Checks ein.
    """
    client = await Client.connect("localhost:7233")

    # Stündlicher Batch-Check aller offenen Orders
    await client.create_schedule(
        "hourly-payment-batch",
        Schedule(
            action=ScheduleActionStartWorkflow(
                BatchPaymentCheckWorkflow.run,
                id="payment-batch-{datetime}",
                task_queue="payment-checks",
            ),
            spec=ScheduleSpec(
                intervals=[ScheduleIntervalSpec(every=timedelta(hours=1))]
            ),
        ),
    )

    print("✓ Hourly payment batch check schedule created")
    print("  Next run: Top of next hour")
    print("  Web UI: http://localhost:8233/namespaces/default/schedules/hourly-payment-batch")


if __name__ == "__main__":
    asyncio.run(setup_payment_monitoring_schedules())
```

---

## Best Practices & Production Considerations

### 1. Idempotenz ist kritisch

**Problem**: Temporal garantiert "At-Least-Once" Execution für Activities.

```python
# ❌ GEFÄHRLICH: Nicht idempotent
@activity.defn
async def charge_customer(order_id: str, amount: float):
    # Bei Retry → Kunde wird mehrfach belastet!
    await payment_api.charge(order_id, amount)


# ✅ SICHER: Idempotent mit Idempotency Key
@activity.defn
async def charge_customer_idempotent(order_id: str, amount: float, idempotency_key: str):
    # Payment-API prüft Idempotency Key
    await payment_api.charge(
        order_id,
        amount,
        idempotency_key=idempotency_key
    )
```

**Workflow generiert deterministischen Key:**

```python
@workflow.defn
class PaymentWorkflow:
    @workflow.run
    async def run(self, order_id: str, amount: float):
        # Deterministischer Idempotency Key (gleich bei Replay)
        idempotency_key = f"payment-{order_id}-{workflow.info().run_id}"

        await workflow.execute_activity(
            charge_customer_idempotent,
            args=[order_id, amount, idempotency_key],
            ...
        )
```

### 2. Timeouts richtig setzen

```python
# ❌ SCHLECHT: Workflow Timeout zu kurz
execution_timeout=timedelta(days=14)  # Compensation hat keine Zeit!

# ✅ GUT: Buffer für Compensation
execution_timeout=timedelta(days=14, hours=1)

# ❌ SCHLECHT: Activity Timeout zu kurz
start_to_close_timeout=timedelta(seconds=5)  # Payment API langsam

# ✅ GUT: Realistischer Timeout + Retries
start_to_close_timeout=timedelta(minutes=5),
retry_policy=RetryPolicy(maximum_attempts=3)
```

### 3. Compensation muss robust sein

```python
# Compensation Retry Policy: Aggressiv!
compensation_retry = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(minutes=5),
    backoff_coefficient=2.0,
    maximum_attempts=10,  # Viele Retries!
    non_retryable_error_types=[]  # ALLES wird retried
)
```

**Was wenn Compensation dauerhaft fehlschlägt?**

```python
async def compensate(self, order_id: str):
    """Compensation mit Fallback."""

    # Versuche automatische Compensation
    try:
        await workflow.execute_activity(
            release_inventory,
            self.reservation_id,
            retry_policy=compensation_retry
        )
    except Exception as e:
        workflow.logger.critical(
            f"❌ CRITICAL: Automatic compensation failed for {order_id}. "
            f"Manual intervention required! Error: {e}"
        )

        # Signal an Monitoring-System
        await workflow.execute_activity(
            send_alert_to_ops,
            args=[
                "COMPENSATION_FAILED",
                f"Order {order_id}, Reservation {self.reservation_id}",
                str(e)
            ],
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Oder: Schreibe in Dead-Letter Queue
        await workflow.execute_activity(
            write_to_dlq,
            {"order_id": order_id, "error": str(e), "context": "compensation"},
            start_to_close_timeout=timedelta(seconds=30)
        )
```

### 4. Event History Management

```python
@workflow.defn
class LargeScaleWorkflow:
    @workflow.run
    async def run(self, items: list):
        processed = 0
        batch_size = 100

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            # Process batch...
            processed += len(batch)

            # Continue-as-new alle 1000 Items (verhindert Event History Bloat)
            if processed >= 1000 and i + batch_size < len(items):
                remaining = items[i + batch_size:]
                workflow.continue_as_new(remaining)

        return {"processed": processed}
```

### 5. Monitoring & Alerting

```python
# Wichtige Metriken zu überwachen:

# Workflow-Level
workflow_execution_time_p99
workflow_failure_rate
workflow_timeout_rate

# Activity-Level
activity_execution_time_p99
activity_retry_rate
activity_failure_rate

# Payment-Spezifisch
payment_confirmation_time_median  # Wie lange dauert es bis Zahlung?
payment_timeout_rate  # Wie viele Orders timeout?
compensation_success_rate  # Wie oft klappt Rollback?
```

**Alerting Setup:**

```python
# Alert wenn:
# - Payment timeout rate > 5%
# - Compensation failure rate > 0.1%
# - Workflow execution time p99 > 15 Tage
```

### 6. Testing Strategies

```python
# ============================================================================
# test_order_saga.py - Unit & Integration Tests
# ============================================================================

import pytest
from temporalio.testing import WorkflowEnvironment

@pytest.mark.asyncio
async def test_order_saga_happy_path():
    """Test: Erfolgreicher Order Flow"""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        # Setup
        async with Worker(
            env.client,
            task_queue="test",
            workflows=[OrderSagaWorkflow],
            activities=[...],
        ):
            # Start Workflow
            handle = await env.client.start_workflow(
                OrderSagaWorkflow.run,
                args=["test-order", ["item"], 99.99],
                id="test-saga",
                task_queue="test",
            )

            # Simulate payment after 2 hours
            await env.sleep(timedelta(hours=2))
            await handle.signal(OrderSagaWorkflow.confirm_payment)

            # Verify success
            result = await handle.result()
            assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_order_saga_timeout_compensation():
    """Test: Timeout triggert Compensation"""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(env.client, task_queue="test", ...):
            handle = await env.client.start_workflow(
                OrderSagaWorkflow.run,
                args=["test-order", ["item"], 99.99],
                id="test-timeout",
                task_queue="test",
            )

            # Skip 14 days (no payment)
            await env.sleep(timedelta(days=14))

            # Verify compensation executed
            result = await handle.result()
            assert result["status"] == "cancelled"
            assert "inventory" in result["compensated_steps"]
            assert "payment_hold" in result["compensated_steps"]
```

### 7. Skalierung in Production

**Worker Scaling:**

```yaml
# kubernetes/workers.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: temporal-payment-workers
spec:
  replicas: 10  # Scale basierend auf Load
  template:
    spec:
      containers:
      - name: worker
        image: myapp/payment-worker:latest
        env:
        - name: TEMPORAL_ADDRESS
          value: "temporal-frontend.temporal:7233"
        - name: TASK_QUEUE
          value: "payment-checks"
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
```

**Auto-Scaling basierend auf Task Queue Length:**

```python
# Monitoring: Task Queue Backlog
temporal_task_queue_backlog{task_queue="payment-checks"} > 1000
→ Scale up workers
```

---

## Weiterführende Ressourcen

### Offizielle Temporal Dokumentation

- **Saga Pattern**: https://temporal.io/blog/compensating-actions-part-of-a-complete-breakfast-with-sagas
- **Temporal Schedules**: https://docs.temporal.io/workflows#schedule
- **Continue-As-New**: https://docs.temporal.io/workflows#continue-as-new
- **Retry Policies**: https://docs.temporal.io/retry-policies

### Community Patterns

- **Batch Processing**: https://community.temporal.io/t/batch-processing-best-practices/1139
- **Long-Running Workflows**: https://community.temporal.io/t/long-running-workflow-patterns/

### Code Examples

- **Temporal Samples (Python)**: https://github.com/temporalio/samples-python
- **Money Transfer Saga**: https://github.com/temporalio/samples-python/tree/main/saga

### Buchkapitel

- **Kapitel 2.2.3**: Continue-As-New Pattern (Zeile 188-217)
- **Kapitel 2.3.3**: Retry Policies (Zeile 430-497)
- **Kapitel 2.3.5**: Idempotenz (Zeile 548-614)

---

## Zusammenfassung

### Die drei Patterns im Überblick

| Pattern | Use Case | Temporal Lösung | Key Benefits |
|---------|----------|----------------|--------------|
| **Stündliche Checks** | Polling für Payment-Status | `workflow.sleep(hours=1)` oder Schedules | - Keine CPU während Sleep<br>- Läuft über Wochen zuverlässig |
| **14-Tage Timeout** | Deadline + Rollback | `wait_condition(timeout=14d)` + Saga | - Automatische Compensation<br>- ACID-ähnliche Garantien |
| **Batch Processing** | Tausende Orders effizient | Batch Activity + Child Workflows | - Eine API-Anfrage für viele Items<br>- Bessere Observability |

### Kritische Success Factors

1. ✅ **Idempotenz**: Alle Activities müssen idempotent sein
2. ✅ **Timeouts**: Realistische Timeouts + Buffer für Compensation
3. ✅ **Retries**: Aggressive Retry Policies für Compensation
4. ✅ **Event History**: Continue-as-new bei >1000 Events
5. ✅ **Monitoring**: Task Queue Backlog, Timeout Rates, Compensation Success

### Wann welches Pattern?

**Einzelne Order mit Payment-Warten:**
→ `OrderPaymentMonitorWorkflow` mit `sleep(hours=1)`

**Viele Orders parallel überwachen:**
→ `PaymentCheckCoordinator` mit Child Workflows

**Effiziente API-Nutzung:**
→ `BatchPaymentCheckWorkflow` mit Batch Activity

**Komplexe Transaktionen mit Rollback:**
→ `OrderSagaWorkflow` mit Compensation

**Regelmäßige System-weite Checks:**
→ Temporal Schedules mit `@hourly` oder `0 * * * *`

---

**Ende des Reports**
