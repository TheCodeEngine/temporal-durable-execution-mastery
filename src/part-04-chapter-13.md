# Kapitel 13: Best Practices und Anti-Muster

## Einleitung

Sie haben die Grundlagen von Temporal gelernt, Workflows geschrieben, Testing implementiert und Monitoring aufgesetzt. Ihr System läuft in Production. Doch dann kommt der Moment:

- Ein Workflow bricht plötzlich mit Non-Determinismus-Fehlern ab
- Die Event History überschreitet 50.000 Events und der Workflow wird terminiert
- Worker können die Last nicht bewältigen, obwohl genug Ressourcen verfügbar sind
- Ein vermeintlich kleines Refactoring führt zu Production-Incidents
- Code-Reviews dauern Stunden, weil niemand die Workflow-Struktur versteht

**Diese Probleme sind vermeidbar** – wenn Sie von Anfang an bewährte Patterns folgen und häufige Anti-Patterns vermeiden.

Dieses Kapitel destilliert Jahre an Production-Erfahrung aus der Temporal-Community in konkrete, umsetzbare Guidelines. Sie lernen **was funktioniert, was nicht funktioniert, und warum**.

### Das Grundproblem

**Scenario**: Ein Team entwickelt einen E-Commerce Workflow. Nach einigen Monaten in Production:

```python
# ❌ ANTI-PATTERN: Alles in einem gigantischen Workflow

@workflow.defn
class MonolithWorkflow:
    """Ein 3000-Zeilen Monster-Workflow"""

    def __init__(self):
        self.orders = []  # ❌ Unbegrenzte Liste
        self.user_sessions = {}  # ❌ Wächst endlos
        self.cache = {}  # ❌ Memory Leak

    @workflow.run
    async def run(self, user_id: str):
        # ❌ Non-deterministic!
        if random.random() > 0.5:
            discount = 0.1

        # ❌ Business Logic im Workflow
        price = self.calculate_complex_pricing(...)

        # ❌ Externe API direkt aufrufen
        async with httpx.AsyncClient() as client:
            response = await client.post("https://payment.api/charge")

        # ❌ Workflow läuft ewig ohne Continue-As-New
        while True:
            order = await workflow.wait_condition(lambda: len(self.orders) > 0)
            # Process order...
            # Event History wächst ins Unendliche

        # ❌ Map-Iteration (random order!)
        for session_id, session in self.user_sessions.items():
            await self.process_session(session)
```

**Konsequenzen nach 6 Monaten:**
```
❌ Event History: 75.000 Events → Workflow terminiert
❌ Non-Determinismus bei Replay → 30% der Workflows brechen ab
❌ Worker Overload → Schedule-To-Start > 10 Minuten
❌ Deployment dauert 6 Stunden → Rollback bei jedem Change
❌ Debugging unmöglich → Team ist frustriert
```

**Mit Best Practices:**
```python
# ✅ BEST PRACTICE: Clean, maintainable, production-ready

@dataclass
class OrderInput:
    """Single object input pattern"""
    user_id: str
    cart_items: List[str]
    discount_code: Optional[str] = None

@workflow.defn
class OrderWorkflow:
    """Focused workflow: Orchestrate, don't implement"""

    @workflow.run
    async def run(self, input: OrderInput) -> OrderResult:
        # ✅ Deterministic: All randomness in activities
        discount = await workflow.execute_activity(
            calculate_discount,
            input.discount_code,
            start_to_close_timeout=timedelta(seconds=30)
        )

        # ✅ Business logic in activities
        payment = await workflow.execute_activity(
            process_payment,
            PaymentInput(user_id=input.user_id, discount=discount),
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )

        # ✅ External calls in activities
        tracking = await workflow.execute_activity(
            create_shipment,
            payment.order_id,
            start_to_close_timeout=timedelta(hours=1)
        )

        return OrderResult(
            order_id=payment.order_id,
            tracking_number=tracking
        )
```

**Resultat:**
```
✓ Event History: ~20 Events pro Workflow
✓ 100% Replay Success Rate
✓ Schedule-To-Start: <100ms
✓ Zero-Downtime Deployments
✓ Debugging in Minuten statt Stunden
```

### Lernziele

Nach diesem Kapitel können Sie:

- **Best Practices** für Workflow-Design, Code-Organisation und Worker-Konfiguration anwenden
- **Anti-Patterns** erkennen und vermeiden, bevor sie Production-Probleme verursachen
- **Determinismus** garantieren durch korrektes Pattern-Anwendung
- **Performance** optimieren durch Worker-Tuning und Event History Management
- **Code-Organisation** strukturieren für Wartbarkeit und Skalierbarkeit
- **Production-Ready** Workflows schreiben, die jahrelang laufen
- **Code Reviews** durchführen mit klarer Checkliste
- **Refactorings** sicher vornehmen ohne Breaking Changes

---

## 13.1 Workflow Design Best Practices

### Orchestration vs. Implementation

**Regel**: Workflows orchestrieren, Activities implementieren.

```python
# ❌ ANTI-PATTERN: Business Logic im Workflow

@workflow.defn
class PricingWorkflowBad:
    @workflow.run
    async def run(self, product_id: str) -> float:
        # ❌ Complex logic in workflow (non-testable, non-deterministic risk)
        base_price = 100.0

        # ❌ Time-based logic (non-deterministic!)
        current_hour = datetime.now().hour
        if current_hour >= 18:
            base_price *= 1.2  # Evening surge pricing

        # ❌ Heavy computation
        for i in range(1000000):
            base_price += math.sin(i) * 0.0001

        return base_price
```

```python
# ✅ BEST PRACTICE: Orchestration only

@workflow.defn
class PricingWorkflowGood:
    @workflow.run
    async def run(self, product_id: str) -> float:
        # ✅ Delegate to activity
        price = await workflow.execute_activity(
            calculate_price,
            product_id,
            start_to_close_timeout=timedelta(seconds=30)
        )

        return price

# ✅ Logic in activity
@activity.defn
async def calculate_price(product_id: str) -> float:
    """Complex pricing logic isolated in activity"""
    base_price = await fetch_base_price(product_id)

    # Time-based logic OK in activity
    current_hour = datetime.now().hour
    if current_hour >= 18:
        base_price *= 1.2

    # Heavy computation OK in activity
    for i in range(1000000):
        base_price += math.sin(i) * 0.0001

    return base_price
```

**Warum?**
- ✅ Workflows bleiben deterministisch
- ✅ Activities sind unit-testbar
- ✅ Retry-Logik funktioniert korrekt
- ✅ Workflow History bleibt klein

---

### Single Object Input Pattern

**Regel**: Ein Input-Objekt statt mehrere Parameter.

```python
# ❌ ANTI-PATTERN: Multiple primitive arguments

@workflow.defn
class OrderWorkflowBad:
    @workflow.run
    async def run(
        self,
        user_id: str,
        product_id: str,
        quantity: int,
        discount: float,
        shipping_address: str,
        billing_address: str,
        gift_wrap: bool,
        express_shipping: bool
    ) -> str:
        # ❌ Signature-Änderungen brechen alte Workflows
        # ❌ Schwer zu lesen
        # ❌ Keine Validierung
        ...
```

```python
# ✅ BEST PRACTICE: Single dataclass input

from dataclasses import dataclass
from typing import Optional

@dataclass
class OrderInput:
    """Order workflow input (versioned)"""
    user_id: str
    product_id: str
    quantity: int
    shipping_address: str

    # Optional fields für Evolution
    discount: Optional[float] = None
    billing_address: Optional[str] = None
    gift_wrap: bool = False
    express_shipping: bool = False

    def __post_init__(self):
        # ✅ Validation at input
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")

@workflow.defn
class OrderWorkflowGood:
    @workflow.run
    async def run(self, input: OrderInput) -> OrderResult:
        # ✅ Neue Felder hinzufügen ist safe
        # ✅ Validierung ist gekapselt
        # ✅ Lesbar und wartbar
        ...
```

**Vorteile:**
- ✅ Einfacher zu erweitern (neue optionale Felder)
- ✅ Bessere Validierung
- ✅ Lesbarerer Code
- ✅ Type-Safety

---

### Continue-As-New für Long-Running Workflows

**Regel**: Verwenden Sie Continue-As-New, wenn Event History groß wird.

```python
# ❌ ANTI-PATTERN: Endlos-Workflow ohne Continue-As-New

@workflow.defn
class UserSessionWorkflowBad:
    def __init__(self):
        self.events = []  # ❌ Wächst unbegrenzt

    @workflow.run
    async def run(self, user_id: str):
        while True:  # ❌ Läuft ewig
            event = await workflow.wait_condition(
                lambda: len(self.pending_events) > 0
            )
            self.events.append(event)  # ❌ Event History explodiert

            # Nach 1 Jahr: 50.000+ Events
            # → Workflow wird terminiert!
```

```python
# ✅ BEST PRACTICE: Continue-As-New mit Limit

@workflow.defn
class UserSessionWorkflowGood:
    def __init__(self):
        self.events = []
        self.processed_count = 0

    @workflow.run
    async def run(self, user_id: str, total_processed: int = 0):
        while True:
            # ✅ Check history size regularly
            info = workflow.info()
            if info.get_current_history_length() > 1000:
                workflow.logger.info(
                    f"History size: {info.get_current_history_length()}, "
                    "continuing as new"
                )
                # ✅ Continue with fresh history
                workflow.continue_as_new(
                    user_id,
                    total_processed=total_processed + self.processed_count
                )

            event = await workflow.wait_condition(
                lambda: len(self.pending_events) > 0
            )

            await workflow.execute_activity(
                process_event,
                event,
                start_to_close_timeout=timedelta(seconds=30)
            )

            self.processed_count += 1
```

**Wann Continue-As-New verwenden:**
- Event History > 1.000 Events
- Workflow läuft > 1 Jahr
- State wächst unbegrenzt
- Workflow ist ein "Entity Workflow" (z.B. User Session, Shopping Cart)

**Limits:**
- ⚠️ Workflow terminiert automatisch bei **50.000 Events**
- ⚠️ Workflow terminiert bei **50 MB History Size**

---

## 13.2 Determinismus Best Practices

### Alles Non-Deterministische in Activities

**Regel**: Workflows müssen deterministisch sein. Alles andere → Activity.

```python
# ❌ ANTI-PATTERN: Non-deterministic workflow code

@workflow.defn
class FraudCheckWorkflowBad:
    @workflow.run
    async def run(self, transaction_id: str) -> bool:
        # ❌ random() ist non-deterministic!
        risk_score = random.random()

        # ❌ datetime.now() ist non-deterministic!
        if datetime.now().hour > 22:
            risk_score += 0.3

        # ❌ UUID generation non-deterministic!
        audit_id = str(uuid.uuid4())

        # ❌ Map iteration order non-deterministic!
        checks = {"ip": check_ip, "device": check_device}
        for check_name, check_fn in checks.items():  # ❌ Random order!
            await check_fn()

        return risk_score < 0.5
```

```python
# ✅ BEST PRACTICE: Deterministic workflow

@workflow.defn
class FraudCheckWorkflowGood:
    @workflow.run
    async def run(self, transaction_id: str) -> bool:
        # ✅ Random logic in activity
        risk_score = await workflow.execute_activity(
            calculate_risk_score,
            transaction_id,
            start_to_close_timeout=timedelta(seconds=30)
        )

        # ✅ Time-based logic in activity
        time_modifier = await workflow.execute_activity(
            get_time_based_modifier,
            start_to_close_timeout=timedelta(seconds=5)
        )

        # ✅ UUID generation in activity
        audit_id = await workflow.execute_activity(
            generate_audit_id,
            start_to_close_timeout=timedelta(seconds=5)
        )

        # ✅ Deterministic iteration order
        check_names = sorted(["ip", "device", "location"])  # ✅ Sorted!
        for check_name in check_names:
            result = await workflow.execute_activity(
                run_fraud_check,
                FraudCheckInput(transaction_id, check_name),
                start_to_close_timeout=timedelta(seconds=30)
            )

        return risk_score + time_modifier < 0.5

# ✅ Non-deterministic logic in activities
@activity.defn
async def calculate_risk_score(transaction_id: str) -> float:
    """Random logic OK in activity"""
    return random.random()

@activity.defn
async def get_time_based_modifier() -> float:
    """Time-based logic OK in activity"""
    if datetime.now().hour > 22:
        return 0.3
    return 0.0

@activity.defn
async def generate_audit_id() -> str:
    """UUID generation OK in activity"""
    return str(uuid.uuid4())
```

**Non-Deterministische Operationen:**
| Operation | Wo? | Warum? |
|-----------|-----|--------|
| `random.random()` | ❌ Workflow | Replay generiert anderen Wert |
| `datetime.now()` | ❌ Workflow | Replay hat andere Zeit |
| `uuid.uuid4()` | ❌ Workflow | Replay generiert andere UUID |
| `time.time()` | ❌ Workflow | Replay hat andere Timestamp |
| `dict.items()` iteration | ❌ Workflow | Order ist non-deterministic in Python <3.7 |
| `set` iteration | ❌ Workflow | Order ist non-deterministic |
| External API calls | ❌ Workflow | Response kann sich ändern |
| File I/O | ❌ Workflow | Datei-Inhalt kann sich ändern |
| Database queries | ❌ Workflow | Daten können sich ändern |

**✅ Alle diese Operationen sind OK in Activities!**

---

### Workflow-Code-Order nie ändern

**Regel**: Activity-Aufrufe dürfen nicht umgeordnet werden.

```python
# v1: Original Workflow
@workflow.defn
class OnboardingWorkflowV1:
    @workflow.run
    async def run(self, user_id: str):
        # Step 1: Validate
        await workflow.execute_activity(
            validate_user,
            user_id,
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Step 2: Create account
        await workflow.execute_activity(
            create_account,
            user_id,
            start_to_close_timeout=timedelta(seconds=30)
        )
```

```python
# ❌ v2-bad: Reihenfolge geändert (NON-DETERMINISTIC!)

@workflow.defn
class OnboardingWorkflowV2Bad:
    @workflow.run
    async def run(self, user_id: str):
        # ❌ FEHLER: Reihenfolge geändert!
        # Step 1: Create account (war vorher Step 2)
        await workflow.execute_activity(
            create_account,  # ❌ Replay erwartet validate_user!
            user_id,
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Step 2: Validate (war vorher Step 1)
        await workflow.execute_activity(
            validate_user,  # ❌ Replay erwartet create_account!
            user_id,
            start_to_close_timeout=timedelta(seconds=30)
        )
```

**Was passiert bei Replay:**
```
History Event: ActivityTaskScheduled(activity_name="validate_user")
Replayed Code: workflow.execute_activity(create_account, ...)

❌ ERROR: Non-deterministic workflow!
   Expected: validate_user
   Got: create_account
```

```python
# ✅ v2-good: Mit workflow.patched() ist Order-Änderung safe

@workflow.defn
class OnboardingWorkflowV2Good:
    @workflow.run
    async def run(self, user_id: str):
        if workflow.patched("reorder-validation-v2"):
            # ✅ NEW CODE PATH: Neue Reihenfolge
            await workflow.execute_activity(create_account, ...)
            await workflow.execute_activity(validate_user, ...)
        else:
            # ✅ OLD CODE PATH: Alte Reihenfolge für Replay
            await workflow.execute_activity(validate_user, ...)
            await workflow.execute_activity(create_account, ...)
```

---

## 13.3 State Management Best Practices

### Vermeiden Sie große Workflow-State

**Regel**: Workflow-State klein halten. Große Daten in Activities oder extern speichern.

```python
# ❌ ANTI-PATTERN: Große Daten im Workflow State

@workflow.defn
class DataProcessingWorkflowBad:
    def __init__(self):
        self.processed_records = []  # ❌ Wächst unbegrenzt!
        self.results = {}  # ❌ Kann riesig werden!

    @workflow.run
    async def run(self, dataset_id: str):
        # ❌ 1 Million Records in Memory
        records = await workflow.execute_activity(
            fetch_all_records,  # Returns 1M records
            dataset_id,
            start_to_close_timeout=timedelta(minutes=10)
        )

        for record in records:
            result = await workflow.execute_activity(
                process_record,
                record,
                start_to_close_timeout=timedelta(seconds=30)
            )
            self.processed_records.append(record)  # ❌ State explodiert!
            self.results[record.id] = result  # ❌ Speichert alles!

        # Event History: 50 MB+ → Workflow terminiert!
```

```python
# ✅ BEST PRACTICE: Minimaler State, externe Speicherung

@workflow.defn
class DataProcessingWorkflowGood:
    def __init__(self):
        self.processed_count = 0  # ✅ Nur Counter
        self.batch_id = None  # ✅ Nur ID

    @workflow.run
    async def run(self, dataset_id: str):
        # ✅ Activity gibt nur Batch-ID zurück (nicht die Daten!)
        self.batch_id = await workflow.execute_activity(
            create_processing_batch,
            dataset_id,
            start_to_close_timeout=timedelta(minutes=1)
        )

        # ✅ Activity returned nur Count
        total_records = await workflow.execute_activity(
            get_record_count,
            self.batch_id,
            start_to_close_timeout=timedelta(seconds=30)
        )

        # ✅ Process in batches
        batch_size = 1000
        for offset in range(0, total_records, batch_size):
            # ✅ Activity verarbeitet Batch und speichert extern
            processed = await workflow.execute_activity(
                process_batch,
                ProcessBatchInput(self.batch_id, offset, batch_size),
                start_to_close_timeout=timedelta(minutes=5)
            )

            self.processed_count += processed  # ✅ Nur Counter im State

        # ✅ Final result aus externer DB
        return await workflow.execute_activity(
            finalize_batch,
            self.batch_id,
            start_to_close_timeout=timedelta(minutes=1)
        )

# ✅ Activities speichern große Daten extern
@activity.defn
async def process_batch(input: ProcessBatchInput) -> int:
    """Process batch and store results in external DB"""
    records = fetch_records_from_db(input.batch_id, input.offset, input.limit)

    results = []
    for record in records:
        result = process_record(record)
        results.append(result)

    # ✅ Store in external database (S3, PostgreSQL, etc.)
    store_results_in_db(input.batch_id, results)

    return len(results)  # ✅ Return only count, not data
```

**Best Practices:**
- ✅ Speichern Sie IDs, nicht Daten
- ✅ Verwenden Sie Counters statt Listen
- ✅ Große Daten in Activities → S3, DB, Redis
- ✅ Workflow State < 1 KB ideal

---

### Query Handlers sind Read-Only

**Regel**: Queries dürfen niemals State mutieren.

```python
# ❌ ANTI-PATTERN: Query mutiert State

@workflow.defn
class OrderWorkflowBad:
    def __init__(self):
        self.status = "pending"
        self.view_count = 0

    @workflow.query
    def get_status(self) -> str:
        self.view_count += 1  # ❌ MUTATION in Query!
        return self.status  # ❌ Non-deterministic!
```

**Warum ist das schlimm?**
- Queries werden **nicht** in History gespeichert
- Bei Replay werden Queries **nicht** ausgeführt
- State ist nach Replay **anders** als vor Replay
- → **Non-Determinismus!**

```python
# ✅ BEST PRACTICE: Read-only Queries

@workflow.defn
class OrderWorkflowGood:
    def __init__(self):
        self.status = "pending"
        self.view_count = 0  # Tracked via Signal instead

    @workflow.query
    def get_status(self) -> str:
        """Read-only query"""
        return self.status  # ✅ No mutation

    @workflow.signal
    def track_view(self):
        """Use Signal for mutations"""
        self.view_count += 1  # ✅ Signal ist in History
```

---

## 13.4 Code-Organisation Best Practices

### Struktur: Workflows, Activities, Worker getrennt

**Regel**: Klare Trennung zwischen Workflows, Activities und Worker.

```
# ❌ ANTI-PATTERN: Alles in einer Datei

my_project/
  └── main.py  # 5000 Zeilen: Workflows, Activities, Worker, Client, alles!
```

```
# ✅ BEST PRACTICE: Modulare Struktur

my_project/
  ├── workflows/
  │   ├── __init__.py
  │   ├── order_workflow.py          # ✅ Ein Workflow pro File
  │   ├── payment_workflow.py
  │   └── shipping_workflow.py
  │
  ├── activities/
  │   ├── __init__.py
  │   ├── order_activities.py        # ✅ Activities grouped by domain
  │   ├── payment_activities.py
  │   ├── shipping_activities.py
  │   └── shared_activities.py       # ✅ Shared utilities
  │
  ├── models/
  │   ├── __init__.py
  │   ├── order_models.py            # ✅ Dataclasses für Inputs/Outputs
  │   └── payment_models.py
  │
  ├── workers/
  │   ├── __init__.py
  │   ├── order_worker.py            # ✅ Worker per domain
  │   └── payment_worker.py
  │
  ├── client/
  │   └── temporal_client.py         # ✅ Client-Setup
  │
  └── tests/
      ├── test_workflows/
      ├── test_activities/
      └── test_integration/
```

**Beispiel: Order Workflow strukturiert**

```python
# workflows/order_workflow.py
from models.order_models import OrderInput, OrderResult
from activities.order_activities import validate_order, process_payment

@workflow.defn
class OrderWorkflow:
    """Order processing workflow"""

    @workflow.run
    async def run(self, input: OrderInput) -> OrderResult:
        # Clean orchestration only
        ...

# activities/order_activities.py
@activity.defn
async def validate_order(input: OrderInput) -> bool:
    """Validate order data"""
    ...

@activity.defn
async def process_payment(order_id: str) -> PaymentResult:
    """Process payment"""
    ...

# models/order_models.py
@dataclass
class OrderInput:
    """Order workflow input"""
    order_id: str
    user_id: str
    items: List[OrderItem]

@dataclass
class OrderResult:
    """Order workflow result"""
    order_id: str
    status: str
    tracking_number: str

# workers/order_worker.py
async def main():
    """Order worker entrypoint"""
    client = await create_temporal_client()

    worker = Worker(
        client,
        task_queue="order-queue",
        workflows=[OrderWorkflow],
        activities=[validate_order, process_payment]
    )

    await worker.run()
```

**Vorteile:**
- ✅ Testbarkeit: Jede Komponente isoliert testbar
- ✅ Wartbarkeit: Klare Zuständigkeiten
- ✅ Code Reviews: Kleinere, fokussierte Files
- ✅ Onboarding: Neue Entwickler finden sich schnell zurecht

---

### Worker pro Domain/Use Case

**Regel**: Separate Workers für verschiedene Domains.

```python
# ❌ ANTI-PATTERN: Ein Monolith-Worker für alles

async def main():
    worker = Worker(
        client,
        task_queue="everything-queue",  # ❌ Alle Workflows auf einer Queue
        workflows=[
            OrderWorkflow,
            PaymentWorkflow,
            ShippingWorkflow,
            UserWorkflow,
            NotificationWorkflow,
            ReportWorkflow,
            # ... 50+ Workflows
        ],
        activities=[
            # ... 200+ Activities
        ]
    )
    # ❌ Probleme:
    # - Kann nicht unabhängig skaliert werden
    # - Deployment ist All-or-Nothing
    # - Ein Bug betrifft alle Workflows
```

```python
# ✅ BEST PRACTICE: Worker pro Domain

# workers/order_worker.py
async def run_order_worker():
    """Dedicated worker for order workflows"""
    client = await create_temporal_client()

    worker = Worker(
        client,
        task_queue="order-queue",  # ✅ Dedicated queue
        workflows=[OrderWorkflow],
        activities=[
            validate_order,
            process_payment,
            reserve_inventory,
            create_shipment
        ]
    )

    await worker.run()

# workers/notification_worker.py
async def run_notification_worker():
    """Dedicated worker for notifications"""
    client = await create_temporal_client()

    worker = Worker(
        client,
        task_queue="notification-queue",  # ✅ Dedicated queue
        workflows=[NotificationWorkflow],
        activities=[
            send_email,
            send_sms,
            send_push_notification
        ]
    )

    await worker.run()
```

**Deployment:**
```yaml
# kubernetes/order-worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-worker
spec:
  replicas: 5  # ✅ Skaliert unabhängig
  template:
    spec:
      containers:
      - name: order-worker
        image: myapp/order-worker:v2.3.0  # ✅ Unabhängige Versions

---
# kubernetes/notification-worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notification-worker
spec:
  replicas: 10  # ✅ Mehr Replicas für hohe Last
  template:
    spec:
      containers:
      - name: notification-worker
        image: myapp/notification-worker:v1.5.0  # ✅ Andere Version OK
```

**Vorteile:**
- ✅ Unabhängige Skalierung
- ✅ Unabhängige Deployments
- ✅ Blast Radius Isolation
- ✅ Team Autonomie

---

## 13.5 Worker Configuration Best Practices

### Immer mehr als ein Worker

**Regel**: Production braucht mindestens 2 Workers pro Queue.

```python
# ❌ ANTI-PATTERN: Single Worker in Production

# ❌ Single Point of Failure!
# Wenn dieser Worker crashed:
#   → Alle Tasks bleiben liegen
#   → Schedule-To-Start explodiert
#   → Workflows timeout

docker run my-worker:latest  # ❌ Nur 1 Instance
```

```python
# ✅ BEST PRACTICE: Multiple Workers für HA

# Kubernetes Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-worker
spec:
  replicas: 3  # ✅ Minimum 3 für High Availability
  template:
    spec:
      containers:
      - name: worker
        image: my-worker:latest
        env:
        - name: TEMPORAL_TASK_QUEUE
          value: "order-queue"

        # ✅ Resource Limits
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"

        # ✅ Health Checks
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10

        # ✅ Graceful Shutdown
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]
```

**Warum mehrere Workers?**
- ✅ High Availability: Worker-Crash betrifft nur Teil der Kapazität
- ✅ Rolling Updates: Zero-Downtime Deployments
- ✅ Load Balancing: Temporal verteilt automatisch
- ✅ Redundanz: Hardware-Failure resilient

---

### Worker Tuning

**Regel**: Tunen Sie Worker basierend auf Schedule-To-Start Metrics.

```python
# ❌ ANTI-PATTERN: Default Settings in Production

worker = Worker(
    client,
    task_queue="order-queue",
    workflows=[OrderWorkflow],
    activities=[process_payment, create_shipment]
    # ❌ Keine Tuning-Parameter
    # → Worker kann überlastet werden
    # → Oder underutilized sein
)
```

```python
# ✅ BEST PRACTICE: Getunter Worker

from temporalio.worker import Worker, WorkerConfig

worker = Worker(
    client,
    task_queue="order-queue",
    workflows=[OrderWorkflow],
    activities=[process_payment, create_shipment],

    # ✅ Max concurrent Workflow Tasks
    max_concurrent_workflow_tasks=100,  # Default: 100

    # ✅ Max concurrent Activity Tasks
    max_concurrent_activities=50,  # Default: 100

    # ✅ Max concurrent Local Activities
    max_concurrent_local_activities=200,  # Default: 200

    # ✅ Workflow Cache Size
    max_cached_workflows=500,  # Default: 600

    # ✅ Sticky Queue Schedule-To-Start Timeout
    sticky_queue_schedule_to_start_timeout=timedelta(seconds=5)
)
```

**Tuning Guidelines:**

| Metric | Wert | Aktion |
|--------|------|--------|
| **Schedule-To-Start** > 1s | Steigend | ❌ **Mehr Workers** oder **max_concurrent erhöhen** |
| **Schedule-To-Start** < 100ms | Konstant | ✅ Optimal |
| **Worker CPU** > 80% | Konstant | ❌ **Weniger Concurrency** oder **mehr Workers** |
| **Worker Memory** > 80% | Steigend | ❌ **max_cached_workflows reduzieren** |

**Monitoring-basiertes Tuning:**

```python
# workers/tuned_worker.py
import os

# ✅ Environment-based tuning
MAX_WORKFLOW_TASKS = int(os.getenv("MAX_WORKFLOW_TASKS", "100"))
MAX_ACTIVITIES = int(os.getenv("MAX_ACTIVITIES", "50"))

async def main():
    client = await create_temporal_client()

    worker = Worker(
        client,
        task_queue="order-queue",
        workflows=[OrderWorkflow],
        activities=[process_payment],
        max_concurrent_workflow_tasks=MAX_WORKFLOW_TASKS,
        max_concurrent_activities=MAX_ACTIVITIES
    )

    logging.info(
        f"Starting worker with "
        f"max_workflow_tasks={MAX_WORKFLOW_TASKS}, "
        f"max_activities={MAX_ACTIVITIES}"
    )

    await worker.run()
```

```bash
# Deployment mit tuning
kubectl set env deployment/order-worker \
  MAX_WORKFLOW_TASKS=200 \
  MAX_ACTIVITIES=100

# ✅ Live-Tuning ohne Code-Change!
```

---

## 13.6 Performance Best Practices

### Sandbox Performance Optimization

**Regel**: Pass deterministic modules through für bessere Performance.

```python
# ❌ ANTI-PATTERN: Langsamer Sandbox (alles wird gesandboxed)

from temporalio.worker import Worker

worker = Worker(
    client,
    task_queue="order-queue",
    workflows=[OrderWorkflow],
    activities=[process_payment]
    # ❌ Alle Module werden gesandboxed
    # → Pydantic Models sind sehr langsam
)
```

```python
# ✅ BEST PRACTICE: Optimierter Sandbox

from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner, SandboxRestrictions

# ✅ Pass-through für deterministische Module
passthrough_modules = [
    "pydantic",  # ✅ Pydantic ist deterministisch
    "dataclasses",  # ✅ Dataclasses sind deterministisch
    "models",  # ✅ Unsere eigenen Models
    "workflows.order_models",  # ✅ Order-spezifische Models
]

worker = Worker(
    client,
    task_queue="order-queue",
    workflows=[OrderWorkflow],
    activities=[process_payment],

    # ✅ Custom Sandbox Configuration
    workflow_runner=SandboxedWorkflowRunner(
        restrictions=SandboxRestrictions.default.with_passthrough_modules(
            *passthrough_modules
        )
    )
)

# ✅ Resultat: 5-10x schnellerer Workflow-Start!
```

---

### Event History Size Monitoring

**Regel**: Monitoren Sie History Size und reagieren Sie frühzeitig.

```python
# ✅ BEST PRACTICE: History Size Monitoring im Workflow

@workflow.defn
class LongRunningWorkflow:
    @workflow.run
    async def run(self, input: JobInput):
        processed = 0

        for item in input.items:
            # ✅ Regelmäßig History Size checken
            info = workflow.info()
            history_length = info.get_current_history_length()

            if history_length > 8000:  # ✅ Warning bei 8k (limit: 50k)
                workflow.logger.warning(
                    f"History size: {history_length} events, "
                    "approaching limit (50k). Consider Continue-As-New."
                )

            if history_length > 10000:  # ✅ Continue-As-New bei 10k
                workflow.logger.info(
                    f"History size: {history_length}, continuing as new"
                )
                workflow.continue_as_new(
                    JobInput(
                        items=input.items[processed:],
                        total_processed=input.total_processed + processed
                    )
                )

            result = await workflow.execute_activity(
                process_item,
                item,
                start_to_close_timeout=timedelta(seconds=30)
            )

            processed += 1
```

**Prometheus Metrics:**

```python
# workers/metrics.py
from prometheus_client import Histogram, Counter

workflow_history_size = Histogram(
    'temporal_workflow_history_size',
    'Workflow history event count',
    buckets=[10, 50, 100, 500, 1000, 5000, 10000, 50000]
)

continue_as_new_counter = Counter(
    'temporal_continue_as_new_total',
    'Continue-As-New executions'
)

# Im Workflow
workflow_history_size.observe(history_length)

if history_length > 10000:
    continue_as_new_counter.inc()
    workflow.continue_as_new(...)
```

---

## 13.7 Anti-Pattern Katalog

### 1. SDK Over-Wrapping

**Anti-Pattern**: Temporal SDK zu stark wrappen.

```python
# ❌ ANTI-PATTERN: Zu starkes Wrapping versteckt Features

class MyTemporalWrapper:
    """❌ Versteckt wichtige Temporal-Features"""

    def __init__(self, namespace: str):
        # ❌ Versteckt Client-Konfiguration
        self.client = Client.connect(namespace)

    async def run_workflow(self, name: str, data: dict):
        # ❌ Kein Zugriff auf:
        #   - Workflow ID customization
        #   - Retry Policies
        #   - Timeouts
        #   - Signals/Queries
        return await self.client.execute_workflow(name, data)

    # ❌ SDK-Updates sind schwierig
    # ❌ Team kennt Temporal nicht wirklich
    # ❌ Features wie Schedules, Updates nicht nutzbar
```

```python
# ✅ BEST PRACTICE: Dünner Helper, voller SDK-Zugriff

# helpers/temporal_helpers.py
async def create_temporal_client(
    namespace: str = "default"
) -> Client:
    """Thin helper for client creation"""
    return await Client.connect(
        f"localhost:7233",
        namespace=namespace,
        # ✅ Weitere Config durchreichbar
    )

# Application code: Voller SDK-Zugriff
async def main():
    client = await create_temporal_client()

    # ✅ Direkter SDK-Zugriff für alle Features
    handle = await client.start_workflow(
        OrderWorkflow.run,
        order_input,
        id=f"order-{order_id}",
        task_queue="order-queue",
        retry_policy=RetryPolicy(maximum_attempts=3),
        execution_timeout=timedelta(days=7)
    )

    # ✅ Signals
    await handle.signal(OrderWorkflow.approve)

    # ✅ Queries
    status = await handle.query(OrderWorkflow.get_status)
```

---

### 2. Local Activities ohne Idempotenz

**Anti-Pattern**: Local Activities verwenden ohne Idempotenz-Keys.

```python
# ❌ ANTI-PATTERN: Non-Idempotent Local Activity

@workflow.defn
class PaymentWorkflow:
    @workflow.run
    async def run(self, amount: float):
        # ❌ Local Activity (kann mehrfach ausgeführt werden!)
        await workflow.execute_local_activity(
            charge_credit_card,
            amount,
            start_to_close_timeout=timedelta(seconds=5)
        )
        # ❌ Bei Retry: Kunde wird doppelt belastet!

@activity.defn
async def charge_credit_card(amount: float):
    """❌ Nicht idempotent!"""
    # Charge without idempotency key
    await payment_api.charge(amount)  # ❌ Kann mehrfach passieren!
```

**Was passiert:**
```
1. Local Activity startet: charge_credit_card(100.0)
2. Payment API wird aufgerufen: $100 charged
3. Worker crashed vor Activity-Completion
4. Workflow replay: Local Activity wird NOCHMAL ausgeführt
5. Payment API wird NOCHMAL aufgerufen: $100 charged AGAIN
6. Kunde wurde $200 belastet statt $100!
```

```python
# ✅ BEST PRACTICE: Idempotente Local Activity ODER Regular Activity

# Option 1: Idempotent Local Activity
@activity.defn
async def charge_credit_card_idempotent(
    amount: float,
    idempotency_key: str  # ✅ Idempotency Key!
):
    """✅ Idempotent mit Key"""
    await payment_api.charge(
        amount,
        idempotency_key=idempotency_key  # ✅ API merkt Duplikate
    )

@workflow.defn
class PaymentWorkflow:
    @workflow.run
    async def run(self, payment_id: str, amount: float):
        # ✅ Unique Key basierend auf Workflow
        idempotency_key = f"{workflow.info().workflow_id}-payment"

        await workflow.execute_local_activity(
            charge_credit_card_idempotent,
            args=[amount, idempotency_key],
            start_to_close_timeout=timedelta(seconds=5)
        )

# Option 2: Regular Activity (recommended!)
@workflow.defn
class PaymentWorkflow:
    @workflow.run
    async def run(self, amount: float):
        # ✅ Regular Activity: Temporal garantiert at-most-once
        await workflow.execute_activity(
            charge_credit_card,
            amount,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
```

**Regel**: Verwenden Sie **Regular Activities** als Default. Local Activities nur für:
- Sehr schnelle Operationen (<1s)
- Read-Only Operationen
- Operations mit eingebauter Idempotenz

---

### 3. Workers Side-by-Side mit Application Code

**Anti-Pattern**: Workers im gleichen Process wie Application Code deployen.

```python
# ❌ ANTI-PATTERN: Worker + Web Server im gleichen Process

# main.py
from fastapi import FastAPI
from temporalio.worker import Worker

app = FastAPI()

@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Web API endpoint"""
    ...

async def main():
    # ❌ Worker und Web Server im gleichen Process!
    client = await create_temporal_client()

    # Start Worker (blocking!)
    worker = Worker(
        client,
        task_queue="order-queue",
        workflows=[OrderWorkflow],
        activities=[process_payment]
    )

    # ❌ Probleme:
    # - Worker blockiert Web Server (oder umgekehrt)
    # - Resource Contention (CPU/Memory)
    # - Deployment ist gekoppelt
    # - Scaling ist gekoppelt
    # - Ein Crash betrifft beides

    await worker.run()
```

```python
# ✅ BEST PRACTICE: Separate Processes

# web_server.py (separate deployment)
from fastapi import FastAPI

app = FastAPI()

@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Web API endpoint"""
    client = await create_temporal_client()
    handle = client.get_workflow_handle(order_id)
    status = await handle.query(OrderWorkflow.get_status)
    return {"status": status}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# worker.py (separate deployment)
from temporalio.worker import Worker

async def main():
    """Dedicated worker process"""
    client = await create_temporal_client()

    worker = Worker(
        client,
        task_queue="order-queue",
        workflows=[OrderWorkflow],
        activities=[process_payment]
    )

    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
```

**Separate Deployments:**

```yaml
# kubernetes/web-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-server
spec:
  replicas: 10  # ✅ Viele Replicas für Web Traffic
  template:
    spec:
      containers:
      - name: web
        image: myapp/web:latest
        command: ["python", "web_server.py"]
        resources:
          requests:
            cpu: "200m"  # ✅ Wenig CPU für Web
            memory: "256Mi"

---
# kubernetes/worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: temporal-worker
spec:
  replicas: 3  # ✅ Weniger Replicas, aber mehr Ressourcen
  template:
    spec:
      containers:
      - name: worker
        image: myapp/worker:latest
        command: ["python", "worker.py"]
        resources:
          requests:
            cpu: "1000m"  # ✅ Mehr CPU für Worker
            memory: "2Gi"  # ✅ Mehr Memory für Workflow Caching
```

---

## 13.8 Production Readiness Checklist

### Code-Ebene

```
✅ Workflows orchestrieren nur, implementieren nicht
✅ Single Object Input Pattern für alle Workflows
✅ Alle non-deterministic Operationen in Activities
✅ Continue-As-New für long-running Workflows
✅ History Size Monitoring implementiert
✅ Query Handlers sind read-only
✅ Replay Tests in CI/CD
✅ Comprehensive Unit Tests für Activities
✅ Integration Tests mit WorkflowEnvironment
```

### Deployment-Ebene

```
✅ Minimum 3 Worker Replicas pro Queue
✅ Workers separiert von Application Code
✅ Resource Limits definiert (CPU/Memory)
✅ Health Checks konfiguriert
✅ Graceful Shutdown implementiert
✅ Worker pro Domain/Use Case
✅ Worker Tuning basierend auf Metrics
✅ Rolling Update Strategy konfiguriert
```

### Monitoring-Ebene

```
✅ Schedule-To-Start Metrics
✅ Workflow Success/Failure Rate
✅ Activity Duration & Error Rate
✅ Event History Size Tracking
✅ Worker CPU/Memory Monitoring
✅ Continue-As-New Rate
✅ Alerts konfiguriert (PagerDuty/Slack)
```

### Testing-Ebene

```
✅ Replay Tests für jede Workflow-Version
✅ Unit Tests für jede Activity
✅ Integration Tests für Happy Path
✅ Integration Tests für Error Cases
✅ Production History Replay in CI
✅ Load Testing für Worker Capacity
✅ Chaos Engineering Tests (Worker Failures)
```

---

## 13.9 Code Review Checkliste

Verwenden Sie diese Checkliste bei Code Reviews:

### Workflow Code Review

```
✅ Workflow orchestriert nur (keine Business Logic)?
✅ Single Object Input statt multiple Parameters?
✅ Keine non-deterministic Operationen (random, datetime.now, etc.)?
✅ Keine Activity-Reihenfolge geändert ohne workflow.patched()?
✅ Continue-As-New für long-running Workflows?
✅ History Size Monitoring vorhanden?
✅ Workflow State klein (<1 KB)?
✅ Query Handlers sind read-only?
✅ Replay Tests hinzugefügt?
```

### Activity Code Review

```
✅ Activity ist idempotent?
✅ Activity hat Retry-Logic (oder RetryPolicy)?
✅ Activity hat Timeout definiert?
✅ Activity ist unit-testbar?
✅ Externe Calls haben Circuit Breaker?
✅ Activity loggt Errors mit Context?
✅ Activity gibt strukturiertes Result zurück (nicht primitives)?
```

### Worker Code Review

```
✅ Worker hat max_concurrent_* konfiguriert?
✅ Worker hat Health Check Endpoint?
✅ Worker hat Graceful Shutdown?
✅ Worker ist unabhängig deploybar?
✅ Worker hat Resource Limits?
✅ Worker hat Monitoring/Metrics?
```

---

## 13.10 Zusammenfassung

### Top 10 Best Practices

1. **Orchestration, nicht Implementation**: Workflows orchestrieren, Activities implementieren
2. **Single Object Input**: Ein Dataclass-Input statt viele Parameter
3. **Determinismus**: Alles Non-Deterministische in Activities
4. **Continue-As-New**: Bei >1.000 Events oder long-running Workflows
5. **Minimaler State**: IDs speichern, nicht Daten
6. **Code-Organisation**: Workflows, Activities, Workers getrennt
7. **Multiple Workers**: Minimum 3 Replicas in Production
8. **Worker Tuning**: Basierend auf Schedule-To-Start Metrics
9. **Replay Testing**: Jede Workflow-Änderung testen
10. **Monitoring**: Schedule-To-Start, Success Rate, History Size

### Top 10 Anti-Patterns

1. **Non-Determinismus**: `random()`, `datetime.now()`, `uuid.uuid4()` im Workflow
2. **Activity-Reihenfolge ändern**: Ohne `workflow.patched()`
3. **Große Event History**: >10.000 Events ohne Continue-As-New
4. **Großer Workflow State**: Listen/Dicts statt IDs
5. **Query Mutation**: State in Query Handler ändern
6. **SDK Over-Wrapping**: Temporal SDK zu stark abstrahieren
7. **Local Activities ohne Idempotenz**: Duplikate werden nicht verhindert
8. **Single Worker**: Kein Failover, kein Rolling Update
9. **Workers mit App Code**: Resource Contention, gekoppeltes Deployment
10. **Fehlende Tests**: Keine Replay Tests, keine Integration Tests

### Quick Reference: Was ist OK wo?

| Operation | Workflow | Activity | Warum |
|-----------|----------|----------|-------|
| `random.random()` | ❌ | ✅ | Non-deterministic |
| `datetime.now()` | ❌ | ✅ | Non-deterministic |
| `uuid.uuid4()` | ❌ | ✅ | Non-deterministic |
| External API Call | ❌ | ✅ | Non-deterministic |
| Database Query | ❌ | ✅ | Non-deterministic |
| File I/O | ❌ | ✅ | Non-deterministic |
| Heavy Computation | ❌ | ✅ | Should be retryable |
| `workflow.sleep()` | ✅ | ❌ | Deterministic timer |
| `workflow.execute_activity()` | ✅ | ❌ | Workflow orchestration |
| State Management | ✅ (minimal) | ❌ | Workflow owns state |
| Logging | ✅ | ✅ | Both OK |

### Nächste Schritte

Sie haben jetzt:
- ✅ **Best Practices** für Production-Ready Workflows
- ✅ **Anti-Patterns** Katalog zur Vermeidung häufiger Fehler
- ✅ **Code-Organisation** Patterns für Wartbarkeit
- ✅ **Worker-Tuning** Guidelines für Performance
- ✅ **Production Readiness** Checkliste

**In Teil V (Kochbuch)** werden wir konkrete Rezepte für häufige Use Cases sehen:
- E-Commerce Order Processing
- Payment Processing with Retries
- Long-Running Approval Workflows
- Scheduled Cleanup Jobs
- Fan-Out/Fan-In Patterns
- Saga Pattern Implementation

---

## Ressourcen

- [Temporal Best Practices Blog](https://temporal.io/blog/spooky-stories-chilling-temporal-anti-patterns-part-1)
- [Worker Performance Guide](https://docs.temporal.io/develop/worker-performance)
- [Safe Deployments](https://docs.temporal.io/develop/safe-deployments)
- [Python SDK Developer Guide](https://docs.temporal.io/develop/python)
