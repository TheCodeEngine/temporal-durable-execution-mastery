# Kapitel 4: Entwicklungs-Setup und SDK-Auswahl

Willkommen zu **Teil II** des Buches! Nachdem wir in Teil I die theoretischen Grundlagen von Temporal kennengelernt haben, tauchen wir nun in die **praktische Entwicklung** ein. In diesem Kapitel richten wir die komplette Entwicklungsumgebung ein, wählen das richtige SDK aus und lernen die Tools kennen, die uns bei der täglichen Arbeit mit Temporal unterstützen.

## 4.1 SDK-Übersicht: Die Wahl der richtigen Sprache

### 4.1.1 Verfügbare SDKs

Temporal bietet **sieben offizielle SDKs** für verschiedene Programmiersprachen (Stand 2025):

```mermaid
graph TB
    subgraph "Native Implementations"
        Go[Go SDK<br/>Native Implementation]
        Java[Java SDK<br/>Native Implementation]
    end

    subgraph "Rust Core SDK Based"
        TS[TypeScript SDK<br/>Built on Rust Core]
        Python[Python SDK<br/>Built on Rust Core]
        DotNet[.NET SDK<br/>Built on Rust Core]
        PHP[PHP SDK<br/>Built on Rust Core]
        Ruby[Ruby SDK<br/>Built on Rust Core<br/>Pre-release]
    end

    RustCore[Rust Core SDK<br/>Shared Implementation]

    TS -.-> RustCore
    Python -.-> RustCore
    DotNet -.-> RustCore
    PHP -.-> RustCore
    Ruby -.-> RustCore

    style Go fill:#e1f5ff
    style Java fill:#ffe1e1
    style Python fill:#90EE90
    style TS fill:#fff4e1
    style DotNet fill:#e1ffe1
    style PHP fill:#ffffcc
    style Ruby fill:#FFB6C1
    style RustCore fill:#cccccc
```

**Architektur-Unterschiede**:

**Native Implementationen** (Go, Java):
- Komplett eigenständige Implementierungen
- Eigene Metric-Standards (Sekunden statt Millisekunden)
- Lange etabliert und battle-tested

**Rust Core SDK Based** (TypeScript, Python, .NET, PHP, Ruby):
- Teilen dieselbe Rust-basierte Core-Implementierung
- Metrics in Millisekunden
- Effizientere Ressourcennutzung
- Einheitliches Verhalten über SDKs hinweg

### 4.1.2 Python SDK: Unser Fokus

**Warum Python?**

```python
# Python bietet native async/await Unterstützung
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class DataProcessingWorkflow:
    @workflow.run
    async def run(self, data: list[str]) -> dict:
        # Natürliches async/await für parallele Operationen
        results = await asyncio.gather(
            *[self.process_item(item) for item in data]
        )
        return {"processed": len(results)}
```

**Python SDK Stärken**:

1. **Async/Await Native**: Perfekt für Workflows mit Timern und parallelen Tasks
2. **Type Safety**: Vollständige Type Hints mit Generics
3. **Workflow Sandbox**: Automatische Modul-Neuladung für Determinismus
4. **ML/AI Ecosystem**: Ideal für Data Science, Machine Learning, LLM-Projekte
5. **Entwickler-Freundlichkeit**: Pythonic API, saubere Syntax

**Technische Anforderungen**:
```bash
# Python Version
Python >= 3.10  (empfohlen: 3.10+)

# Core Dependencies
temporalio >= 1.0.0
protobuf >= 3.20, < 7.0.0
```

### 4.1.3 Wann welches SDK?

**Entscheidungsmatrix**:

| Szenario | Empfohlenes SDK | Grund |
|----------|----------------|-------|
| Data Science, ML, AI | **Python** | Ecosystem, Libraries |
| High-Performance Microservices | **Go** | Performance, Concurrency |
| Enterprise Backend | **Java** | JVM Ecosystem, Legacy Integration |
| Web Development | **TypeScript** | Node.js, Frontend-Integration |
| .NET Shops | **.NET** | C# Integration, Performance |
| Polyglot Architektur | **Mix** | Go API + Python Workers für ML |

**Feature Parity**: Alle Major SDKs (Go, Java, TypeScript, Python, .NET) sind **production-ready** mit vollständiger Feature-Parität.

## 4.2 Lokale Entwicklungsumgebung

### 4.2.1 Temporal Server Optionen

**Option 1: Temporal CLI Dev Server** (Empfohlen für Einstieg)

```bash
# Installation Temporal CLI
# macOS/Linux:
brew install temporal

# Oder: Download binary von CDN

# Dev Server starten
temporal server start-dev

# Mit persistenter SQLite-Datenbank
temporal server start-dev --db-filename temporal.db

# In Docker
docker run --rm -p 7233:7233 -p 8233:8233 \
    temporalio/temporal server start-dev --ip 0.0.0.0
```

**Eigenschaften**:
- **Ports**: gRPC auf localhost:7233, Web UI auf http://localhost:8233
- **Database**: In-Memory (ohne `--db-filename`) oder SQLite
- **Features**: Embedded Server, Web UI, Default Namespace
- **Ideal für**: Erste Schritte, Tutorials, lokales Testen

**Option 2: Docker Compose** (Production-like)

```bash
# Temporal Docker Compose Setup klonen
git clone https://github.com/temporalio/docker-compose.git
cd docker-compose

# Starten
docker compose up

# Im Hintergrund
docker compose up -d
```

**Komponenten**:
```yaml
services:
  postgresql:      # Port 5432, Credentials: temporal/temporal
  elasticsearch:   # Port 9200, Single-Node Mode
  temporal:        # gRPC: 7233, Web UI: 8080
  temporal-admin-tools:
  temporal-ui:
```

**Ideal für**:
- Production-ähnliche lokale Entwicklung
- Testing mit Elasticsearch Visibility
- Multi-Service Integration Tests

**Option 3: Temporalite** (Leichtgewichtig)

```bash
# Standalone Binary mit SQLite
# Weniger Ressourcen als Docker Compose
# Nur für Development/Testing
```

**Vergleich der Optionen**:

```mermaid
graph LR
    subgraph "Development Journey"
        Start[Start Learning]
        Dev[Active Development]
        PreProd[Pre-Production Testing]
    end

    Start -->|Use| CLI[CLI Dev Server<br/>Schnell, Einfach]
    Dev -->|Use| Docker[Docker Compose<br/>Production-like]
    PreProd -->|Use| Full[Full Deployment<br/>Kubernetes]

    style CLI fill:#90EE90
    style Docker fill:#fff4e1
    style Full fill:#ffe1e1
```

### 4.2.2 Python Entwicklungsumgebung

**Moderne Toolchain mit uv** (Empfohlen 2025):

```bash
# uv installieren (10-100x schneller als pip)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Projekt erstellen
mkdir my-temporal-project
cd my-temporal-project

# Python-Version festlegen
echo "3.13" > .python-version

# pyproject.toml erstellen
cat > pyproject.toml << 'EOF'
[project]
name = "my-temporal-project"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "temporalio>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
]
EOF

# Dependencies installieren
uv sync

# Script ausführen (uv managed venv automatisch)
uv run python worker.py
```

**Traditioneller Ansatz** (falls uv nicht verfügbar):

```bash
# Virtual Environment erstellen
python -m venv venv

# Aktivieren
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies installieren
pip install temporalio

# Mit optionalen Features
pip install temporalio[opentelemetry,pydantic]
```

**Temporal SDK Extras**:

```bash
# gRPC Support
pip install temporalio[grpc]

# OpenTelemetry für Tracing
pip install temporalio[opentelemetry]

# Pydantic Integration
pip install temporalio[pydantic]

# Alles
pip install temporalio[grpc,opentelemetry,pydantic]
```

### 4.2.3 IDE Setup und Debugging

**VSCode Configuration**:

```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Worker",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/workers/worker.py",
            "console": "integratedTerminal",
            "justMyCode": false,
            "env": {
                "TEMPORAL_ADDRESS": "localhost:7233",
                "LOG_LEVEL": "DEBUG"
            }
        },
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal"
        }
    ]
}
```

**Debugging-Einschränkungen**:

```python
from temporalio import workflow, activity

# ✅ Breakpoints funktionieren
@activity.defn
async def my_activity(param: str) -> str:
    # Breakpoint hier funktioniert!
    result = process(param)
    return result

# ❌ Breakpoints funktionieren NICHT (Sandbox-Limitation)
@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, input: str) -> str:
        # Breakpoint hier wird NICHT getroffen
        result = await workflow.execute_activity(...)
        return result
```

**Workaround**: Nutze `workflow.logger` für Debugging in Workflows:

```python
@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, order_id: str) -> str:
        workflow.logger.info(f"Processing order: {order_id}")

        result = await workflow.execute_activity(...)
        workflow.logger.debug(f"Activity result: {result}")

        return result
```

## 4.3 Projekt-Struktur und Best Practices

### 4.3.1 Empfohlene Verzeichnisstruktur

```
my-temporal-project/
├── .env                        # Environment Variables (nicht committen!)
├── .gitignore
├── .python-version             # Python 3.13
├── pyproject.toml              # Projekt-Konfiguration
├── temporal.toml               # Temporal Multi-Environment Config
├── README.md
│
├── src/
│   ├── __init__.py
│   │
│   ├── workflows/              # Alle Workflow-Definitionen
│   │   ├── __init__.py
│   │   ├── order_workflow.py
│   │   └── payment_workflow.py
│   │
│   ├── activities/             # Alle Activity-Implementierungen
│   │   ├── __init__.py
│   │   ├── email_activities.py
│   │   └── payment_activities.py
│   │
│   ├── models/                 # Shared Types und Dataclasses
│   │   ├── __init__.py
│   │   └── order_models.py
│   │
│   └── workers/                # Worker-Prozesse
│       ├── __init__.py
│       └── main_worker.py
│
├── tests/                      # Test Suite
│   ├── __init__.py
│   ├── conftest.py            # pytest Fixtures
│   ├── test_workflows/
│   │   └── test_order_workflow.py
│   └── test_activities/
│       └── test_email_activities.py
│
└── scripts/                    # Helper Scripts
    ├── start_worker.sh
    └── deploy.sh
```

### 4.3.2 Type-Safe Workflow Development

**Input/Output mit Dataclasses**:

```python
# src/models/order_models.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class OrderInput:
    order_id: str
    customer_email: str
    items: list[str]
    total_amount: float

@dataclass
class OrderResult:
    success: bool
    transaction_id: Optional[str] = None
    error_message: Optional[str] = None

# src/workflows/order_workflow.py
from temporalio import workflow
from datetime import timedelta
from ..models.order_models import OrderInput, OrderResult
from ..activities.payment_activities import process_payment
from ..activities.email_activities import send_confirmation

@workflow.defn
class OrderWorkflow:
    """
    Orchestriert den Order-Processing-Flow.
    """

    @workflow.run
    async def run(self, input: OrderInput) -> OrderResult:
        """
        Verarbeitet eine Bestellung.

        Args:
            input: Order-Daten mit allen relevanten Informationen

        Returns:
            OrderResult mit Transaction ID oder Fehler
        """
        workflow.logger.info(f"Processing order {input.order_id}")

        try:
            # Payment verarbeiten
            transaction_id = await workflow.execute_activity(
                process_payment,
                args=[input.total_amount, input.customer_email],
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Confirmation Email senden
            await workflow.execute_activity(
                send_confirmation,
                args=[input.customer_email, input.order_id, transaction_id],
                start_to_close_timeout=timedelta(seconds=10),
            )

            return OrderResult(
                success=True,
                transaction_id=transaction_id
            )

        except Exception as e:
            workflow.logger.error(f"Order processing failed: {e}")
            return OrderResult(
                success=False,
                error_message=str(e)
            )
```

**Vorteile von Dataclasses**:
- ✅ Typsicherheit mit IDE-Unterstützung
- ✅ Einfaches Hinzufügen neuer Felder (mit Defaults)
- ✅ Automatische Serialisierung/Deserialisierung
- ✅ Bessere Lesbarkeit als `*args, **kwargs`

### 4.3.3 Configuration Management

**Multi-Environment Setup mit temporal.toml**:

```toml
# temporal.toml - Multi-Environment Configuration

# Default für lokale Entwicklung
[default]
target = "localhost:7233"
namespace = "default"

# Development Environment
[dev]
target = "localhost:7233"
namespace = "development"

# Staging Environment
[staging]
target = "staging.temporal.example.com:7233"
namespace = "staging"
tls_cert_path = "/path/to/staging-cert.pem"
tls_key_path = "/path/to/staging-key.pem"

# Production Environment
[prod]
target = "prod.temporal.example.com:7233"
namespace = "production"
tls_cert_path = "/path/to/prod-cert.pem"
tls_key_path = "/path/to/prod-key.pem"
```

**Environment-basierte Client-Konfiguration**:

```python
# src/config.py
import os
from temporalio.client import Client
from temporalio.envconfig import load_client_config

async def create_client() -> Client:
    """
    Erstellt Temporal Client basierend auf TEMPORAL_PROFILE env var.

    Beispiel:
        export TEMPORAL_PROFILE=prod
        python worker.py  # Verbindet zu Production
    """
    profile = os.getenv("TEMPORAL_PROFILE", "default")
    config = load_client_config(profile=profile)

    client = await Client.connect(**config)
    return client
```

**.env File** (nicht committen!):

```bash
# .env - Lokale Entwicklung
TEMPORAL_ADDRESS=localhost:7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=order-processing
TEMPORAL_PROFILE=dev

# Application Config
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://user:pass@localhost:5432/orders

# External Services
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
STRIPE_API_KEY=sk_test_...
```

**Config Loading mit Pydantic**:

```python
# src/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Temporal Config
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "default"

    # Application Config
    log_level: str = "INFO"
    database_url: str

    # External Services
    smtp_server: str
    smtp_port: int = 587
    stripe_api_key: str

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Singleton Settings Instance."""
    return Settings()

# Usage
from config import get_settings
settings = get_settings()
```

## 4.4 Development Workflow

### 4.4.1 Worker Development Loop

**Typischer Entwicklungs-Workflow**:

```mermaid
graph TB
    Start[Code Ändern]
    Restart[Worker Neustarten]
    Test[Workflow Testen]
    Debug[Debuggen mit Web UI]
    Fix[Fehler Fixen]

    Start --> Restart
    Restart --> Test
    Test -->|Error| Debug
    Debug --> Fix
    Fix --> Start
    Test -->|Success| Done[Feature Complete]

    style Start fill:#e1f5ff
    style Test fill:#fff4e1
    style Debug fill:#ffe1e1
    style Done fill:#90EE90
```

**1. Worker starten**:

```bash
# Terminal 1: Temporal Server (falls nicht bereits läuft)
temporal server start-dev --db-filename temporal.db

# Terminal 2: Worker starten
uv run python src/workers/main_worker.py

# Oder mit Environment
TEMPORAL_PROFILE=dev LOG_LEVEL=DEBUG uv run python src/workers/main_worker.py
```

**2. Workflow ausführen**:

```python
# scripts/run_workflow.py
import asyncio
from temporalio.client import Client
from src.workflows.order_workflow import OrderWorkflow
from src.models.order_models import OrderInput

async def main():
    client = await Client.connect("localhost:7233")

    input_data = OrderInput(
        order_id="ORD-123",
        customer_email="customer@example.com",
        items=["Item A", "Item B"],
        total_amount=99.99
    )

    result = await client.execute_workflow(
        OrderWorkflow.run,
        input_data,
        id="order-ORD-123",
        task_queue="order-processing",
    )

    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

```bash
# Workflow ausführen
uv run python scripts/run_workflow.py
```

**3. Debugging mit Web UI**:

```
# Web UI öffnen
http://localhost:8233

# Workflow suchen: order-ORD-123
# → Event History inspizieren
# → Input/Output anzeigen
# → Stack Trace bei Errors
```

**4. Code-Änderungen ohne Downtime**:

```python
# Bei Code-Änderungen:
# 1. Worker mit Ctrl+C stoppen
# 2. Code ändern
# 3. Worker neu starten

# Laufende Workflows:
# → Werden automatisch fortgesetzt
# → Event History bleibt erhalten
# → Bei Breaking Changes: Workflow Versioning nutzen (Kapitel 9)
```

### 4.4.2 Temporal CLI Commands

**Wichtigste Commands für Development**:

```bash
# Workflows auflisten
temporal workflow list

# Workflow Details
temporal workflow describe -w order-ORD-123

# Event History anzeigen
temporal workflow show -w order-ORD-123

# Event History als JSON exportieren
temporal workflow show -w order-ORD-123 > history.json

# Workflow starten
temporal workflow start \
  --task-queue order-processing \
  --type OrderWorkflow \
  --workflow-id order-ORD-456 \
  --input '{"order_id": "ORD-456", "customer_email": "test@example.com", ...}'

# Workflow ausführen und auf Result warten
temporal workflow execute \
  --task-queue order-processing \
  --type OrderWorkflow \
  --workflow-id order-ORD-789 \
  --input @input.json

# Workflow canceln
temporal workflow cancel -w order-ORD-123

# Workflow terminieren (hard stop)
temporal workflow terminate -w order-ORD-123

# Signal senden
temporal workflow signal \
  --workflow-id order-ORD-123 \
  --name add-item \
  --input '{"item": "Item C"}'

# Query ausführen
temporal workflow query \
  --workflow-id order-ORD-123 \
  --type get-status

# Workflow Count
temporal workflow count
```

**Temporal Web UI Navigation**:

```
http://localhost:8233
│
├── Workflows → Alle Workflow Executions
│   ├── Filter (Status, Type, Time Range)
│   ├── Search (Workflow ID, Run ID)
│   └── Details → Event History
│       ├── Timeline View
│       ├── Compact View
│       ├── Full History
│       └── JSON Export
│
├── Namespaces → Namespace Management
├── Archival → Archived Workflows
└── Settings → Server Configuration
```

## 4.5 Testing und Debugging

### 4.5.1 Test-Setup mit pytest

**Dependencies installieren**:

```toml
# pyproject.toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",  # Coverage reporting
]
```

```bash
uv sync --all-extras
```

**pytest Configuration**:

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### 4.5.2 Workflow Testing mit Time-Skipping

**Integration Test**:

```python
# tests/test_workflows/test_order_workflow.py
import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from src.workflows.order_workflow import OrderWorkflow
from src.activities.payment_activities import process_payment
from src.activities.email_activities import send_confirmation
from src.models.order_models import OrderInput

@pytest.mark.asyncio
async def test_order_workflow_success():
    """Test erfolgreicher Order-Processing Flow."""

    # Time-Skipping Test Environment
    async with await WorkflowEnvironment.start_time_skipping() as env:
        # Worker mit Workflows und Activities
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[OrderWorkflow],
            activities=[process_payment, send_confirmation],
        ):
            # Workflow ausführen
            input_data = OrderInput(
                order_id="TEST-001",
                customer_email="test@example.com",
                items=["Item A"],
                total_amount=49.99
            )

            result = await env.client.execute_workflow(
                OrderWorkflow.run,
                input_data,
                id="test-order-001",
                task_queue="test-queue",
            )

            # Assertions
            assert result.success is True
            assert result.transaction_id is not None
            assert result.error_message is None
```

**Test mit gemockten Activities**:

```python
from temporalio import activity

@activity.defn
async def mock_process_payment(amount: float, email: str) -> str:
    """Mock Payment Activity für Tests."""
    return f"mock-txn-{amount}"

@activity.defn
async def mock_send_confirmation(email: str, order_id: str, txn_id: str) -> None:
    """Mock Email Activity für Tests."""
    pass

@pytest.mark.asyncio
async def test_order_workflow_with_mocks():
    """Test mit gemockten Activities."""

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[OrderWorkflow],
            activities=[mock_process_payment, mock_send_confirmation],  # Mocks!
        ):
            result = await env.client.execute_workflow(...)

            assert result.success is True
```

**Time Skipping für Timeouts**:

```python
from datetime import timedelta

@pytest.mark.asyncio
async def test_workflow_with_long_timeout():
    """Test Workflow mit 7 Tagen Sleep - läuft sofort!"""

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(...):
            # Workflow mit 7-Tage Sleep
            # Time-Skipping: Läuft in Millisekunden statt 7 Tagen!
            result = await env.client.execute_workflow(
                WeeklyReportWorkflow.run,
                ...
            )

            assert result.week_number == 1
```

### 4.5.3 Activity Unit Tests

```python
# tests/test_activities/test_payment_activities.py
import pytest
from src.activities.payment_activities import process_payment

@pytest.mark.asyncio
async def test_process_payment_success():
    """Test Payment Activity in Isolation."""

    # Activity direkt testen (ohne Temporal)
    result = await process_payment(
        amount=99.99,
        email="test@example.com"
    )

    assert result.startswith("txn_")
    assert len(result) > 10

@pytest.mark.asyncio
async def test_process_payment_invalid_amount():
    """Test Payment Activity mit ungültigem Amount."""

    from temporalio.exceptions import ApplicationError

    with pytest.raises(ApplicationError) as exc_info:
        await process_payment(
            amount=-10.00,  # Ungültig!
            email="test@example.com"
        )

    assert "Invalid amount" in str(exc_info.value)
    assert exc_info.value.non_retryable is True
```

### 4.5.4 Replay Testing

**Workflow History exportieren**:

```bash
# Via CLI
temporal workflow show -w order-ORD-123 > workflow_history.json

# Via Web UI
# → Workflow Details → JSON Tab → Copy
```

**Replay Test**:

```python
# tests/test_workflows/test_replay.py
import pytest
from temporalio.worker import Replayer
from temporalio.client import WorkflowHistory
from src.workflows.order_workflow import OrderWorkflow

@pytest.mark.asyncio
async def test_replay_order_workflow():
    """Test Workflow Replay für Non-Determinism."""

    # History laden
    with open("tests/fixtures/order_workflow_history.json") as f:
        history = WorkflowHistory.from_json(f.read())

    # Replayer erstellen
    replayer = Replayer(
        workflows=[OrderWorkflow]
    )

    # Replay (wirft Exception bei Non-Determinism)
    await replayer.replay_workflow(history)
```

**Warum Replay Testing?**
- Erkennt Non-Deterministic Errors bei Code-Änderungen
- Verifiziert Workflow-Kompatibilität mit alten Executions
- Verhindert Production-Crashes durch Breaking Changes

### 4.5.5 Coverage und CI/CD

```bash
# Test Coverage
pytest --cov=src --cov-report=html tests/

# Output
# Coverage: 87%
# HTML Report: htmlcov/index.html

# Im CI/CD (GitHub Actions Beispiel)
# .github/workflows/test.yml
```

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run tests
        run: uv run pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 4.6 Debugging und Observability

### 4.6.1 Logging Best Practices

```python
import logging
from temporalio import workflow, activity

# Root Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,  # DEBUG für Development
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, input: OrderInput) -> OrderResult:
        # Workflow Logger nutzen (nicht logging.getLogger!)
        workflow.logger.info(f"Processing order {input.order_id}")
        workflow.logger.debug(f"Input details: {input}")

        try:
            result = await workflow.execute_activity(...)
            workflow.logger.info(f"Payment successful: {result}")
            return OrderResult(success=True, transaction_id=result)

        except Exception as e:
            workflow.logger.error(f"Order failed: {e}", exc_info=True)
            return OrderResult(success=False, error_message=str(e))

@activity.defn
async def process_payment(amount: float, email: str) -> str:
    # Activity Logger nutzen
    activity.logger.info(f"Processing payment: {amount} for {email}")

    try:
        txn_id = charge_card(amount, email)
        activity.logger.info(f"Payment successful: {txn_id}")
        return txn_id
    except Exception as e:
        activity.logger.error(f"Payment failed: {e}", exc_info=True)
        raise
```

**Log Levels**:
- **DEBUG**: Development, detailliertes Troubleshooting
- **INFO**: Production, wichtige Events
- **WARNING**: Potentielle Probleme
- **ERROR**: Fehler die gehandled werden
- **CRITICAL**: Kritische Fehler

### 4.6.2 Prometheus Metrics

```python
from temporalio.runtime import Runtime, TelemetryConfig, PrometheusConfig
from temporalio.client import Client

# Prometheus Endpoint konfigurieren
runtime = Runtime(
    telemetry=TelemetryConfig(
        metrics=PrometheusConfig(
            bind_address="0.0.0.0:9000"  # Metrics Port
        )
    )
)

client = await Client.connect(
    "localhost:7233",
    runtime=runtime
)

# Metrics verfügbar auf:
# http://localhost:9000/metrics
```

**Verfügbare Metrics**:
- `temporal_workflow_task_execution_total`
- `temporal_activity_execution_total`
- `temporal_workflow_task_execution_latency_ms`
- `temporal_activity_execution_latency_ms`
- `temporal_worker_task_slots_available`
- `temporal_sticky_cache_hit_total`

### 4.6.3 OpenTelemetry Tracing

```bash
# Installation
pip install temporalio[opentelemetry]
```

```python
from temporalio.contrib.opentelemetry import TracingInterceptor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor

# OpenTelemetry Setup
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)

# Temporal Client mit Tracing
interceptor = TracingInterceptor()
client = await Client.connect(
    "localhost:7233",
    interceptors=[interceptor]
)

# Alle Workflow/Activity Executions werden getracet
```

## 4.7 Zusammenfassung

In diesem Kapitel haben wir die komplette Entwicklungsumgebung für Temporal aufgesetzt:

**SDK-Auswahl**:
- 7 offizielle SDKs (Go, Java, TypeScript, Python, .NET, PHP, Ruby)
- Python SDK: Python >= 3.10, Rust Core SDK, Type-Safe, Async/Await
- Feature Parity über alle Major SDKs

**Lokale Entwicklung**:
- **Temporal Server**: CLI Dev Server (Einstieg), Docker Compose (Production-like)
- **Python Setup**: uv (modern, schnell) oder venv (traditionell)
- **IDE**: VSCode/PyCharm mit Debugging (Limitations in Workflows!)

**Projekt-Struktur**:
- Separation: workflows/, activities/, models/, workers/
- Type-Safe Dataclasses für Input/Output
- Multi-Environment Config (temporal.toml, .env)

**Development Workflow**:
- Worker Development Loop: Code → Restart → Test → Debug
- Temporal CLI: workflow list/show/execute/signal/query
- Web UI: Event History, Timeline, Stack Traces

**Testing**:
- pytest mit pytest-asyncio
- Time-Skipping Environment für schnelle Tests
- Activity Mocking
- Replay Testing für Non-Determinism
- Coverage Tracking

**Debugging & Observability**:
- Logging: workflow.logger, activity.logger
- Prometheus Metrics auf Port 9000
- OpenTelemetry Tracing
- Web UI Event History Inspection

```mermaid
graph TB
    Code[Code Schreiben]
    Test[Testen mit pytest]
    Debug[Debuggen mit Web UI]
    Deploy[Deployment]

    Code -->|Type-Safe Dataclasses| Test
    Test -->|Time-Skipping| Debug
    Debug -->|Logging + Metrics| Deploy
    Deploy -->|Observability| Monitor[Monitoring]

    style Code fill:#e1f5ff
    style Test fill:#fff4e1
    style Debug fill:#ffe1e1
    style Deploy fill:#90EE90
    style Monitor fill:#ffffcc
```

**Nächstes Kapitel**: [Kapitel 5: Workflows programmieren](part-02-chapter-05.md) – Wir tauchen tief in fortgeschrittene Workflow-Patterns ein!

---

**Praktische Übung**: Richten Sie Ihre lokale Entwicklungsumgebung ein und erstellen Sie Ihren ersten eigenen Workflow!
