# Kapitel 7 Beispiele: Error Handling und Retry Policies

Praktische Code-Beispiele für robuste Fehlerbehandlung in Temporal.

## Beispiele

### 1. retry_policy_example.py
**Demonstriert**: Verschiedene Retry-Strategien

Features:
- Default Retry (unbegrenzt)
- Limited Retries (maximum_attempts)
- Custom Backoff (initial_interval, backoff_coefficient)
- Non-Retryable Errors

```bash
python retry_policy_example.py
```

**Was Sie lernen:**
- RetryPolicy Parameter konfigurieren
- Exponential Backoff Strategien
- Non-retryable Error Types
- Unterschied zwischen retriable und non-retriable Errors

**Retry Strategies im Beispiel:**

1. **Default**: Unbegrenzte Retries bis Erfolg
2. **Limited**: Max 3 Versuche
3. **Custom Backoff**: 100ms initial, 1.5x coefficient, max 2s
4. **Non-Retryable**: Sofortiges Fehlschlagen ohne Retries

---

### 2. saga_pattern_example.py
**Demonstriert**: SAGA Pattern für Distributed Transactions

Features:
- Forward Transactions (book_car, book_hotel, book_flight)
- Compensation Actions (undo_book_*)
- Automatic Rollback bei Failure
- LIFO Compensation Order

```bash
python saga_pattern_example.py
```

**Was Sie lernen:**
- SAGA Pattern Implementation
- Compensation Activities definieren
- Error Handling mit Compensations
- Resiliente Compensation Execution
- State Tracking für Partial Success

**SAGA Flow:**
```
Success:
  book_car → book_hotel → book_flight → Complete

Failure (hotel fails):
  book_car → book_hotel [FAIL] → undo_book_car → Rolled Back
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

### Retry Policy Parameter

```python
RetryPolicy(
    initial_interval=timedelta(seconds=1),      # Erste Wartezeit
    backoff_coefficient=2.0,                     # Multiplikator
    maximum_interval=timedelta(seconds=100),     # Max Wartezeit
    maximum_attempts=5,                          # Max Versuche (0=∞)
    non_retryable_error_types=["ValidationError"]  # Keine Retries
)
```

### Exponential Backoff

```
Versuch 1: Sofort
Versuch 2: +1s  (1s total)
Versuch 3: +2s  (3s total)
Versuch 4: +4s  (7s total)
Versuch 5: +8s  (15s total)
...
```

### SAGA Pattern

**Komponenten:**
1. **Forward Activities**: Normale Business-Operationen
2. **Compensation Activities**: Undo-Operationen
3. **Compensation Stack**: LIFO Order für Rollback
4. **Error Handling**: Catch und execute compensations

**Best Practices:**
- Alle Activities idempotent machen
- Compensations robuster als Forward (mehr Retries)
- Partial Success tracken
- Ausführliches Logging

## Activity Timeout Types

| Timeout | Scope | Triggers Retry |
|---------|-------|----------------|
| Start-To-Close | Einzelner Versuch | Ja |
| Schedule-To-Close | Gesamt (inkl. Retries) | Nein |
| Schedule-To-Start | Queue Zeit | Nein |
| Heartbeat | Zwischen Heartbeats | Ja |

## Error Kategorien

### Retriable (Retry erlaubt)
- Network Timeouts
- Connection Errors
- Service Unavailable (503)
- Rate Limiting (429)
- Database Deadlocks

### Non-Retriable (Kein Retry)
- Authentication Failed (401, 403)
- Not Found (404)
- Validation Errors (400)
- Business Logic (Insufficient Funds)

## Best Practices

1. **Timeouts**:
   - ✅ Start-To-Close IMMER setzen
   - ✅ Heartbeats für Long-Running (>1min)
   - ⚠️ Schedule-To-Close optional

2. **Retry Policies**:
   - ✅ Non-retryable Errors explizit markieren
   - ✅ Custom Delays bei Rate Limiting
   - ✅ Limited Attempts bei kritischen Ops

3. **Error Handling**:
   - ✅ Try/Except in Workflows
   - ✅ Root Cause via e.cause navigieren
   - ✅ Details für Debugging loggen

4. **SAGA Pattern**:
   - ✅ Idempotenz sicherstellen
   - ✅ Compensations testen
   - ✅ Partial Success erlauben
   - ✅ LIFO Order einhalten

## Debugging

### Activity Fehler untersuchen:
```python
try:
    result = await workflow.execute_activity(...)
except ActivityError as e:
    print(f"Activity Type: {e.activity_type}")
    print(f"Activity ID: {e.activity_id}")
    print(f"Retry State: {e.retry_state}")
    if isinstance(e.cause, ApplicationError):
        print(f"Root Cause: {e.cause.type}: {e.cause.message}")
        print(f"Details: {e.cause.details}")
```

### CLI Commands:
```bash
# Workflow beschreiben
temporal workflow describe --workflow-id my-workflow-id

# Event History anzeigen
temporal workflow show --workflow-id my-workflow-id

# Stack Trace abrufen
temporal workflow stack --workflow-id my-workflow-id
```

## Weiterführende Themen

- Circuit Breaker Pattern (Kapitel 7.5.2)
- Dead Letter Queue Pattern (Kapitel 7.5.3)
- Workflow Evolution und Versioning (Kapitel 8)
- Advanced Resilienz Patterns (Kapitel 9)
