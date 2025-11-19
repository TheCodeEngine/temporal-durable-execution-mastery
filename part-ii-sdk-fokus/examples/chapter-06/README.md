# Kapitel 6 Beispiele: Kommunikation mit Workflows

Praktische Code-Beispiele für Temporal Signals, Queries und Updates.

## Beispiele

### 1. signal_example.py
**Demonstriert**: Asynchrone Signal-basierte Kommunikation

Features:
- Signal Handler mit `@workflow.signal`
- Wait Conditions für Signal-basierte Koordination
- Timeouts für Human-in-the-Loop Patterns
- Approval/Rejection Workflows

```bash
python signal_example.py
```

**Was Sie lernen:**
- Signal Handler definieren und verwenden
- `workflow.wait_condition()` für Signal-basierte Koordination
- Fire-and-forget Semantik von Signalen
- Timeout-Handling mit `asyncio.TimeoutError`

---

### 2. query_example.py
**Demonstriert**: Read-only Queries für State Inspection

Features:
- Query Handler mit `@workflow.query`
- Progress Tracking und Monitoring
- Queries auf abgeschlossenen Workflows
- Detaillierte Progress-Objekte

```bash
python query_example.py
```

**Was Sie lernen:**
- Query Handler definieren (synchron!)
- Progress Monitoring mit Queries
- Query auf completed Workflows (innerhalb Retention)
- Berechnete Query-Werte

---

### 3. update_example.py
**Demonstriert**: Updates mit Validierung

Features:
- Update Handler mit `@workflow.update`
- Validator-Funktionen mit `@handler.validator`
- Synchrone Responses mit Fehler-Feedback
- Activity-Ausführung in Updates
- Concurrency-Schutz mit `asyncio.Lock`

```bash
python update_example.py
```

**Was Sie lernen:**
- Update Handler mit Validierung
- Frühe Ablehnung ungültiger Inputs (Validator)
- Synchrone Error-Propagierung
- Validator vs Handler Exceptions
- Thread-Safety bei async Handlern

---

### 4. combined_example.py
**Demonstriert**: Alle drei Mechanismen zusammen

Features:
- E-Commerce Order Workflow
- Updates für Item-Verwaltung und Payment
- Queries für Status und Progress
- Signals für Shipment und Cancellation
- Complete Order Lifecycle

```bash
python combined_example.py
```

**Was Sie lernen:**
- Kombination von Signals, Queries und Updates
- Wann welcher Mechanismus zu verwenden ist
- State Management über verschiedene Handler
- Production-Ready Patterns

---

## Voraussetzungen

Alle Beispiele benötigen:

1. **Temporal Server** (lokal laufend):
   ```bash
   temporal server start-dev
   ```

2. **Worker** (in separatem Terminal):
   ```bash
   python worker.py
   ```

3. **Python Dependencies**:
   ```bash
   uv sync
   ```

## Quick Reference

### Signal
```python
@workflow.signal
def approve(self, decision: ApprovalInput) -> None:
    self.approved = decision.approved

# Client
await handle.signal(MyWorkflow.approve, decision)
```

### Query
```python
@workflow.query
def get_status(self) -> str:
    return self.status

# Client
status = await handle.query(MyWorkflow.get_status)
```

### Update
```python
@workflow.update
async def add_item(self, item: Item) -> dict:
    self.items.append(item)
    return {"count": len(self.items)}

@add_item.validator
def validate_add_item(self, item: Item) -> None:
    if not item.valid:
        raise ValueError("Invalid item")

# Client
result = await handle.execute_update(MyWorkflow.add_item, item)
```

## Wichtige Konzepte

### Signal vs Query vs Update

| Feature | Signal | Query | Update |
|---------|--------|-------|--------|
| Response | Keine | Ja (read-only) | Ja (mit state change) |
| Synchron | Nein | Ja | Ja |
| Validierung | Nein | N/A | Optional |
| Event History | Ja | Nein | Nur wenn validiert |
| State ändern | Ja | Nein | Ja |
| Activities | Ja (async) | Nein | Ja (async) |

### Best Practices

1. **Initialisierung**: `@workflow.init` verwenden
2. **Typsicherheit**: Dataclasses für Parameter
3. **Concurrency**: `asyncio.Lock` für async Handler
4. **Validierung**: Validators für frühe Ablehnung
5. **Idempotenz**: Duplicate-Checks implementieren

### Häufige Fehler

❌ State in `run()` initialisieren → `@workflow.init` verwenden
❌ Async Query Handler → Nur `def`, nicht `async def`
❌ State in Query ändern → Update verwenden
❌ Kontinuierlich pollen → Update mit wait_condition

## Weiterführende Ressourcen

- [Temporal Docs: Message Passing](https://docs.temporal.io/develop/python/message-passing)
- [Python SDK API Reference](https://python.temporal.io/temporalio.workflow.html)
- [Samples Repository](https://github.com/temporalio/samples-python)
