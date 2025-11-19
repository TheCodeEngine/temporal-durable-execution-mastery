# Kapitel 12: Testing Strategies

## Einleitung

Sie haben einen komplexen Workflow implementiert, der mehrere External Services orchestriert, komplizierte Retry-Logik hat und über Tage hinweg laufen kann. Alles funktioniert lokal. Sie deployen in Production – und plötzlich:

- Ein Edge Case bricht den Workflow
- Eine kürzlich geänderte Activity verhält sich anders als erwartet
- Ein Refactoring führt zu Non-Determinismus-Fehlern
- Ein Workflow, der Tage dauert, kann nicht schnell getestet werden

**Ohne Testing-Strategie** sind Sie:
- Unsicher bei jedem Deployment
- Abhängig von manuellen Tests in Production
- Blind gegenüber Breaking Changes
- Langsam beim Debugging

**Mit einer robusten Testing-Strategie** haben Sie:
- Vertrauen in Ihre Changes
- Schnelles Feedback (Sekunden statt Tage)
- Automatische Regression-Detection
- Sichere Workflow-Evolution

Temporal bietet leistungsstarke Testing-Tools, die speziell für durable, long-running Workflows entwickelt wurden. Dieses Kapitel zeigt Ihnen, wie Sie sie effektiv nutzen.

### Das Grundproblem

**Scenario**: Sie entwickeln einen Order Processing Workflow:

```python
@workflow.defn
class OrderWorkflow:
    async def run(self, order_id: str) -> str:
        # Payment (mit Retry-Logik)
        payment = await workflow.execute_activity(
            process_payment,
            order_id,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )

        # Inventory (kann lange dauern)
        await workflow.execute_activity(
            reserve_inventory,
            order_id,
            start_to_close_timeout=timedelta(hours=24)
        )

        # Warte auf manuelle Approval (via Signal)
        await workflow.wait_condition(lambda: self.approved)

        # Shipping
        tracking = await workflow.execute_activity(
            create_shipment,
            order_id,
            start_to_close_timeout=timedelta(hours=1)
        )

        return tracking
```

**Ohne Testing-Framework**:
```
❌ Test dauert 24+ Stunden (wegen inventory timeout)
❌ Manuelle Approval muss simuliert werden
❌ External Services müssen verfügbar sein
❌ Retry-Logik schwer zu testen
❌ Workflow-Evolution kann nicht validiert werden

→ Tests werden nicht geschrieben
→ Bugs landen in Production
→ Debugging dauert Stunden
```

**Mit Temporal Testing**:
```
✓ Test läuft in Sekunden (time-skipping)
✓ Activities werden gemockt
✓ Signals können simuliert werden
✓ Retry-Verhalten ist testbar
✓ Workflow History kann replayed werden

→ Comprehensive Test Suite
→ Bugs werden vor Deployment gefunden
→ Sichere Refactorings
```

### Lernziele

Nach diesem Kapitel können Sie:

- **Unit Tests** für Activities und Workflows schreiben
- **Integration Tests** mit `WorkflowEnvironment` implementieren
- **Time-Skipping** für Tests mit langen Timeouts nutzen
- **Activities mocken** für isolierte Workflow-Tests
- **Replay Tests** für Workflow-Evolution durchführen
- **pytest Fixtures** für Test-Isolation aufsetzen
- **CI/CD Integration** mit automatisierten Tests
- **Production Histories** in Tests verwenden

---

## 12.1 Unit Testing: Activities in Isolation

Der einfachste Test-Ansatz: **Activities direkt aufrufen**, ohne Worker oder Workflow.

### 12.1.1 Warum Activity Unit Tests?

**Vorteile**:
- ⚡ Schnell (keine Temporal-Infrastruktur nötig)
- 🎯 Fokussiert (nur Business-Logik)
- 🔄 Einfach zu debuggen
- 📊 Hohe Code Coverage

**Best Practice**: **80% Unit Tests, 15% Integration Tests, 5% E2E Tests**

### 12.1.2 Activity Unit Test Beispiel

```python
# activities.py
from temporalio import activity
from dataclasses import dataclass
import httpx

@dataclass
class PaymentRequest:
    order_id: str
    amount: float

@dataclass
class PaymentResult:
    success: bool
    transaction_id: str

@activity.defn
async def process_payment(request: PaymentRequest) -> PaymentResult:
    """Process payment via external API"""
    activity.logger.info(f"Processing payment for {request.order_id}")

    # Call external payment API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://payment.api.com/charge",
            json={
                "order_id": request.order_id,
                "amount": request.amount
            },
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()

    return PaymentResult(
        success=data["status"] == "success",
        transaction_id=data["transaction_id"]
    )
```

**Test (ohne Temporal)**:

```python
# tests/test_activities.py
import pytest
from unittest.mock import AsyncMock, patch
from activities import process_payment, PaymentRequest, PaymentResult

@pytest.mark.asyncio
async def test_process_payment_success():
    """Test successful payment processing"""

    # Mock httpx client
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "status": "success",
        "transaction_id": "txn_12345"
    }

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        # Call activity directly (no Temporal needed!)
        result = await process_payment(
            PaymentRequest(order_id="order-001", amount=99.99)
        )

        # Assert
        assert result.success is True
        assert result.transaction_id == "txn_12345"

@pytest.mark.asyncio
async def test_process_payment_failure():
    """Test payment processing failure"""

    with patch("httpx.AsyncClient") as mock_client:
        # Simulate API error
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Payment failed",
                request=AsyncMock(),
                response=AsyncMock(status_code=400)
            )
        )

        # Expect activity to raise
        with pytest.raises(httpx.HTTPStatusError):
            await process_payment(
                PaymentRequest(order_id="order-002", amount=199.99)
            )
```

**Vorteile**:
- ✅ Keine Temporal Server nötig
- ✅ Tests laufen in Millisekunden
- ✅ External API wird gemockt
- ✅ Error Cases sind testbar

---

## 12.2 Integration Testing mit WorkflowEnvironment

**Integration Tests** testen Workflows UND Activities zusammen, mit einem **in-memory Temporal Server**.

### 12.2.1 WorkflowEnvironment Setup

```python
# tests/test_workflows.py
import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from workflows import OrderWorkflow
from activities import process_payment, reserve_inventory, create_shipment

@pytest.fixture
async def workflow_env():
    """Fixture: Temporal test environment"""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        yield env

@pytest.fixture
async def worker(workflow_env):
    """Fixture: Worker mit Workflows und Activities"""
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[OrderWorkflow],
        activities=[process_payment, reserve_inventory, create_shipment]
    ):
        yield
```

**Wichtig**: `start_time_skipping()` aktiviert **automatisches Time-Skipping**!

### 12.2.2 Workflow Integration Test

```python
@pytest.mark.asyncio
async def test_order_workflow_success(workflow_env, worker):
    """Test successful order workflow execution"""

    # Start workflow
    handle = await workflow_env.client.start_workflow(
        OrderWorkflow.run,
        "order-test-001",
        id="test-order-001",
        task_queue="test-queue"
    )

    # Send approval signal (simulating manual step)
    await handle.signal(OrderWorkflow.approve)

    # Wait for result
    result = await handle.result()

    # Assert
    assert result.startswith("TRACKING-")
```

**Was passiert hier?**
1. `workflow_env` startet in-memory Temporal Server
2. `worker` registriert Workflows/Activities
3. Workflow wird gestartet
4. Signal wird gesendet (simuliert manuellen Schritt)
5. Ergebnis wird validiert

**Time-Skipping**: 24-Stunden Timeout dauert nur Sekunden!

---

## 12.3 Time-Skipping: Tage in Sekunden testen

### 12.3.1 Das Problem: Lange Timeouts

```python
@workflow.defn
class NotificationWorkflow:
    async def run(self, user_id: str):
        # Send initial notification
        await workflow.execute_activity(
            send_email,
            user_id,
            start_to_close_timeout=timedelta(minutes=5)
        )

        # Wait 3 days
        await asyncio.sleep(timedelta(days=3).total_seconds())

        # Send reminder
        await workflow.execute_activity(
            send_reminder,
            user_id,
            start_to_close_timeout=timedelta(minutes=5)
        )
```

**Ohne Time-Skipping**: Test dauert 3 Tage 😱

**Mit Time-Skipping**: Test dauert Sekunden ⚡

### 12.3.2 Time-Skipping in Action

```python
@pytest.mark.asyncio
async def test_notification_workflow_with_delay(workflow_env, worker):
    """Test workflow with 3-day sleep (executes in seconds!)"""

    # Start workflow
    handle = await workflow_env.client.start_workflow(
        NotificationWorkflow.run,
        "user-123",
        id="test-notification",
        task_queue="test-queue"
    )

    # Wait for completion (time is automatically skipped!)
    await handle.result()

    # Verify both activities were called
    history = await handle.fetch_history()
    activity_events = [
        e for e in history.events
        if e.event_type == "ACTIVITY_TASK_SCHEDULED"
    ]
    assert len(activity_events) == 2  # send_email + send_reminder
```

**Wie funktioniert Time-Skipping?**

- **WorkflowEnvironment** erkennt, dass keine Activities laufen
- Zeit wird **automatisch vorwärts gespult** bis zum nächsten Event
- `asyncio.sleep(3 days)` wird **instant** übersprungen
- Test läuft in **<1 Sekunde**

### 12.3.3 Manuelles Time-Skipping

```python
@pytest.mark.asyncio
async def test_manual_time_skip(workflow_env):
    """Manually control time skipping"""

    # Start workflow
    handle = await workflow_env.client.start_workflow(
        NotificationWorkflow.run,
        "user-456",
        id="test-manual-skip",
        task_queue="test-queue"
    )

    # Manually skip time
    await workflow_env.sleep(timedelta(days=3))

    # Check workflow state via query
    state = await handle.query("get_state")
    assert state == "reminder_sent"
```

---

## 12.4 Mocking Activities

**Problem**: Activities rufen externe Services auf (Datenbanken, APIs, etc.). Im Test wollen wir diese **nicht** aufrufen.

### 12.4.1 Activity Mocking mit Mock-Implementierung

```python
# activities.py (production code)
@activity.defn
async def send_email(user_id: str, subject: str, body: str):
    """Send email via SendGrid"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            json={
                "to": f"user-{user_id}@example.com",
                "subject": subject,
                "body": body
            },
            headers={"Authorization": f"Bearer {SENDGRID_API_KEY}"}
        )
        response.raise_for_status()

# tests/mocks.py (test code)
@activity.defn(name="send_email")  # Same name as production activity!
async def mock_send_email(user_id: str, subject: str, body: str):
    """Mock email sending (no external call)"""
    activity.logger.info(f"MOCK: Sending email to user {user_id}")
    # No actual API call - just return success
    return None
```

**Test mit Mock**:

```python
from tests.mocks import mock_send_email

@pytest.mark.asyncio
async def test_with_mock_activity(workflow_env):
    """Test workflow with mocked activity"""

    # Worker uses MOCK activity instead of production one
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[NotificationWorkflow],
        activities=[mock_send_email]  # Mock statt Production!
    ):
        handle = await workflow_env.client.start_workflow(
            NotificationWorkflow.run,
            "user-789",
            id="test-with-mock",
            task_queue="test-queue"
        )

        await handle.result()

        # Verify workflow completed without calling SendGrid
```

**Vorteile**:
- ✅ Keine external dependencies
- ✅ Tests laufen offline
- ✅ Schneller (keine Network Latency)
- ✅ Deterministisch (keine Flakiness)

### 12.4.2 Conditional Mocking (Production vs Test)

```python
# config.py
import os

IS_TEST = os.getenv("TESTING", "false") == "true"

# activities.py
@activity.defn
async def send_email(user_id: str, subject: str, body: str):
    if IS_TEST:
        activity.logger.info(f"TEST MODE: Would send email to {user_id}")
        return

    # Production code
    async with httpx.AsyncClient() as client:
        # ... real API call
        pass
```

**Nachteile dieses Ansatzes**:
- ⚠️ Vermischt Production und Test-Code
- ⚠️ Schwieriger zu maintainen
- ✅ **Besser**: Separate Mock-Implementierungen (siehe oben)

---

## 12.5 Replay Testing: Workflow-Evolution validieren

**Replay Testing** ist Temporals **Killer-Feature** für sichere Workflow-Evolution.

### 12.5.1 Was ist Replay Testing?

**Konzept**:
1. Workflow wird ausgeführt → **History** wird aufgezeichnet
2. Workflow-Code wird geändert
3. **Replay**: Alte History wird mit neuem Code replayed
4. **Validierung**: Prüfen, ob neuer Code deterministisch ist

**Use Case**: Sie deployen eine neue Workflow-Version. Replay Testing stellt sicher, dass alte, noch laufende Workflows **nicht brechen**.

### 12.5.2 Replay Test Setup

```python
# tests/test_replay.py
from temporalio.worker import Replayer
from temporalio.client import WorkflowHistory
from workflows import OrderWorkflowV1, OrderWorkflowV2

@pytest.mark.asyncio
async def test_workflow_v2_replays_v1_history():
    """Test that v2 workflow can replay v1 history"""

    # 1. Execute v1 workflow and capture history
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[OrderWorkflowV1],
            activities=[process_payment]
        ):
            handle = await env.client.start_workflow(
                OrderWorkflowV1.run,
                "order-replay-test",
                id="replay-test",
                task_queue="test-queue"
            )

            await handle.result()

            # Capture workflow history
            history = await handle.fetch_history()

    # 2. Create Replayer with v2 workflow
    replayer = Replayer(
        workflows=[OrderWorkflowV2],
        activities=[process_payment]
    )

    # 3. Replay v1 history with v2 code
    try:
        await replayer.replay_workflow(history)
        print("✅ Replay successful - v2 is compatible!")
    except Exception as e:
        pytest.fail(f"❌ Replay failed - non-determinism detected: {e}")
```

### 12.5.3 Breaking Change Detection

**Scenario**: Sie ändern Activity-Reihenfolge (Breaking Change!)

```python
# workflows.py (v1)
@workflow.defn
class OrderWorkflowV1:
    async def run(self, order_id: str):
        payment = await workflow.execute_activity(process_payment, ...)
        inventory = await workflow.execute_activity(reserve_inventory, ...)
        return "done"

# workflows.py (v2 - BREAKING!)
@workflow.defn
class OrderWorkflowV2:
    async def run(self, order_id: str):
        # WRONG: Changed order!
        inventory = await workflow.execute_activity(reserve_inventory, ...)
        payment = await workflow.execute_activity(process_payment, ...)
        return "done"
```

**Replay Test fängt das ab**:

```
❌ Replay failed - non-determinism detected:
Expected ActivityScheduled(process_payment)
Got ActivityScheduled(reserve_inventory)
```

**Lösung**: Verwende `workflow.patched()` (siehe Kapitel 8)

```python
@workflow.defn
class OrderWorkflowV2Fixed:
    async def run(self, order_id: str):
        if workflow.patched("swap-order-v2"):
            # New order
            inventory = await workflow.execute_activity(reserve_inventory, ...)
            payment = await workflow.execute_activity(process_payment, ...)
        else:
            # Old order (for replay)
            payment = await workflow.execute_activity(process_payment, ...)
            inventory = await workflow.execute_activity(reserve_inventory, ...)

        return "done"
```

### 12.5.4 Production History Replay

**Best Practice**: Replay **echte Production Histories** in CI/CD!

```python
# tests/test_production_replay.py
import json
from pathlib import Path

@pytest.mark.asyncio
async def test_replay_production_histories():
    """Replay 100 most recent production histories"""

    # Load histories from exported JSON files
    history_dir = Path("tests/fixtures/production_histories")

    replayer = Replayer(
        workflows=[OrderWorkflowV2],
        activities=[process_payment, reserve_inventory, create_shipment]
    )

    for history_file in history_dir.glob("*.json"):
        with open(history_file) as f:
            history_data = json.load(f)

        workflow_id = history_file.stem
        history = WorkflowHistory.from_json(workflow_id, history_data)

        try:
            await replayer.replay_workflow(history)
            print(f"✅ {workflow_id} replayed successfully")
        except Exception as e:
            pytest.fail(f"❌ {workflow_id} failed: {e}")
```

**Workflow Histories exportieren**:

```bash
# Export history for a workflow
temporal workflow show \
  --workflow-id order-12345 \
  --output json > tests/fixtures/production_histories/order-12345.json

# Batch export (last 100 workflows)
temporal workflow list \
  --query 'WorkflowType="OrderWorkflow"' \
  --limit 100 \
  --fields WorkflowId \
  | xargs -I {} temporal workflow show --workflow-id {} --output json > {}.json
```

---

## 12.6 pytest Fixtures für Test-Isolation

**Problem**: Tests beeinflussen sich gegenseitig, wenn sie Workflows mit denselben IDs starten.

**Lösung**: pytest Fixtures + eindeutige Workflow IDs

### 12.6.1 Wiederverwendbare Fixtures

```python
# tests/conftest.py (shared fixtures)
import pytest
import uuid
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from workflows import OrderWorkflow
from activities import process_payment, reserve_inventory

@pytest.fixture
async def temporal_env():
    """Fixture: Temporal test environment (time-skipping)"""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        yield env

@pytest.fixture
async def worker(temporal_env):
    """Fixture: Worker with all workflows/activities"""
    async with Worker(
        temporal_env.client,
        task_queue="test-queue",
        workflows=[OrderWorkflow],
        activities=[process_payment, reserve_inventory]
    ):
        yield

@pytest.fixture
def unique_workflow_id():
    """Fixture: Generate unique workflow ID for each test"""
    return f"test-{uuid.uuid4()}"
```

### 12.6.2 Test Isolation

```python
# tests/test_order_workflow.py
import pytest

@pytest.mark.asyncio
async def test_order_success(temporal_env, worker, unique_workflow_id):
    """Test successful order (isolated via unique ID)"""

    handle = await temporal_env.client.start_workflow(
        OrderWorkflow.run,
        "order-001",
        id=unique_workflow_id,  # Unique ID!
        task_queue="test-queue"
    )

    result = await handle.result()
    assert result == "ORDER_COMPLETED"

@pytest.mark.asyncio
async def test_order_payment_failure(temporal_env, worker, unique_workflow_id):
    """Test order with payment failure (isolated)"""

    handle = await temporal_env.client.start_workflow(
        OrderWorkflow.run,
        "order-002",
        id=unique_workflow_id,  # Different unique ID!
        task_queue="test-queue"
    )

    # Expect workflow to fail
    with pytest.raises(Exception, match="Payment failed"):
        await handle.result()
```

**Vorteile**:
- ✅ Keine Test-Interferenz
- ✅ Tests können parallel laufen
- ✅ Deterministisch (kein Flakiness)

### 12.6.3 Parametrisierte Tests

```python
@pytest.mark.parametrize("order_id,expected_status", [
    ("order-001", "COMPLETED"),
    ("order-002", "PAYMENT_FAILED"),
    ("order-003", "INVENTORY_UNAVAILABLE"),
])
@pytest.mark.asyncio
async def test_order_scenarios(
    temporal_env,
    worker,
    unique_workflow_id,
    order_id,
    expected_status
):
    """Test multiple order scenarios"""

    handle = await temporal_env.client.start_workflow(
        OrderWorkflow.run,
        order_id,
        id=unique_workflow_id,
        task_queue="test-queue"
    )

    result = await handle.result()
    assert result["status"] == expected_status
```

---

## 12.7 CI/CD Integration

### 12.7.1 pytest in CI/CD Pipeline

**GitHub Actions Beispiel**:

```yaml
# .github/workflows/test.yml
name: Temporal Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio

      - name: Run unit tests
        run: pytest tests/test_activities.py -v

      - name: Run integration tests
        run: pytest tests/test_workflows.py -v

      - name: Run replay tests
        run: pytest tests/test_replay.py -v

      - name: Generate coverage report
        run: |
          pip install pytest-cov
          pytest --cov=workflows --cov=activities --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### 12.7.2 Test-Organisation

```
tests/
├── conftest.py              # Shared fixtures
├── test_activities.py       # Unit tests (fast)
├── test_workflows.py        # Integration tests (slower)
├── test_replay.py           # Replay tests (critical)
├── fixtures/
│   └── production_histories/  # Exported workflow histories
│       ├── order-12345.json
│       └── order-67890.json
└── mocks/
    └── mock_activities.py   # Mock implementations
```

**pytest Marker für Test-Kategorien**:

```python
# tests/test_workflows.py
import pytest

@pytest.mark.unit
@pytest.mark.asyncio
async def test_activity_directly():
    """Fast unit test"""
    result = await process_payment(...)
    assert result.success

@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow_with_worker(temporal_env, worker):
    """Slower integration test"""
    handle = await temporal_env.client.start_workflow(...)
    await handle.result()

@pytest.mark.replay
@pytest.mark.asyncio
async def test_replay_production_history():
    """Critical replay test"""
    replayer = Replayer(...)
    await replayer.replay_workflow(history)
```

**Selektives Ausführen**:

```bash
# Nur Unit Tests (schnell)
pytest -m unit

# Nur Integration Tests
pytest -m integration

# Nur Replay Tests (vor Deployment!)
pytest -m replay

# Alle Tests
pytest
```

### 12.7.3 Pre-Commit Hook für Replay Tests

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "Running replay tests before commit..."
pytest tests/test_replay.py -v

if [ $? -ne 0 ]; then
    echo "❌ Replay tests failed! Commit blocked."
    exit 1
fi

echo "✅ Replay tests passed!"
```

---

## 12.8 Advanced: Testing mit echten Temporal Server

**Use Case**: End-to-End Tests mit realem Temporal Server (nicht in-memory).

### 12.8.1 Temporal Dev Server in CI

```yaml
# .github/workflows/e2e.yml
jobs:
  e2e-test:
    runs-on: ubuntu-latest

    services:
      temporal:
        image: temporalio/auto-setup:latest
        ports:
          - 7233:7233
        env:
          TEMPORAL_ADDRESS: localhost:7233

    steps:
      - uses: actions/checkout@v3

      - name: Wait for Temporal
        run: |
          timeout 60 bash -c 'until nc -z localhost 7233; do sleep 1; done'

      - name: Run E2E tests
        run: pytest tests/e2e/ -v
        env:
          TEMPORAL_ADDRESS: localhost:7233
```

### 12.8.2 E2E Test mit realem Server

```python
# tests/e2e/test_order_e2e.py
import pytest
from temporalio.client import Client
from temporalio.worker import Worker

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_order_workflow_e2e():
    """E2E test with real Temporal server"""

    # Connect to real Temporal server
    client = await Client.connect("localhost:7233")

    # Start real worker
    async with Worker(
        client,
        task_queue="e2e-queue",
        workflows=[OrderWorkflow],
        activities=[process_payment, reserve_inventory]
    ):
        # Execute workflow
        handle = await client.start_workflow(
            OrderWorkflow.run,
            "order-e2e-001",
            id="e2e-test-001",
            task_queue="e2e-queue"
        )

        result = await handle.result()
        assert result == "ORDER_COMPLETED"

        # Verify via Temporal UI (optional)
        history = await handle.fetch_history()
        assert len(history.events) > 0
```

---

## 12.9 Testing Best Practices

### 12.9.1 Test-Pyramide für Temporal

```
         /\
        /  \  E2E Tests (5%)
       /____\  - Real Temporal Server
      /      \  - All services integrated
     /________\ Integration Tests (15%)
    /          \ - WorkflowEnvironment
   /____________\ - Time-skipping
  /              \ - Mocked activities
 /________________\ Unit Tests (80%)
                   - Direct activity calls
                   - Fast, isolated
```

### 12.9.2 Checkliste: Was testen?

**Workflows**:
- ✅ Happy Path (erfolgreiches Durchlaufen)
- ✅ Error Cases (Activity Failures, Timeouts)
- ✅ Signal Handling (korrekte Reaktion auf Signals)
- ✅ Query Responses (richtige State-Rückgabe)
- ✅ Retry Behavior (Retries funktionieren wie erwartet)
- ✅ Long-running Scenarios (mit Time-Skipping)
- ✅ Replay Compatibility (nach Code-Änderungen)

**Activities**:
- ✅ Business Logic (korrekte Berechnung/Verarbeitung)
- ✅ Error Handling (Exceptions werden richtig geworfen)
- ✅ Edge Cases (null, empty, extreme values)
- ✅ External API Mocking (keine echten Calls im Test)

**Workflow Evolution**:
- ✅ Replay Tests (alte Histories mit neuem Code)
- ✅ Patching Scenarios (workflow.patched() funktioniert)
- ✅ Breaking Change Detection (Non-Determinismus)

### 12.9.3 Common Testing Mistakes

| Fehler | Problem | Lösung |
|--------|---------|--------|
| **Keine Replay Tests** | Breaking Changes in Production | Replay Tests in CI/CD |
| **Tests dauern zu lang** | Keine Time-Skipping-Nutzung | `start_time_skipping()` |
| **Flaky Tests** | Shared Workflow IDs | Unique IDs pro Test |
| **Nur Happy Path** | Bugs in Error Cases | Edge Cases testen |
| **External Calls im Test** | Langsam, flaky, Kosten | Activities mocken |
| **Keine Production History** | Ungetestete Edge Cases | Production Histories exportieren |

### 12.9.4 Performance-Optimierung

```python
# SLOW: Neues Environment pro Test
@pytest.mark.asyncio
async def test_workflow_1():
    async with await WorkflowEnvironment.start_time_skipping() as env:
        # Test...
        pass

@pytest.mark.asyncio
async def test_workflow_2():
    async with await WorkflowEnvironment.start_time_skipping() as env:
        # Test...
        pass

# FAST: Shared environment via fixture (session scope)
@pytest.fixture(scope="session")
async def shared_env():
    async with await WorkflowEnvironment.start_time_skipping() as env:
        yield env

@pytest.mark.asyncio
async def test_workflow_1(shared_env):
    # Test... (uses same environment)
    pass

@pytest.mark.asyncio
async def test_workflow_2(shared_env):
    # Test... (uses same environment)
    pass
```

**Speedup**: 10x schneller bei vielen Tests!

---

## 12.10 Zusammenfassung

### Testing Strategy Checklist

**Development**:
- [ ] Unit Tests für alle Activities
- [ ] Integration Tests für kritische Workflows
- [ ] Replay Tests für Workflow-Versionen
- [ ] Mocks für externe Services
- [ ] Time-Skipping für lange Workflows

**CI/CD**:
- [ ] pytest in GitHub Actions / GitLab CI
- [ ] Replay Tests vor jedem Deployment
- [ ] Production History Replay (wöchentlich)
- [ ] Test Coverage Tracking (>80%)
- [ ] Pre-Commit Hooks für Replay Tests

**Production**:
- [ ] Workflow Histories regelmäßig exportieren
- [ ] Replay Tests mit Production Histories
- [ ] Monitoring für Test-Failures in CI
- [ ] Rollback-Plan bei Breaking Changes

### Häufige Fehler

❌ **FEHLER 1: Keine Replay Tests**
```python
# Deployment ohne Replay Testing
# → Breaking Changes landen in Production
```

✅ **RICHTIG**:
```python
@pytest.mark.asyncio
async def test_replay_before_deploy():
    replayer = Replayer(workflows=[WorkflowV2])
    await replayer.replay_workflow(production_history)
```

❌ **FEHLER 2: Tests dauern ewig**
```python
# Warten auf echte Timeouts
await asyncio.sleep(3600)  # 1 Stunde
```

✅ **RICHTIG**:
```python
# Time-Skipping nutzen
async with await WorkflowEnvironment.start_time_skipping() as env:
    # 1 Stunde wird instant übersprungen
```

❌ **FEHLER 3: Flaky Tests**
```python
# Feste Workflow ID
id="test-workflow"  # Mehrere Tests kollidieren!
```

✅ **RICHTIG**:
```python
# Unique ID pro Test
id=f"test-{uuid.uuid4()}"
```

### Best Practices

1. **80/15/5 Regel**: 80% Unit, 15% Integration, 5% E2E
2. **Time-Skipping immer nutzen** für Integration Tests
3. **Replay Tests in CI/CD** vor jedem Deployment
4. **Production Histories regelmäßig exportieren** und testen
5. **Activities mocken** für schnelle, deterministische Tests
6. **Unique Workflow IDs** für Test-Isolation
7. **pytest Fixtures** für Wiederverwendbarkeit
8. **Test-Marker** für selektives Ausführen

### Testing Anti-Patterns

| Anti-Pattern | Warum schlecht? | Alternative |
|--------------|-----------------|-------------|
| Nur manuelle Tests | Langsam, fehleranfällig | Automatisierte pytest Suite |
| Keine Mocks | Tests brauchen externe Services | Mock Activities |
| Feste Workflow IDs | Tests beeinflussen sich | Unique IDs via uuid |
| Warten auf echte Zeit | Tests dauern Stunden/Tage | Time-Skipping |
| Kein Replay Testing | Breaking Changes unentdeckt | Replay in CI/CD |
| Nur Happy Path | Bugs in Edge Cases | Error Cases testen |

### Nächste Schritte

Nach diesem Kapitel sollten Sie:

1. **Test Suite aufsetzen**:
   ```bash
   mkdir tests
   touch tests/conftest.py tests/test_activities.py tests/test_workflows.py
   ```

2. **pytest konfigurieren**:
   ```ini
   # pytest.ini
   [pytest]
   asyncio_mode = auto
   markers =
       unit: Unit tests
       integration: Integration tests
       replay: Replay tests
   ```

3. **CI/CD Pipeline erweitern**:
   ```yaml
   # .github/workflows/test.yml
   - name: Run tests
     run: pytest -v --cov
   ```

4. **Production History Export automatisieren**:
   ```bash
   # Wöchentlicher Cron Job
   temporal workflow list --limit 100 | xargs -I {} temporal workflow show ...
   ```

### Ressourcen

- [Temporal Testing Docs (Python)](https://docs.temporal.io/develop/python/testing-suite)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [Replay Testing Guide](https://docs.temporal.io/dev-guide/python/testing#replay-testing)
- [WorkflowEnvironment API](https://python.temporal.io/temporalio.testing.WorkflowEnvironment.html)

---

**[⬆ Zurück zum Inhaltsverzeichnis](README.md)**

**Nächstes Kapitel**: [Kapitel 13: Best Practices und Anti-Muster](part-04-chapter-13.md)

**Code-Beispiele für dieses Kapitel**: [`examples/part-04/chapter-12/`](../examples/part-04/chapter-12/)
