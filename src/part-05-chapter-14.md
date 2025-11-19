# Kapitel 14: Muster-Rezepte (Human-in-Loop, Cron, Order Fulfillment)

In diesem Kapitel untersuchen wir drei bewährte Workflow-Muster, die in der Praxis häufig vorkommen und für die Temporal besonders gut geeignet ist. Diese Muster zeigen die Stärken von Temporal bei der Orchestrierung komplexer Geschäftsprozesse.

## 14.1 Überblick: Warum Muster-Rezepte?

Während wir in den vorherigen Kapiteln die Grundlagen von Temporal kennengelernt haben, geht es nun darum, wie man häufige Geschäftsszenarien elegant und robust implementiert. Die drei Muster, die wir behandeln werden, repräsentieren typische Herausforderungen in verteilten Systemen:

- **Human-in-the-Loop**: Prozesse, die menschliche Eingaben oder Genehmigungen erfordern
- **Cron/Scheduling**: Zeitgesteuerte, wiederkehrende Aufgaben
- **Order Fulfillment (Saga)**: Verteilte Transaktionen über mehrere Services hinweg

## 14.2 Human-in-the-Loop Pattern

### Das Problem

Viele Geschäftsprozesse erfordern an bestimmten Punkten menschliche Entscheidungen oder Eingaben:

- Genehmigung von Urlaubsanträgen
- Überprüfung von Hintergrundüberprüfungen (Background Checks)
- Freigabe von Zahlungen über einem bestimmten Betrag
- Klärung von Mehrdeutigkeiten in automatisierten Prozessen

Die Herausforderung besteht darin, dass diese menschlichen Interaktionen unvorhersehbar lange dauern können – von Minuten bis zu Tagen oder sogar Wochen.

### Die Temporal-Lösung

Temporal ermöglicht es Workflows, auf menschliche Eingaben zu warten, ohne Ressourcen zu blockieren. Der Workflow kann für Stunden oder Tage "schlafen" und wird genau dort fortgesetzt, wo er gestoppt hat, sobald die Eingabe erfolgt.

**Wichtige Konzepte:**
- **Signals**: Ermöglichen es, Daten in einen laufenden Workflow zu senden
- **Queries**: Erlauben das Abfragen des aktuellen Workflow-Status
- **Timers**: Können als Timeout für zu lange Wartezeiten dienen

### Implementierungsbeispiel: Genehmigungsprozess

```python
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class ApprovalWorkflow:
    def __init__(self):
        self.approved = False
        self.rejection_reason = None

    @workflow.run
    async def run(self, request_data: dict) -> str:
        # 1. Sende Benachrichtigung an Genehmiger
        await workflow.execute_activity(
            send_approval_notification,
            request_data,
            start_to_close_timeout=timedelta(seconds=30)
        )

        # 2. Warte auf Genehmigung mit Timeout von 7 Tagen
        try:
            await workflow.wait_condition(
                lambda: self.approved or self.rejection_reason,
                timeout=timedelta(days=7)
            )
        except asyncio.TimeoutError:
            # Automatische Eskalation nach 7 Tagen
            await workflow.execute_activity(
                escalate_to_manager,
                request_data,
                start_to_close_timeout=timedelta(seconds=30)
            )
            # Warte weitere 3 Tage auf Manager
            await workflow.wait_condition(
                lambda: self.approved or self.rejection_reason,
                timeout=timedelta(days=3)
            )

        # 3. Verarbeite das Ergebnis
        if self.approved:
            await workflow.execute_activity(
                process_approval,
                request_data,
                start_to_close_timeout=timedelta(minutes=5)
            )
            return "approved"
        else:
            await workflow.execute_activity(
                notify_rejection,
                args=[request_data, self.rejection_reason],
                start_to_close_timeout=timedelta(seconds=30)
            )
            return f"rejected: {self.rejection_reason}"

    @workflow.signal
    async def approve(self):
        """Signal zum Genehmigen des Antrags"""
        self.approved = True

    @workflow.signal
    async def reject(self, reason: str):
        """Signal zum Ablehnen des Antrags"""
        self.rejection_reason = reason

    @workflow.query
    def get_status(self) -> dict:
        """Abfrage des aktuellen Status"""
        return {
            "approved": self.approved,
            "rejected": self.rejection_reason is not None,
            "pending": not self.approved and not self.rejection_reason
        }
```

**Verwendung des Workflows:**

```python
# Workflow starten
handle = await client.start_workflow(
    ApprovalWorkflow.run,
    request_data,
    id="approval-12345",
    task_queue="approval-tasks"
)

# Status abfragen (jederzeit möglich)
status = await handle.query(ApprovalWorkflow.get_status)
print(f"Current status: {status}")

# Genehmigung senden (kann Tage später erfolgen)
await handle.signal(ApprovalWorkflow.approve)

# Auf Ergebnis warten
result = await handle.result()
```

### Best Practices

1. **Timeouts verwenden**: Implementiere immer Timeouts und Eskalationsmechanismen
2. **Status abfragbar machen**: Nutze Queries, damit Benutzer den Status jederzeit prüfen können
3. **Benachrichtigungen senden**: Informiere Menschen aktiv über ausstehende Aktionen
4. **Idempotenz beachten**: Signals können mehrfach gesendet werden – handle dies entsprechend

## 14.3 Cron und Scheduling Pattern

### Warum nicht einfach Cron?

Traditionelle Cron-Jobs haben mehrere Probleme:

- Keine Visibilität in den Ausführungsstatus
- Keine einfache Möglichkeit, Jobs zu pausieren oder zu stoppen
- Schwierig zu testen und zu überwachen
- Keine Garantie für genau eine Ausführung (at-least-once, aber nicht exactly-once)
- Kein eingebautes Retry-Verhalten

### Temporal Schedules: Die bessere Alternative

Temporal Schedules bieten:

- **Vollständige Kontrolle**: Start, Stop, Pause, Update zur Laufzeit
- **Observability**: Einsicht in alle vergangenen und zukünftigen Ausführungen
- **Backfill**: Nachträgliches Ausführen verpasster Runs
- **Overlap-Policies**: Kontrolliere, was passiert, wenn ein Workflow noch läuft, während der nächste starten soll

### Schedule-Optionen

**1. Cron-Style Scheduling:**

```python
from temporalio.client import Client, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleIntervalSpec
from datetime import timedelta

async def create_cron_schedule():
    client = await Client.connect("localhost:7233")

    await client.create_schedule(
        id="daily-report-schedule",
        schedule=Schedule(
            action=ScheduleActionStartWorkflow(
                workflow_type=GenerateReportWorkflow,
                args=["daily"],
                id=f"daily-report-{datetime.now().strftime('%Y%m%d')}",
                task_queue="reporting"
            ),
            spec=ScheduleSpec(
                # Jeden Tag um 6 Uhr morgens UTC
                cron_expressions=["0 6 * * *"],
            ),
            # Was tun bei Überlappungen?
            policy=SchedulePolicy(
                overlap=ScheduleOverlapPolicy.SKIP,  # Überspringe, wenn noch läuft
            )
        )
    )
```

**Cron-Format in Temporal:**
```
┌───────────── Minute (0-59)
│ ┌───────────── Stunde (0-23)
│ │ ┌───────────── Tag des Monats (1-31)
│ │ │ ┌───────────── Monat (1-12)
│ │ │ │ ┌───────────── Tag der Woche (0-6, Sonntag = 0)
│ │ │ │ │
* * * * *
```

**Beispiele:**
- `0 9 * * 1-5`: Werktags um 9 Uhr
- `*/15 * * * *`: Alle 15 Minuten
- `0 0 1 * *`: Am ersten Tag jeden Monats um Mitternacht

**2. Interval-basiertes Scheduling:**

```python
await client.create_schedule(
    id="health-check-schedule",
    schedule=Schedule(
        action=ScheduleActionStartWorkflow(
            workflow_type=HealthCheckWorkflow,
            task_queue="monitoring"
        ),
        spec=ScheduleSpec(
            # Alle 5 Minuten
            intervals=[ScheduleIntervalSpec(
                every=timedelta(minutes=5)
            )],
        )
    )
)
```

### Overlap-Policies

Was passiert, wenn ein Workflow noch läuft, während der nächste geplant ist?

```python
from temporalio import ScheduleOverlapPolicy

# SKIP: Überspringe die neue Ausführung
policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.SKIP)

# BUFFER_ONE: Führe maximal eine weitere Ausführung in der Warteschlange
policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.BUFFER_ONE)

# BUFFER_ALL: Puffere alle Ausführungen (Vorsicht: kann zu Stau führen!)
policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.BUFFER_ALL)

# CANCEL_OTHER: Breche den laufenden Workflow ab und starte neu
policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.CANCEL_OTHER)

# ALLOW_ALL: Erlaube parallele Ausführungen
policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.ALLOW_ALL)
```

### Schedule-Management

```python
# Schedule abrufen
schedule_handle = client.get_schedule_handle("daily-report-schedule")

# Beschreibung abrufen
description = await schedule_handle.describe()
print(f"Next 5 runs: {description.info.next_action_times[:5]}")

# Pausieren
await schedule_handle.pause(note="Maintenance window")

# Wieder aktivieren
await schedule_handle.unpause(note="Maintenance complete")

# Einmalig manuell auslösen
await schedule_handle.trigger(overlap=ScheduleOverlapPolicy.ALLOW_ALL)

# Backfill: Verpasste Ausführungen nachholen
await schedule_handle.backfill(
    start_at=datetime(2024, 1, 1),
    end_at=datetime(2024, 1, 31),
    overlap=ScheduleOverlapPolicy.ALLOW_ALL
)

# Schedule löschen
await schedule_handle.delete()
```

### Workflow-Implementierung für Schedules

```python
@workflow.defn
class DataSyncWorkflow:
    @workflow.run
    async def run(self) -> dict:
        # Workflow weiß, ob er via Schedule gestartet wurde
        info = workflow.info()

        workflow.logger.info(
            f"Running scheduled sync. Attempt: {info.attempt}"
        )

        # Normale Workflow-Logik
        records = await workflow.execute_activity(
            fetch_new_records,
            start_to_close_timeout=timedelta(minutes=10)
        )

        await workflow.execute_activity(
            sync_to_database,
            records,
            start_to_close_timeout=timedelta(minutes=5)
        )

        return {
            "synced_records": len(records),
            "timestamp": datetime.now().isoformat()
        }
```

### Best Practices für Scheduling

1. **Idempotenz**: Schedules können Workflows mehrfach starten – stelle sicher, dass deine Logik idempotent ist
2. **Monitoring**: Nutze Temporal UI, um verpasste oder fehlgeschlagene Runs zu überwachen
3. **Overlap-Policy wählen**: Überlege genau, was bei Überlappungen passieren soll
4. **Zeitzone beachten**: Cron-Ausdrücke werden standardmäßig in UTC interpretiert
5. **Workflow-IDs**: Verwende dynamische Workflow-IDs mit Zeitstempel, um Duplikate zu vermeiden

## 14.4 Order Fulfillment mit dem Saga Pattern

### Das Problem: Verteilte Transaktionen

Stellen wir uns einen E-Commerce-Bestellprozess vor, der mehrere Services involviert:

1. **Inventory Service**: Prüfe Verfügbarkeit und reserviere Artikel
2. **Payment Service**: Belaste Kreditkarte
3. **Shipping Service**: Erstelle Versandetikett und beauftrage Versand
4. **Notification Service**: Sende Bestätigungsmail

Was passiert, wenn Schritt 3 fehlschlägt, nachdem wir bereits Schritt 1 und 2 ausgeführt haben? Wir müssen:
- Die Kreditkartenbelastung rückgängig machen (Schritt 2)
- Die Inventar-Reservierung aufheben (Schritt 1)

Dies ist das klassische Problem verteilter Transaktionen: **Entweder alle Schritte erfolgreich, oder keiner.**

### Das Saga Pattern

Ein Saga ist eine Sequenz von lokalen Transaktionen, wobei jede Transaktion eine **Kompensation** (Rückgängigmachung) hat. Falls ein Schritt fehlschlägt, werden alle vorherigen Schritte durch ihre Kompensationen rückgängig gemacht.

**Zwei Hauptkomponenten:**

1. **Forward-Recovery**: Die normalen Schritte vorwärts
2. **Backward-Recovery (Compensations)**: Die Rückgängigmachung bei Fehler

### Temporal vereinfacht Sagas

Ohne Temporal müsstest du:
- Selbst den Fortschritt tracken (Event Sourcing)
- Retry-Logik implementieren
- State Management über Services hinweg
- Crash-Recovery-Mechanismen bauen

Mit Temporal bekommst du all das **kostenlos**. Du musst nur die Kompensationen definieren.

### Implementierung: Order Fulfillment

```python
from temporalio import workflow, activity
from datetime import timedelta
from dataclasses import dataclass
from typing import Optional

@dataclass
class OrderInfo:
    order_id: str
    customer_id: str
    items: list[dict]
    total_amount: float
    idempotency_key: str  # Wichtig für Idempotenz!

@dataclass
class SagaCompensation:
    activity_name: str
    args: list

class Saga:
    """Helper-Klasse zum Verwalten von Kompensationen"""

    def __init__(self):
        self.compensations: list[SagaCompensation] = []

    def add_compensation(self, activity_name: str, *args):
        """Füge eine Kompensation hinzu"""
        self.compensations.append(
            SagaCompensation(activity_name, list(args))
        )

    async def compensate(self):
        """Führe alle Kompensationen in umgekehrter Reihenfolge aus"""
        # LIFO: Last In, First Out
        for comp in reversed(self.compensations):
            try:
                await workflow.execute_activity(
                    comp.activity_name,
                    args=comp.args,
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=workflow.RetryPolicy(
                        maximum_attempts=5,
                        initial_interval=timedelta(seconds=1),
                        maximum_interval=timedelta(seconds=60)
                    )
                )
                workflow.logger.info(f"Compensated: {comp.activity_name}")
            except Exception as e:
                workflow.logger.error(
                    f"Compensation failed for {comp.activity_name}: {e}"
                )
                # In Produktion: Dead Letter Queue, Alerting, etc.

@workflow.defn
class OrderFulfillmentWorkflow:
    @workflow.run
    async def run(self, order: OrderInfo) -> dict:
        saga = Saga()

        try:
            # Schritt 1: Inventar prüfen und reservieren
            inventory_reserved = await workflow.execute_activity(
                reserve_inventory,
                order,
                start_to_close_timeout=timedelta(minutes=2)
            )
            # Kompensation hinzufügen: Reservierung aufheben
            saga.add_compensation(
                "release_inventory",
                order.order_id,
                order.idempotency_key
            )
            workflow.logger.info(f"Inventory reserved: {inventory_reserved}")

            # Schritt 2: Zahlung durchführen
            payment_result = await workflow.execute_activity(
                charge_payment,
                order,
                start_to_close_timeout=timedelta(minutes=5)
            )
            # Kompensation hinzufügen: Zahlung erstatten
            saga.add_compensation(
                "refund_payment",
                payment_result["transaction_id"],
                order.total_amount,
                order.idempotency_key
            )
            workflow.logger.info(f"Payment charged: {payment_result}")

            # Schritt 3: Versand erstellen
            shipping_result = await workflow.execute_activity(
                create_shipment,
                order,
                start_to_close_timeout=timedelta(minutes=3)
            )
            # Kompensation hinzufügen: Versand stornieren
            saga.add_compensation(
                "cancel_shipment",
                shipping_result["shipment_id"],
                order.idempotency_key
            )
            workflow.logger.info(f"Shipment created: {shipping_result}")

            # Schritt 4: Bestätigung senden (keine Kompensation nötig)
            await workflow.execute_activity(
                send_confirmation_email,
                order,
                start_to_close_timeout=timedelta(seconds=30)
            )

            # Erfolg!
            return {
                "status": "fulfilled",
                "order_id": order.order_id,
                "tracking_number": shipping_result["tracking_number"]
            }

        except Exception as e:
            workflow.logger.error(f"Order fulfillment failed: {e}")
            # Kompensiere alle bisherigen Schritte
            await saga.compensate()

            # Sende Fehlerbenachrichtigung
            await workflow.execute_activity(
                send_error_notification,
                args=[order, str(e)],
                start_to_close_timeout=timedelta(seconds=30)
            )

            return {
                "status": "failed",
                "order_id": order.order_id,
                "error": str(e)
            }
```

### Activity-Implementierungen

```python
# Activities mit Idempotenz

@activity.defn
async def reserve_inventory(order: OrderInfo) -> bool:
    """Reserviere Artikel im Inventar"""
    # Verwende idempotency_key, um Duplikate zu vermeiden
    response = await inventory_service.reserve(
        items=order.items,
        order_id=order.order_id,
        idempotency_key=order.idempotency_key
    )
    return response.success

@activity.defn
async def release_inventory(order_id: str, idempotency_key: str):
    """Kompensation: Gib Inventar-Reservierung frei"""
    await inventory_service.release(
        order_id=order_id,
        idempotency_key=f"{idempotency_key}-release"
    )

@activity.defn
async def charge_payment(order: OrderInfo) -> dict:
    """Belaste Zahlungsmittel"""
    # Viele Payment-APIs akzeptieren bereits idempotency_keys
    response = await payment_service.charge(
        customer_id=order.customer_id,
        amount=order.total_amount,
        idempotency_key=order.idempotency_key
    )
    return {
        "transaction_id": response.transaction_id,
        "status": response.status
    }

@activity.defn
async def refund_payment(
    transaction_id: str,
    amount: float,
    idempotency_key: str
):
    """Kompensation: Erstatte Zahlung"""
    await payment_service.refund(
        transaction_id=transaction_id,
        amount=amount,
        idempotency_key=f"{idempotency_key}-refund"
    )

@activity.defn
async def create_shipment(order: OrderInfo) -> dict:
    """Erstelle Versandetikett"""
    response = await shipping_service.create_shipment(
        order=order,
        idempotency_key=order.idempotency_key
    )
    return {
        "shipment_id": response.shipment_id,
        "tracking_number": response.tracking_number
    }

@activity.defn
async def cancel_shipment(shipment_id: str, idempotency_key: str):
    """Kompensation: Storniere Versand"""
    await shipping_service.cancel(
        shipment_id=shipment_id,
        idempotency_key=f"{idempotency_key}-cancel"
    )

@activity.defn
async def send_confirmation_email(order: OrderInfo):
    """Sende Bestätigungs-E-Mail"""
    await email_service.send(
        to=order.customer_id,
        template="order_confirmation",
        data=order
    )

@activity.defn
async def send_error_notification(order: OrderInfo, error: str):
    """Sende Fehler-Benachrichtigung"""
    await email_service.send(
        to=order.customer_id,
        template="order_failed",
        data={"order": order, "error": error}
    )
```

### Kritisches Konzept: Idempotenz

Da Temporal Activities automatisch wiederholt, **müssen** alle Activities idempotent sein:

```python
# Schlechtes Beispiel: Nicht idempotent
async def charge_payment_bad(customer_id: str, amount: float):
    # Könnte bei Retry mehrfach belasten!
    return payment_api.charge(customer_id, amount)

# Gutes Beispiel: Idempotent mit Key
async def charge_payment_good(
    customer_id: str,
    amount: float,
    idempotency_key: str
):
    # Payment-API prüft den Key und führt nur einmal aus
    return payment_api.charge(
        customer_id,
        amount,
        idempotency_key=idempotency_key
    )
```

**Best Practices für Idempotenz:**

1. **Idempotenz-Keys verwenden**: UUIDs oder zusammengesetzte Keys (z.B. `{order_id}-{operation}`)
2. **API-Unterstützung nutzen**: Viele APIs (Stripe, PayPal, etc.) akzeptieren bereits Idempotenz-Keys
3. **Datenbank-Constraints**: Unique-Constraints auf Keys in der Datenbank
4. **State-Checks**: Prüfe vor Ausführung, ob Operation bereits durchgeführt wurde

### Erweiterte Saga-Techniken

**Parallele Kompensationen:**

```python
async def compensate_parallel(self):
    """Führe Kompensationen parallel aus für bessere Performance"""
    tasks = []
    for comp in reversed(self.compensations):
        task = workflow.execute_activity(
            comp.activity_name,
            args=comp.args,
            start_to_close_timeout=timedelta(minutes=5)
        )
        tasks.append(task)

    # Warte auf alle Kompensationen
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            workflow.logger.error(
                f"Compensation failed: {self.compensations[i].activity_name}"
            )
```

**Teilweise Kompensation:**

```python
class Saga:
    def __init__(self):
        self.compensations: list[SagaCompensation] = []
        self.checkpoints: list[str] = []

    def add_checkpoint(self, name: str):
        """Setze einen Checkpoint für teilweise Kompensation"""
        self.checkpoints.append(name)

    async def compensate_to_checkpoint(self, checkpoint_name: str):
        """Kompensiere nur bis zu einem bestimmten Checkpoint"""
        checkpoint_index = self.checkpoints.index(checkpoint_name)
        for comp in reversed(self.compensations[:checkpoint_index]):
            await workflow.execute_activity(...)
```

### Wann Sagas verwenden?

**Geeignet für:**
- E-Commerce Order Processing
- Reisebuchungen (Flug + Hotel + Mietwagen)
- Finanzielle Transaktionen über mehrere Konten
- Multi-Service Workflows mit "Alles-oder-Nichts"-Semantik

**Nicht geeignet für:**
- Einfache, nicht-transaktionale Workflows
- Workflows ohne Notwendigkeit für Rollback
- Szenarien, wo echte ACID-Transaktionen möglich sind

## 14.5 Zusammenfassung

In diesem Kapitel haben wir drei essenzielle Workflow-Muster kennengelernt:

### Human-in-the-Loop
- **Problem**: Workflows benötigen menschliche Eingaben mit unvorhersehbarer Dauer
- **Lösung**: Signals zum Senden von Eingaben, Queries zum Abfragen des Status, Timers für Timeouts
- **Key Takeaway**: Temporal-Workflows können problemlos Tage oder Wochen auf Input warten

### Cron/Scheduling
- **Problem**: Traditionelle Cron-Jobs sind schwer zu überwachen und zu steuern
- **Lösung**: Temporal Schedules mit voller Kontrolle, Observability und Overlap-Policies
- **Key Takeaway**: Schedules sind Cron-Jobs mit Superkräften

### Order Fulfillment (Saga Pattern)
- **Problem**: Verteilte Transaktionen über mehrere Services ohne echte ACID-Garantien
- **Lösung**: Saga Pattern mit Kompensationen für Rollback, Temporal übernimmt State-Management
- **Key Takeaway**: Idempotenz ist kritisch, Temporal macht Sagas einfach

### Gemeinsame Prinzipien

Alle drei Muster profitieren von Temporals Kernstärken:

1. **Durability**: State wird automatisch persistiert
2. **Reliability**: Automatische Retries und Fehlerbehandlung
3. **Observability**: Vollständige Einsicht in Workflow-Ausführungen
4. **Scalability**: Workflows können über lange Zeiträume laufen

Im nächsten Kapitel werden wir uns mit Testing-Strategien für Temporal-Workflows beschäftigen, um sicherzustellen, dass diese Muster auch robust in Produktion laufen.
