# Kapitel 8 Beispiele: Workflow Evolution und Versioning

Praktische Code-Beispiele für sichere Workflow-Evolution mit Temporal.

## Beispiele

### 1. versioning_patching_example.py
**Demonstriert**: Patching API (`workflow.patched`)

Features:
- Multi-Version Workflow (v1, v2, v3)
- Fraud Check hinzugefügt (v2)
- Customer Notification hinzugefügt (v3)
- Replay-Kompatibilität

```bash
python versioning_patching_example.py
```

**Was Sie lernen:**
- `workflow.patched()` API verwenden
- Neue Features ohne Breaking Changes hinzufügen
- Old vs New Code Paths
- Multi-Patch Management

**Version Evolution:**

```
v1 (Base):
  ├─ process_payment
  └─ send_confirmation

v2 (+ Fraud Check):
  ├─ process_payment
  ├─ check_fraud [NEW via patch "add-fraud-check-v1"]
  └─ send_confirmation

v3 (+ Notification):
  ├─ process_payment
  ├─ check_fraud
  ├─ send_notification [NEW via patch "add-notification-v1"]
  └─ send_confirmation
```

**Patching Pattern:**
```python
if workflow.patched("patch-name"):
    # NEW CODE PATH - executed for new workflows
    result = await workflow.execute_activity(new_activity, ...)
else:
    # OLD CODE PATH - executed when replaying old workflows
    pass
```

---

### 2. replay_testing_example.py
**Demonstriert**: Replay Testing für Workflow-Kompatibilität

Features:
- Workflow History Recording
- Replay mit neuer Workflow-Version
- Breaking Change Detection
- Determinism Verification

```bash
python replay_testing_example.py
```

**Was Sie lernen:**
- Replay Tests schreiben
- Workflow-Kompatibilität verifizieren
- Breaking Changes erkennen
- `Replayer` API verwenden

**Replay Test Flow:**
```
1. Record History:
   Execute v1 workflow → Capture history

2. Replay Test:
   Replay history with v2 code → Verify compatibility

3. Result:
   ✅ Success: v2 is compatible
   ❌ Failure: Breaking change detected
```

**Breaking Changes Example:**
```python
# v1: Validate THEN Create
validate_user()
create_account()

# v2-bad: Create THEN Validate (BREAKS DETERMINISM!)
create_account()  # ❌ Order changed
validate_user()
```

---

## Voraussetzungen

1. **Temporal Server**:
   ```bash
   temporal server start-dev
   ```

2. **Worker**:
   ```bash
   python worker.py
   ```

3. **Python Dependencies**:
   ```bash
   uv sync
   ```

## Konzepte

### Determinismus

**Was ist deterministisch:**
- Workflow-Code wird bei Replay exakt gleich ausgeführt
- Gleiche Eingabe → Gleiche Entscheidungen → Gleiche History

**Warum wichtig:**
- Temporal replayed Workflows nach Worker-Crash
- Replay muss identische History erzeugen
- Non-Determinismus → Workflow Failure

### Patching API

```python
if workflow.patched("patch-id"):
    # NEW: Code für neue Executions
    new_behavior()
else:
    # OLD: Code für Replay alter Executions
    old_behavior()
```

**Lifecycle:**
1. **Add Patch**: Deployment mit neuem Code
2. **Wait**: Alle alten Workflows abwarten
3. **Deprecate**: `workflow.deprecate_patch("patch-id")`
4. **Remove**: Old code path entfernen

### Safe vs Unsafe Changes

| Change Type | Safe? | Erklärung |
|-------------|-------|-----------|
| Activity hinzufügen (mit Patch) | ✅ | Patching API macht es safe |
| Activity entfernen | ❌ | Replay wird fehlschlagen |
| Activity umordnen | ❌ | Bricht Determinismus |
| Activity Parameter ändern | ❌ | Neue Signatur ≠ alte History |
| Timeout ändern | ✅ | Metadata, nicht im Code |
| Retry Policy ändern | ✅ | Metadata, nicht im Code |
| Logging hinzufügen | ✅ | Hat keine Seiteneffekte |
| Neue Condition hinzufügen | ⚠️ | Nur mit Patch! |
| Signal Handler ändern | ⚠️ | Nur mit Patch! |

### Replay Testing

**Warum Replay Testing:**
- Workflow-Changes vor Deployment verifizieren
- Breaking Changes frühzeitig erkennen
- CI/CD Integration möglich

**Replay Test Setup:**
```python
from temporalio.worker import Replayer

# 1. Workflow History laden
history = await workflow_handle.fetch_history()

# 2. Replayer erstellen
replayer = Replayer(
    workflows=[MyWorkflowV2],
    activities=[...]
)

# 3. Replay durchführen
try:
    await replayer.replay_workflow(history)
    print("✅ Compatible!")
except Exception as e:
    print(f"❌ Breaking change: {e}")
```

## Best Practices

### 1. Patching

✅ **DO:**
- Eindeutige Patch IDs verwenden (`add-fraud-check-v1`)
- Patches dokumentieren (Kommentare im Code)
- Alte Workflows vor Cleanup abwarten
- Patch Cleanup planen (deprecate → remove)

❌ **DON'T:**
- Patch IDs wiederverwenden
- Patches ohne Wartezeit entfernen
- Zu viele Patches akkumulieren (>5)

### 2. Versioning Strategy

**Wann welche Strategie:**

1. **Patching API**:
   - ✅ Kleine, inkrementelle Changes
   - ✅ Backward-kompatible Additions
   - ❌ Komplexe Refactorings

2. **Worker Versioning**:
   - ✅ Größere Feature-Releases
   - ✅ Team hat mehrere Versionen parallel
   - ✅ A/B Testing needed

3. **Workflow-Name Versioning**:
   - ✅ Breaking Changes unvermeidbar
   - ✅ Komplette Business Logic Änderung
   - ❌ Häufige Changes

### 3. Testing

✅ **Immer testen:**
- Replay Tests für jeden Workflow-Change
- Integration Tests mit echtem Temporal Server
- History-Export aus Production → Replay in Dev

✅ **CI/CD Integration:**
```bash
# In CI Pipeline
pytest tests/replay/test_workflow_v2_compatibility.py
```

### 4. Migration Patterns

**Pattern 1: Dual-Write während Migration**
```python
# Old workflows weiter unterstützen
if workflow.patched("migration-v2"):
    new_workflow_logic()
else:
    old_workflow_logic()
```

**Pattern 2: Graceful Deprecation**
```python
# Nach einiger Zeit
if workflow.deprecate_patch("old-feature"):
    # Code wird nie mehr ausgeführt
    pass
```

**Pattern 3: Big Bang Migration**
```python
# Neue Workflow-Version mit neuem Namen
@workflow.defn(name="OrderWorkflowV2")
class OrderWorkflowV2:
    ...
```

## Common Pitfalls

### ❌ Pitfall 1: Nicht-deterministische Operationen

```python
# FALSCH: random() ändert sich bei Replay
if random.random() > 0.5:
    do_something()

# RICHTIG: random() in Activity
result = await workflow.execute_activity(random_decision, ...)
if result:
    do_something()
```

### ❌ Pitfall 2: Activity Reihenfolge ändern

```python
# v1
await activity_a()
await activity_b()

# v2 (FALSCH!)
await activity_b()  # Reihenfolge geändert
await activity_a()

# v2 (RICHTIG mit Patch)
if workflow.patched("reorder-v2"):
    await activity_b()
    await activity_a()
else:
    await activity_a()
    await activity_b()
```

### ❌ Pitfall 3: Workflow State ändern

```python
# FALSCH: State-Struktur ändern bricht Replay
# v1
self.status = "pending"

# v2
self.status = {"state": "pending", "timestamp": ...}  # ❌ Breaking!

# RICHTIG:
if workflow.patched("status-v2"):
    self.status = {"state": "pending", "timestamp": ...}
else:
    self.status = "pending"
```

## Debugging

### Workflow History analysieren

```bash
# History Events anzeigen
temporal workflow show \
  --workflow-id my-workflow-123 \
  --output json

# Als JSON exportieren (für Replay Tests)
temporal workflow show \
  --workflow-id my-workflow-123 \
  --output json > history.json
```

### Non-Determinism Error debuggen

```python
# Im Worker Log suchen nach:
# "non-deterministic workflow: expected X, got Y"

# Problem identifizieren:
# 1. Welches Event wird erwartet? (X)
# 2. Welches Event wurde generiert? (Y)
# 3. Welcher Code-Change hat Y verursacht?
```

### Replay Test mit captured History

```python
import json

# History aus File laden
with open("production_history.json") as f:
    history_data = json.load(f)

# Als History Object konvertieren
from temporalio.client import WorkflowHistory
history = WorkflowHistory.from_json("workflow-id", history_data)

# Replay
await replayer.replay_workflow(history)
```

## Weiterführende Themen

- Worker Versioning mit Build IDs (Kapitel 8.4)
- Deployment Strategies (Blue-Green, Canary) (Kapitel 10)
- Workflow Migration Patterns (Kapitel 8.6)
- Testing Advanced Patterns (Kapitel 11)

## Ressourcen

- [Temporal Docs: Versioning](https://docs.temporal.io/workflows#workflow-versioning)
- [Python SDK: workflow.patched](https://python.temporal.io/temporalio.workflow.html#patched)
- [Replay Testing Guide](https://docs.temporal.io/dev-guide/python/testing#replay-testing)
