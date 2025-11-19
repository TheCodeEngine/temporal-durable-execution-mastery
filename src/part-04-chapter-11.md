# Kapitel 11: Monitoring und Observability

## Einleitung

Sie haben Temporal in Production deployed, Workers laufen, Workflows werden ausgeführt. Alles scheint gut zu funktionieren. Bis plötzlich:

- Workflows verzögern sich ohne erkennbaren Grund
- Activities schlagen häufiger fehl als erwartet
- Task Queues füllen sich auf
- Die Business-Logik funktioniert nicht mehr wie gewünscht

**Ohne Monitoring sind Sie blind.** Sie merken Probleme erst, wenn Kunden sich beschweren. Sie haben keine Ahnung, wo das Problem liegt. Debugging wird zum Rätselraten.

**Mit richtigem Monitoring und Observability** sehen Sie:
- Wie viele Workflows gerade laufen
- Wo Bottlenecks sind
- Welche Activities am längsten dauern
- Ob Worker überlastet sind
- Wann Probleme begannen und warum

Temporal bietet umfassende Observability-Features, aber sie müssen richtig konfiguriert und genutzt werden.

### Das Grundproblem

**Scenario**: Sie betreiben einen Order Processing Service mit Temporal:

```python
@workflow.defn
class OrderWorkflow:
    async def run(self, order_id: str) -> str:
        # 10+ Activities: payment, inventory, shipping, notifications, etc.
        payment = await workflow.execute_activity(process_payment, ...)
        inventory = await workflow.execute_activity(check_inventory, ...)
        shipping = await workflow.execute_activity(create_shipment, ...)
        # ... more activities
```

**Plötzlich**: Kunden berichten, dass Orders langsamer verarbeitet werden. Von 2 Minuten auf 10+ Minuten.

**Ohne Monitoring**:
```
❓ Welche Activity ist langsam?
❓ Ist es ein spezifischer Worker?
❓ Ist die Datenbank überlastet?
❓ Sind externe APIs langsam?
❓ Gibt es ein Deployment-Problem?

→ Stunden mit Guesswork verbringen
→ Logs manuell durchsuchen
→ Code instrumentieren und neu deployen
```

**Mit Monitoring & Observability**:
```
✓ Grafana Dashboard öffnen
✓ "process_payment" Activity latency: 9 Minuten (normal: 30s)
✓ Trace zeigt: Payment API antwortet nicht
✓ Logs zeigen: Connection timeouts zu payment.api.com
✓ Alert wurde bereits ausgelöst

→ Problem in 2 Minuten identifiziert
→ Payment Service Team kontaktieren
→ Fallback-Lösung aktivieren
```

### Die drei Säulen der Observability

**1. Metrics** (Was passiert?)
- Workflow execution rate
- Activity success/failure rates
- Queue depth
- Worker utilization
- Latency percentiles (p50, p95, p99)

**2. Logs** (Warum passiert es?)
- Structured logging in Workflows/Activities
- Correlation mit Workflow/Activity IDs
- Error messages und stack traces
- Business-relevante Events

**3. Traces** (Wie fließen Requests?)
- End-to-end Workflow execution traces
- Activity spans
- Distributed tracing über Service-Grenzen
- Bottleneck-Identifikation

### Lernziele

Nach diesem Kapitel können Sie:

- **SDK Metrics** mit Prometheus exportieren und monitoren
- **Temporal Cloud/Server Metrics** nutzen
- **Grafana Dashboards** für Temporal erstellen und nutzen
- **OpenTelemetry** für Distributed Tracing integrieren
- **Strukturierte Logs** mit Correlation implementieren
- **SLO-basiertes Alerting** für kritische Workflows aufsetzen
- **Debugging mit Observability-Tools** durchführen

---

## 11.1 SDK Metrics mit Prometheus

### 11.1.1 Warum SDK Metrics?

Temporal bietet zwei Arten von Metrics:

| Metric Source | Perspektive | Was wird gemessen? |
|---------------|-------------|-------------------|
| **SDK Metrics** | Client/Worker | Ihre Application-Performance |
| **Server Metrics** | Temporal Service | Temporal Infrastructure Health |

**Für Application Monitoring → SDK Metrics sind die Source of Truth!**

SDK Metrics zeigen:
- Activity execution time **aus Sicht Ihrer Worker**
- Workflow execution success rate **Ihrer Workflows**
- Task Queue lag **Ihrer Queues**
- Worker resource usage **Ihrer Deployments**

### 11.1.2 Prometheus Setup für Python SDK

**Schritt 1: Dependencies**

```bash
# requirements.txt
temporalio>=1.5.0
prometheus-client>=0.19.0
```

**Schritt 2: Prometheus Exporter in Worker**

```python
"""
Worker mit Prometheus Metrics Export

Chapter: 11 - Monitoring und Observability
"""

import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.contrib.prometheus import PrometheusMetricsExporter
from prometheus_client import start_http_server, CollectorRegistry
import logging

logger = logging.getLogger(__name__)


class MonitoredWorker:
    """Worker mit Prometheus Metrics"""

    def __init__(
        self,
        temporal_host: str,
        task_queue: str,
        workflows: list,
        activities: list,
        metrics_port: int = 9090
    ):
        self.temporal_host = temporal_host
        self.task_queue = task_queue
        self.workflows = workflows
        self.activities = activities
        self.metrics_port = metrics_port

    async def run(self):
        """Start worker mit Prometheus metrics export"""

        # 1. Prometheus Registry erstellen
        registry = CollectorRegistry()

        # 2. Temporal Client mit Metrics Exporter
        client = await Client.connect(
            self.temporal_host,
            # Metrics aktivieren
            runtime=self._create_runtime_with_metrics(registry)
        )

        # 3. Prometheus HTTP Server starten
        start_http_server(self.metrics_port, registry=registry)
        logger.info(f"✓ Prometheus metrics exposed on :{self.metrics_port}/metrics")

        # 4. Worker mit Metrics starten
        async with Worker(
            client,
            task_queue=self.task_queue,
            workflows=self.workflows,
            activities=self.activities
        ):
            logger.info(f"✓ Worker started on queue: {self.task_queue}")
            await asyncio.Event().wait()  # Run forever

    def _create_runtime_with_metrics(self, registry: CollectorRegistry):
        """Runtime mit Prometheus Metrics konfigurieren"""
        from temporalio.runtime import (
            Runtime,
            TelemetryConfig,
            PrometheusConfig
        )

        return Runtime(telemetry=TelemetryConfig(
            metrics=PrometheusConfig(
                # Bind an localhost:0 - wird von start_http_server übernommen
                bind_address="0.0.0.0:0",
                # Custom registry
                registry=registry
            )
        ))


# Verwendung
if __name__ == "__main__":
    from my_workflows import OrderWorkflow
    from my_activities import process_payment, check_inventory

    worker = MonitoredWorker(
        temporal_host="localhost:7233",
        task_queue="order-processing",
        workflows=[OrderWorkflow],
        activities=[process_payment, check_inventory],
        metrics_port=9090
    )

    asyncio.run(worker.run())
```

**Schritt 3: Metrics abrufen**

```bash
# Metrics endpoint testen
curl http://localhost:9090/metrics

# Ausgabe (Beispiel):
# temporal_workflow_task_execution_count{namespace="default",task_queue="order-processing"} 142
# temporal_activity_execution_count{activity_type="process_payment"} 89
# temporal_activity_execution_latency_seconds_sum{activity_type="process_payment"} 45.2
# temporal_worker_task_slots_available{task_queue="order-processing"} 98
# ...
```

### 11.1.3 Prometheus Scrape Configuration

**prometheus.yml**:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Temporal Workers
  - job_name: 'temporal-workers'
    static_configs:
      - targets:
          - 'worker-1:9090'
          - 'worker-2:9090'
          - 'worker-3:9090'
    # Labels für besseres Filtering
    relabel_configs:
      - source_labels: [__address__]
        regex: 'worker-(\d+):.*'
        target_label: 'worker_id'
        replacement: '$1'

  # Temporal Server (self-hosted)
  - job_name: 'temporal-server'
    static_configs:
      - targets:
          - 'temporal-frontend:9090'
          - 'temporal-history:9090'
          - 'temporal-matching:9090'
          - 'temporal-worker:9090'

  # Temporal Cloud (via Prometheus API)
  - job_name: 'temporal-cloud'
    scheme: https
    static_configs:
      - targets:
          - 'cloud-metrics.temporal.io'
    authorization:
      credentials: '<YOUR_TEMPORAL_CLOUD_API_KEY>'
    params:
      namespace: ['your-namespace.account']
```

**Kubernetes Service Discovery** (fortgeschritten):

```yaml
scrape_configs:
  - job_name: 'temporal-workers-k8s'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      # Nur Pods mit Label app=temporal-worker
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: temporal-worker
      # Port 9090 targeten
      - source_labels: [__meta_kubernetes_pod_ip]
        action: replace
        target_label: __address__
        replacement: '$1:9090'
      # Labels hinzufügen
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
```

### 11.1.4 Wichtige SDK Metrics

**Workflow Metrics:**

```promql
# Workflow Execution Rate
rate(temporal_workflow_task_execution_count[5m])

# Workflow Success Rate
rate(temporal_workflow_completed_count{status="completed"}[5m])
  /
rate(temporal_workflow_completed_count[5m])

# Workflow Latency (p95)
histogram_quantile(0.95,
  rate(temporal_workflow_execution_latency_seconds_bucket[5m])
)
```

**Activity Metrics:**

```promql
# Activity Execution Rate by Type
rate(temporal_activity_execution_count[5m]) by (activity_type)

# Activity Failure Rate
rate(temporal_activity_execution_failed_count[5m]) by (activity_type)

# Activity Latency by Type
histogram_quantile(0.95,
  rate(temporal_activity_execution_latency_seconds_bucket[5m])
) by (activity_type)

# Slowest Activities (Top 5)
topk(5,
  avg(rate(temporal_activity_execution_latency_seconds_sum[5m]))
  by (activity_type)
)
```

**Worker Metrics:**

```promql
# Task Slots Used vs Available
temporal_worker_task_slots_used / temporal_worker_task_slots_available

# Task Queue Lag (Backlog)
temporal_task_queue_lag_seconds

# Worker Poll Success Rate
rate(temporal_worker_poll_success_count[5m])
  /
rate(temporal_worker_poll_count[5m])
```

### 11.1.5 Custom Business Metrics

**Problem**: SDK Metrics zeigen technische Metriken, aber nicht Ihre Business KPIs.

**Lösung**: Custom Metrics in Activities exportieren.

```python
"""
Custom Business Metrics in Activities
"""

from temporalio import activity
from prometheus_client import Counter, Histogram, Gauge

# Custom Metrics
orders_processed = Counter(
    'orders_processed_total',
    'Total orders processed',
    ['status', 'payment_method']
)

order_value = Histogram(
    'order_value_usd',
    'Order value in USD',
    buckets=[10, 50, 100, 500, 1000, 5000]
)

payment_latency = Histogram(
    'payment_processing_seconds',
    'Payment processing time',
    ['payment_provider']
)

active_orders = Gauge(
    'active_orders',
    'Currently processing orders'
)


@activity.defn
async def process_order(order_id: str, amount: float, payment_method: str) -> str:
    """Process order mit custom metrics"""

    # Gauge: Active orders erhöhen
    active_orders.inc()

    try:
        # Business-Logic
        start = time.time()
        payment_result = await process_payment(amount, payment_method)
        latency = time.time() - start

        # Metrics erfassen
        payment_latency.labels(payment_provider=payment_method).observe(latency)
        order_value.observe(amount)
        orders_processed.labels(
            status='completed',
            payment_method=payment_method
        ).inc()

        return f"Order {order_id} completed"

    except Exception as e:
        orders_processed.labels(
            status='failed',
            payment_method=payment_method
        ).inc()
        raise

    finally:
        # Gauge: Active orders reduzieren
        active_orders.dec()
```

**PromQL Queries für Business Metrics:**

```promql
# Revenue per Hour
sum(rate(order_value_usd_sum[1h]))

# Orders per Minute by Payment Method
sum(rate(orders_processed_total[1m])) by (payment_method)

# Payment Provider Performance
histogram_quantile(0.95,
  rate(payment_processing_seconds_bucket[5m])
) by (payment_provider)

# Success Rate by Payment Method
sum(rate(orders_processed_total{status="completed"}[5m])) by (payment_method)
  /
sum(rate(orders_processed_total[5m])) by (payment_method)
```

---

## 11.2 Grafana Dashboards

### 11.2.1 Grafana Setup

**Docker Compose Setup** (Development):

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9091:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - prometheus

volumes:
  prometheus-data:
  grafana-data:
```

**Grafana Datasource Provisioning**:

```yaml
# grafana/provisioning/datasources/prometheus.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
```

### 11.2.2 Community Dashboards

Temporal stellt Community Grafana Dashboards bereit:

**Installation:**

```bash
# Dashboard JSON herunterladen
curl -O https://raw.githubusercontent.com/temporalio/dashboards/main/grafana/temporal-sdk.json

# In Grafana importieren:
# Dashboards > Import > Upload JSON file
```

**Verfügbare Dashboards:**

1. **Temporal SDK Overview**
   - Workflow execution rates
   - Activity success/failure rates
   - Worker health
   - Task queue metrics

2. **Temporal Server**
   - Service health (Frontend, History, Matching, Worker)
   - Request rates und latency
   - Database performance
   - Resource usage

3. **Temporal Cloud**
   - Namespace metrics
   - API request rates
   - Workflow execution trends
   - Billing metrics

### 11.2.3 Custom Dashboard erstellen

**Panel 1: Workflow Execution Rate**

```json
{
  "title": "Workflow Execution Rate",
  "targets": [{
    "expr": "rate(temporal_workflow_task_execution_count{namespace=\"$namespace\"}[5m])",
    "legendFormat": "{{task_queue}}"
  }],
  "type": "graph"
}
```

**Panel 2: Activity Latency Heatmap**

```json
{
  "title": "Activity Latency Distribution",
  "targets": [{
    "expr": "rate(temporal_activity_execution_latency_seconds_bucket{activity_type=\"$activity\"}[5m])",
    "format": "heatmap"
  }],
  "type": "heatmap",
  "yAxis": { "format": "s" }
}
```

**Panel 3: Worker Task Slots**

```json
{
  "title": "Worker Task Slots",
  "targets": [
    {
      "expr": "temporal_worker_task_slots_available",
      "legendFormat": "Available - {{worker_id}}"
    },
    {
      "expr": "temporal_worker_task_slots_used",
      "legendFormat": "Used - {{worker_id}}"
    }
  ],
  "type": "graph",
  "stack": true
}
```

**Panel 4: Top Slowest Activities**

```json
{
  "title": "Top 10 Slowest Activities",
  "targets": [{
    "expr": "topk(10, avg(rate(temporal_activity_execution_latency_seconds_sum[5m])) by (activity_type))",
    "legendFormat": "{{activity_type}}",
    "instant": true
  }],
  "type": "table"
}
```

**Complete Dashboard Example** (kompakt):

```json
{
  "dashboard": {
    "title": "Temporal - Order Processing",
    "timezone": "browser",
    "templating": {
      "list": [
        {
          "name": "namespace",
          "type": "query",
          "query": "label_values(temporal_workflow_task_execution_count, namespace)"
        },
        {
          "name": "task_queue",
          "type": "query",
          "query": "label_values(temporal_workflow_task_execution_count{namespace=\"$namespace\"}, task_queue)"
        }
      ]
    },
    "panels": [
      {
        "title": "Workflow Execution Rate",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "targets": [{
          "expr": "rate(temporal_workflow_task_execution_count{namespace=\"$namespace\",task_queue=\"$task_queue\"}[5m])"
        }]
      },
      {
        "title": "Activity Success Rate",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        "targets": [{
          "expr": "rate(temporal_activity_execution_count{status=\"completed\"}[5m]) / rate(temporal_activity_execution_count[5m])"
        }]
      },
      {
        "title": "Task Queue Lag",
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8},
        "targets": [{
          "expr": "temporal_task_queue_lag_seconds{task_queue=\"$task_queue\"}"
        }]
      }
    ]
  }
}
```

### 11.2.4 Alerting in Grafana

**Alert 1: High Workflow Failure Rate**

```yaml
# Alert Definition
- alert: HighWorkflowFailureRate
  expr: |
    (
      rate(temporal_workflow_completed_count{status="failed"}[5m])
      /
      rate(temporal_workflow_completed_count[5m])
    ) > 0.05
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High workflow failure rate"
    description: "{{ $value | humanizePercentage }} of workflows are failing"
```

**Alert 2: Task Queue Backlog**

```yaml
- alert: TaskQueueBacklog
  expr: temporal_task_queue_lag_seconds > 300
  for: 10m
  labels:
    severity: critical
  annotations:
    summary: "Task queue has significant backlog"
    description: "Task queue {{ $labels.task_queue }} has {{ $value }}s lag"
```

**Alert 3: Worker Unavailable**

```yaml
- alert: WorkerUnavailable
  expr: up{job="temporal-workers"} == 0
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Worker is down"
    description: "Worker {{ $labels.instance }} is not responding"
```

**Alert 4: Activity Latency Spike**

```yaml
- alert: ActivityLatencySpike
  expr: |
    histogram_quantile(0.95,
      rate(temporal_activity_execution_latency_seconds_bucket[5m])
    ) > 60
  for: 5m
  labels:
    severity: warning
    activity_type: "{{ $labels.activity_type }}"
  annotations:
    summary: "Activity latency is high"
    description: "p95 latency for {{ $labels.activity_type }}: {{ $value }}s"
```

---

## 11.3 OpenTelemetry Integration

### 11.3.1 Warum OpenTelemetry?

**Prometheus + Grafana** geben Ihnen Metrics. Aber für **Distributed Tracing** brauchen Sie mehr:

- **End-to-End Traces**: Verfolgen Sie einen Request durch Ihr gesamtes System
- **Spans**: Sehen Sie, wie lange jede Activity dauert
- **Context Propagation**: Korrelieren Sie Logs, Metrics und Traces
- **Service Dependencies**: Visualisieren Sie, wie Services miteinander kommunizieren

**Use Case**: Ein Workflow ruft 5 verschiedene Microservices auf. Welcher Service verursacht die Latenz?

```
HTTP Request → API Gateway → Order Workflow
                                  ├─> Payment Service (500ms)
                                  ├─> Inventory Service (200ms)
                                  ├─> Shipping Service (3000ms) ← BOTTLENECK!
                                  ├─> Email Service (100ms)
                                  └─> Analytics Service (50ms)
```

Mit OpenTelemetry sehen Sie diese gesamte Kette als **einen zusammenhängenden Trace**.

### 11.3.2 OpenTelemetry Setup

**Dependencies:**

```bash
pip install opentelemetry-api opentelemetry-sdk \
    opentelemetry-instrumentation-temporal \
    opentelemetry-exporter-otlp
```

**Tracer Setup:**

```python
"""
OpenTelemetry Integration für Temporal

Chapter: 11 - Monitoring und Observability
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio import workflow, activity
import asyncio


def setup_telemetry(service_name: str):
    """Setup OpenTelemetry Tracing"""

    # Resource: Identifiziert diesen Service
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
        "deployment.environment": "production"
    })

    # Tracer Provider
    provider = TracerProvider(resource=resource)

    # OTLP Exporter (zu Tempo, Jaeger, etc.)
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://tempo:4317",
        insecure=True
    )

    # Batch Processor (für Performance)
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)

    # Global Tracer setzen
    trace.set_tracer_provider(provider)

    return trace.get_tracer(service_name)


# Tracer erstellen
tracer = setup_telemetry("order-service")


@activity.defn
async def process_payment(order_id: str, amount: float) -> dict:
    """Activity mit manual tracing"""

    # Span für diese Activity
    with tracer.start_as_current_span("process_payment") as span:

        # Span Attributes (Metadata)
        span.set_attribute("order_id", order_id)
        span.set_attribute("amount", amount)
        span.set_attribute("activity.type", "process_payment")

        # External Service Call tracen
        with tracer.start_as_current_span("call_payment_api") as api_span:
            api_span.set_attribute("http.method", "POST")
            api_span.set_attribute("http.url", "https://payment.api/charge")

            # Simulierter API Call
            await asyncio.sleep(0.5)

            api_span.set_attribute("http.status_code", 200)

        # Span Status
        span.set_status(trace.StatusCode.OK)

        return {
            "success": True,
            "transaction_id": f"txn_{order_id}"
        }


@workflow.defn
class OrderWorkflow:
    """Workflow mit Tracing"""

    @workflow.run
    async def run(self, order_id: str) -> dict:

        # Workflow-Context als Span
        # (automatisch durch Temporal SDK + OpenTelemetry Instrumentation)

        workflow.logger.info(f"Processing order {order_id}")

        # Activities werden automatisch als Child Spans getrackt
        payment = await workflow.execute_activity(
            process_payment,
            args=[order_id, 99.99],
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Weitere Activities...

        return {"status": "completed", "payment": payment}
```

### 11.3.3 Automatic Instrumentation

**Einfachere Alternative**: Temporal SDK Instrumentation (experimentell):

```python
from opentelemetry.instrumentation.temporal import TemporalInstrumentor

# Automatische Instrumentation
TemporalInstrumentor().instrument()

# Jetzt werden Workflows und Activities automatisch getrackt
client = await Client.connect("localhost:7233")
```

**Was wird automatisch getrackt:**

- Workflow Start/Complete
- Activity Execution
- Task Queue Operations
- Signals/Queries
- Child Workflows

### 11.3.4 Tempo + Grafana Setup

**Docker Compose:**

```yaml
version: '3.8'

services:
  tempo:
    image: grafana/tempo:latest
    command: ["-config.file=/etc/tempo.yaml"]
    ports:
      - "4317:4317"  # OTLP gRPC
      - "4318:4318"  # OTLP HTTP
      - "3200:3200"  # Tempo Query Frontend
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml
      - tempo-data:/var/tempo

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
    volumes:
      - ./grafana-datasources.yaml:/etc/grafana/provisioning/datasources/datasources.yaml

volumes:
  tempo-data:
```

**tempo.yaml:**

```yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: "0.0.0.0:4317"
        http:
          endpoint: "0.0.0.0:4318"

storage:
  trace:
    backend: local
    local:
      path: /var/tempo/traces

query_frontend:
  search:
    enabled: true
```

**grafana-datasources.yaml:**

```yaml
apiVersion: 1

datasources:
  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    isDefault: false
```

### 11.3.5 Trace Visualisierung

**In Grafana Explore:**

```
1. Data Source: Tempo
2. Query: trace_id = "abc123..."
3. Visualisierung:

   OrderWorkflow                     [========== 5.2s ==========]
   ├─ process_payment               [=== 0.5s ===]
   │  └─ call_payment_api          [== 0.48s ==]
   ├─ check_inventory               [= 0.2s =]
   ├─ create_shipment              [======== 3.0s ========] ← SLOW!
   ├─ send_confirmation_email      [= 0.1s =]
   └─ update_analytics             [= 0.05s =]
```

**Trace Search Queries:**

```
# Alle Traces für einen Workflow
service.name="order-service" && workflow.type="OrderWorkflow"

# Langsame Traces (> 5s)
service.name="order-service" && duration > 5s

# Fehlerhafte Traces
status=error

# Traces für bestimmte Order
order_id="order-12345"
```

### 11.3.6 Correlation: Metrics + Logs + Traces

**Das Problem**: Metrics zeigen ein Problem, aber Sie brauchen Details.

**Lösung**: Exemplars + Trace IDs in Logs

**Prometheus Exemplars:**

```python
from prometheus_client import Histogram
from opentelemetry import trace

# Histogram mit Exemplar Support
activity_latency = Histogram(
    'activity_execution_seconds',
    'Activity execution time'
)

@activity.defn
async def my_activity():
    start = time.time()

    # ... Activity Logic ...

    latency = time.time() - start

    # Metric + Trace ID als Exemplar
    current_span = trace.get_current_span()
    trace_id = current_span.get_span_context().trace_id

    activity_latency.observe(
        latency,
        exemplar={'trace_id': format(trace_id, '032x')}
    )
```

**In Grafana**: Click auf Metric Point → Jump zu Trace!

**Structured Logging mit Trace Context:**

```python
import logging
from opentelemetry import trace

logger = logging.getLogger(__name__)

@activity.defn
async def my_activity(order_id: str):

    # Trace Context extrahieren
    span = trace.get_current_span()
    trace_id = format(span.get_span_context().trace_id, '032x')
    span_id = format(span.get_span_context().span_id, '016x')

    # Structured Log mit Trace IDs
    logger.info(
        "Processing order",
        extra={
            "order_id": order_id,
            "trace_id": trace_id,
            "span_id": span_id,
            "workflow_id": activity.info().workflow_id,
            "activity_type": activity.info().activity_type
        }
    )
```

**Log Output (JSON):**

```json
{
  "timestamp": "2025-01-19T10:30:45Z",
  "level": "INFO",
  "message": "Processing order",
  "order_id": "order-12345",
  "trace_id": "a1b2c3d4e5f6...",
  "span_id": "789abc...",
  "workflow_id": "order-workflow-12345",
  "activity_type": "process_payment"
}
```

**In Grafana Loki**: Search for `trace_id="a1b2c3d4e5f6..."` → Alle Logs für diesen Trace!

---

## 11.4 Logging Best Practices

### 11.4.1 Structured Logging Setup

**Warum Structured Logging?**

**Unstructured** (schlecht):
```python
logger.info(f"Order {order_id} completed in {duration}s")
```

**Structured** (gut):
```python
logger.info("Order completed", extra={
    "order_id": order_id,
    "duration_seconds": duration,
    "status": "success"
})
```

**Vorteile:**
- Suchbar nach Feldern
- Aggregierbar
- Maschinenlesbar
- Integriert mit Observability Tools

**Python Setup mit `structlog`:**

```python
import structlog
from temporalio import activity, workflow

# Structlog konfigurieren
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


@activity.defn
async def process_order(order_id: str):
    """Activity mit strukturiertem Logging"""

    # Workflow Context hinzufügen
    log = logger.bind(
        workflow_id=activity.info().workflow_id,
        activity_id=activity.info().activity_id,
        activity_type="process_order",
        order_id=order_id
    )

    log.info("activity_started")

    try:
        # Business Logic
        result = await do_something(order_id)

        log.info(
            "activity_completed",
            result=result,
            duration_ms=123
        )

        return result

    except Exception as e:
        log.error(
            "activity_failed",
            error=str(e),
            error_type=type(e).__name__
        )
        raise
```

**Log Output:**

```json
{
  "timestamp": "2025-01-19T10:30:45.123456Z",
  "level": "info",
  "event": "activity_started",
  "workflow_id": "order-workflow-abc",
  "activity_id": "activity-xyz",
  "activity_type": "process_order",
  "order_id": "order-12345"
}

{
  "timestamp": "2025-01-19T10:30:45.345678Z",
  "level": "info",
  "event": "activity_completed",
  "workflow_id": "order-workflow-abc",
  "activity_id": "activity-xyz",
  "result": "success",
  "duration_ms": 123,
  "order_id": "order-12345"
}
```

### 11.4.2 Temporal Logger Integration

**Temporal SDK Logger nutzen:**

```python
from temporalio import workflow, activity


@workflow.defn
class MyWorkflow:

    @workflow.run
    async def run(self):
        # Temporal Workflow Logger (automatisch mit Context)
        workflow.logger.info(
            "Workflow started",
            extra={"custom_field": "value"}
        )

        # Logging ist replay-safe!
        # Logs werden nur bei echter Execution ausgegeben


@activity.defn
async def my_activity():
    # Temporal Activity Logger (automatisch mit Context)
    activity.logger.info(
        "Activity started",
        extra={"custom_field": "value"}
    )
```

**Automatischer Context:**

Temporal Logger fügen automatisch hinzu:
- `workflow_id`
- `workflow_type`
- `run_id`
- `activity_id`
- `activity_type`
- `namespace`
- `task_queue`

### 11.4.3 Log Aggregation mit Loki

**Loki Setup:**

```yaml
# docker-compose.yml
services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yaml:/etc/loki/local-config.yaml
      - loki-data:/loki

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log
      - ./promtail-config.yaml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
```

**loki-config.yaml:**

```yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/cache
  filesystem:
    directory: /loki/chunks
```

**promtail-config.yaml:**

```yaml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: temporal-workers
    static_configs:
      - targets:
          - localhost
        labels:
          job: temporal-workers
          __path__: /var/log/temporal-worker/*.log

    # JSON Log Parsing
    pipeline_stages:
      - json:
          expressions:
            timestamp: timestamp
            level: level
            message: event
            workflow_id: workflow_id
            activity_type: activity_type
      - labels:
          level:
          workflow_id:
          activity_type:
      - timestamp:
          source: timestamp
          format: RFC3339
```

**LogQL Queries in Grafana:**

```logql
# Alle Logs für einen Workflow
{job="temporal-workers"} | json | workflow_id="order-workflow-abc"

# Fehler-Logs
{job="temporal-workers"} | json | level="error"

# Langsame Activities (> 5s)
{job="temporal-workers"}
  | json
  | duration_ms > 5000
  | line_format "{{.activity_type}}: {{.duration_ms}}ms"

# Rate von Errors
rate({job="temporal-workers"} | json | level="error" [5m])

# Top Activities nach Count
topk(10,
  sum by (activity_type) (
    count_over_time({job="temporal-workers"} | json [1h])
  )
)
```

### 11.4.4 Best Practices

**DO:**
- ✅ Strukturierte Logs (JSON)
- ✅ Correlation IDs (workflow_id, trace_id)
- ✅ Log Level appropriate nutzen (DEBUG, INFO, WARN, ERROR)
- ✅ Performance-relevante Metrics loggen
- ✅ Business Events loggen
- ✅ Fehler mit Context loggen

**DON'T:**
- ❌ Sensitive Daten loggen (Passwords, PII, Credit Cards)
- ❌ Zu viel loggen (Performance-Impact)
- ❌ Unstrukturierte Logs
- ❌ Logging in Workflows ohne Replay-Safety

**Replay-Safe Logging:**

```python
@workflow.defn
class MyWorkflow:

    @workflow.run
    async def run(self):
        # FALSCH: Logging ohne Replay-Check
        print(f"Workflow started at {datetime.now()}")  # ❌ Non-deterministic!

        # RICHTIG: Temporal Logger (replay-safe)
        workflow.logger.info("Workflow started")  # ✅ Nur bei echter Execution
```

**Sensitive Data redaktieren:**

```python
import re

def redact_sensitive(data: dict) -> dict:
    """Redact sensitive fields"""
    sensitive_fields = ['password', 'credit_card', 'ssn', 'api_key']

    redacted = data.copy()
    for key in redacted:
        if any(field in key.lower() for field in sensitive_fields):
            redacted[key] = "***REDACTED***"

    return redacted


@activity.defn
async def process_payment(payment_data: dict):
    # Log mit redaktierten Daten
    activity.logger.info(
        "Processing payment",
        extra=redact_sensitive(payment_data)
    )
```

---

## 11.5 SLO-basiertes Alerting

### 11.5.1 Was sind SLIs, SLOs, SLAs?

**SLI (Service Level Indicator)**: Messgröße für Service-Qualität
- Beispiel: "99.5% der Workflows werden erfolgreich abgeschlossen"

**SLO (Service Level Objective)**: Ziel für SLI
- Beispiel: "SLO: 99.9% Workflow Success Rate"

**SLA (Service Level Agreement)**: Vertragliche Vereinbarung
- Beispiel: "SLA: 99.5% Uptime mit finanziellen Konsequenzen"

**Verhältnis**: SLI ≤ SLO ≤ SLA

### 11.5.2 SLIs für Temporal Workflows

**Request Success Rate** (wichtigster SLI):

```promql
# Workflow Success Rate
sum(rate(temporal_workflow_completed_count{status="completed"}[5m]))
  /
sum(rate(temporal_workflow_completed_count[5m]))
```

**Latency** (p50, p95, p99):

```promql
# Workflow p95 Latency
histogram_quantile(0.95,
  rate(temporal_workflow_execution_latency_seconds_bucket[5m])
)
```

**Availability**:

```promql
# Worker Availability
avg(up{job="temporal-workers"})
```

**Beispiel SLOs:**

| SLI | SLO | Messung |
|-----|-----|---------|
| Workflow Success Rate | ≥ 99.9% | Last 30d |
| Order Workflow p95 Latency | ≤ 5s | Last 1h |
| Worker Availability | ≥ 99.5% | Last 30d |
| Task Queue Lag | ≤ 30s | Last 5m |

### 11.5.3 Error Budget

**Konzept**: Wie viel "Failure" ist erlaubt?

**Berechnung:**

```
Error Budget = 100% - SLO
```

**Beispiel:**

```
SLO: 99.9% Success Rate
Error Budget: 0.1% = 1 von 1000 Requests darf fehlschlagen

Bei 1M Workflows/Monat:
Error Budget = 1M * 0.001 = 1,000 erlaubte Failures
```

**Error Budget Tracking:**

```promql
# Verbleibender Error Budget (30d window)
(
  1 - (
    sum(increase(temporal_workflow_completed_count{status="completed"}[30d]))
    /
    sum(increase(temporal_workflow_completed_count[30d]))
  )
) / 0.001  # 0.001 = Error Budget für 99.9% SLO
```

**Interpretation:**

```
Result = 0.5  → 50% Error Budget verbraucht ✅
Result = 0.9  → 90% Error Budget verbraucht ⚠️
Result = 1.2  → 120% Error Budget verbraucht ❌ SLO missed!
```

### 11.5.4 Multi-Window Multi-Burn-Rate Alerts

**Problem mit einfachen Alerts:**

```yaml
# Zu simpel
- alert: HighErrorRate
  expr: error_rate > 0.01
  for: 5m
```

**Probleme:**
- Flapping bei kurzen Spikes
- Langsame Reaktion bei echten Problemen
- Keine Unterscheidung: Kurzer Spike vs. anhaltender Ausfall

**Lösung: Multi-Window Alerts** (aus Google SRE Workbook)

**Konzept:**

| Severity | Burn Rate | Short Window | Long Window | Alert |
|----------|-----------|--------------|-------------|-------|
| Critical | 14.4x | 1h | 5m | Page immediately |
| High | 6x | 6h | 30m | Page during business hours |
| Medium | 3x | 1d | 2h | Ticket |
| Low | 1x | 3d | 6h | No alert |

**Implementation:**

```yaml
groups:
  - name: temporal_slo_alerts
    rules:
      # Critical: 14.4x burn rate (1h budget in 5m)
      - alert: WorkflowSLOCritical
        expr: |
          (
            (1 - (
              sum(rate(temporal_workflow_completed_count{status="completed"}[1h]))
              /
              sum(rate(temporal_workflow_completed_count[1h]))
            )) > (14.4 * 0.001)
          )
          and
          (
            (1 - (
              sum(rate(temporal_workflow_completed_count{status="completed"}[5m]))
              /
              sum(rate(temporal_workflow_completed_count[5m]))
            )) > (14.4 * 0.001)
          )
        labels:
          severity: critical
        annotations:
          summary: "Critical: Workflow SLO burn rate too high"
          description: "Error budget will be exhausted in < 2 days at current rate"

      # High: 6x burn rate
      - alert: WorkflowSLOHigh
        expr: |
          (
            (1 - (
              sum(rate(temporal_workflow_completed_count{status="completed"}[6h]))
              /
              sum(rate(temporal_workflow_completed_count[6h]))
            )) > (6 * 0.001)
          )
          and
          (
            (1 - (
              sum(rate(temporal_workflow_completed_count{status="completed"}[30m]))
              /
              sum(rate(temporal_workflow_completed_count[30m]))
            )) > (6 * 0.001)
          )
        labels:
          severity: warning
        annotations:
          summary: "High: Workflow SLO burn rate elevated"
          description: "Error budget will be exhausted in < 5 days at current rate"

      # Medium: 3x burn rate
      - alert: WorkflowSLOMedium
        expr: |
          (
            (1 - (
              sum(rate(temporal_workflow_completed_count{status="completed"}[1d]))
              /
              sum(rate(temporal_workflow_completed_count[1d]))
            )) > (3 * 0.001)
          )
          and
          (
            (1 - (
              sum(rate(temporal_workflow_completed_count{status="completed"}[2h]))
              /
              sum(rate(temporal_workflow_completed_count[2h]))
            )) > (3 * 0.001)
          )
        labels:
          severity: info
        annotations:
          summary: "Medium: Workflow SLO burn rate concerning"
          description: "Error budget will be exhausted in < 10 days at current rate"
```

### 11.5.5 Activity-Specific SLOs

**Nicht alle Activities sind gleich wichtig!**

**Beispiel:**

```yaml
# Critical Activity: Payment Processing
- alert: PaymentActivitySLOBreach
  expr: |
    (
      sum(rate(temporal_activity_execution_count{
        activity_type="process_payment",
        status="completed"
      }[5m]))
      /
      sum(rate(temporal_activity_execution_count{
        activity_type="process_payment"
      }[5m]))
    ) < 0.999  # 99.9% SLO
  for: 5m
  labels:
    severity: critical
    activity: process_payment
  annotations:
    summary: "Payment activity SLO breach"
    description: "Success rate: {{ $value | humanizePercentage }}"

# Low-Priority Activity: Analytics Update
- alert: AnalyticsActivitySLOBreach
  expr: |
    (
      sum(rate(temporal_activity_execution_count{
        activity_type="update_analytics",
        status="completed"
      }[30m]))
      /
      sum(rate(temporal_activity_execution_count{
        activity_type="update_analytics"
      }[30m]))
    ) < 0.95  # 95% SLO (relaxed)
  for: 30m
  labels:
    severity: warning
    activity: update_analytics
  annotations:
    summary: "Analytics activity degraded"
```

### 11.5.6 Alertmanager Configuration

**alertmanager.yml:**

```yaml
global:
  slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'

route:
  receiver: 'default'
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 4h

  routes:
    # Critical alerts → PagerDuty
    - match:
        severity: critical
      receiver: pagerduty
      continue: true

    # Critical alerts → Slack #alerts
    - match:
        severity: critical
      receiver: slack-critical

    # Warnings → Slack #monitoring
    - match:
        severity: warning
      receiver: slack-monitoring

    # Info → Slack #monitoring (low priority)
    - match:
        severity: info
      receiver: slack-monitoring
      group_wait: 5m
      repeat_interval: 12h

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#monitoring'
        title: 'Temporal Alert'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'slack-critical'
    slack_configs:
      - channel: '#alerts'
        title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        color: 'danger'

  - name: 'slack-monitoring'
    slack_configs:
      - channel: '#monitoring'
        title: '⚠️  {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        color: 'warning'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
```

---

## 11.6 Temporal Cloud Observability

### 11.6.1 Cloud Metrics Zugriff

**Temporal Cloud bietet zwei Metrics Endpoints:**

1. **Prometheus Endpoint** (Scraping):
```
https://cloud-metrics.temporal.io/prometheus/<account-id>/<namespace>
```

2. **PromQL Endpoint** (Querying):
```
https://cloud-metrics.temporal.io/api/v1/query
```

**Authentication:**

```bash
# API Key generieren (Temporal Cloud UI)
# Settings > Integrations > Prometheus

# Metrics abrufen
curl -H "Authorization: Bearer <API_KEY>" \
  https://cloud-metrics.temporal.io/prometheus/<account-id>/<namespace>/metrics
```

### 11.6.2 Prometheus Scrape Config

```yaml
scrape_configs:
  - job_name: 'temporal-cloud'
    scheme: https
    static_configs:
      - targets:
          - 'cloud-metrics.temporal.io'
    authorization:
      credentials: '<YOUR_API_KEY>'
    params:
      account: ['<account-id>']
      namespace: ['<namespace>']
    scrape_interval: 60s  # Cloud Metrics: Max 1/minute
```

### 11.6.3 Verfügbare Cloud Metrics

**Namespace Metrics:**

```promql
# Workflow Execution Rate
temporal_cloud_v0_workflow_started

# Workflow Success/Failure
temporal_cloud_v0_workflow_success
temporal_cloud_v0_workflow_failed

# Active Workflows
temporal_cloud_v0_workflow_running

# Task Queue Depth
temporal_cloud_v0_task_queue_depth{task_queue="order-processing"}
```

**Resource Metrics:**

```promql
# Actions per Second (Billing)
temporal_cloud_v0_resource_actions_count

# Storage Usage
temporal_cloud_v0_resource_storage_bytes
```

### 11.6.4 Grafana Dashboard für Cloud

**Cloud-specific Dashboard:**

```json
{
  "title": "Temporal Cloud Overview",
  "panels": [
    {
      "title": "Workflow Start Rate",
      "targets": [{
        "expr": "rate(temporal_cloud_v0_workflow_started[5m])",
        "legendFormat": "{{namespace}}"
      }]
    },
    {
      "title": "Workflow Success Rate",
      "targets": [{
        "expr": "rate(temporal_cloud_v0_workflow_success[5m]) / rate(temporal_cloud_v0_workflow_started[5m])",
        "legendFormat": "Success Rate"
      }]
    },
    {
      "title": "Active Workflows",
      "targets": [{
        "expr": "temporal_cloud_v0_workflow_running",
        "legendFormat": "{{workflow_type}}"
      }]
    },
    {
      "title": "Actions per Second (Billing)",
      "targets": [{
        "expr": "rate(temporal_cloud_v0_resource_actions_count[5m])",
        "legendFormat": "Actions/s"
      }]
    }
  ]
}
```

### 11.6.5 SDK Metrics vs. Cloud Metrics

**Wichtig**: Verwenden Sie die richtige Metrik-Quelle!

| Use Case | Source | Warum |
|----------|--------|-------|
| "Wie lange dauert meine Activity?" | SDK Metrics | Misst aus Worker-Sicht |
| "Wie viele Workflows sind aktiv?" | Cloud Metrics | Server-seitige Sicht |
| "Ist mein Worker überlastet?" | SDK Metrics | Worker-spezifisch |
| "Task Queue Backlog?" | Cloud Metrics | Server-seitiger Zustand |
| "Billing/Cost?" | Cloud Metrics | Nur Cloud kennt Actions |

**Best Practice**: Beide kombinieren!

```promql
# Workflow End-to-End Latency (Cloud)
temporal_cloud_v0_workflow_execution_time

# Activity Latency within Workflow (SDK)
temporal_activity_execution_latency_seconds{activity_type="process_payment"}
```

---

## 11.7 Debugging mit Observability

### 11.7.1 Problem → Metrics → Traces → Logs

**Workflow**: Von groß zu klein

```
1. Metrics: "Payment workflows sind langsam (p95: 30s statt 5s)"
   ↓
2. Traces: "process_payment Activity dauert 25s"
   ↓
3. Logs: "Connection timeout zu payment.api.com"
   ↓
4. Root Cause: Payment API ist down
```

**Grafana Workflow:**

```
1. Öffne Dashboard "Temporal - Orders"
2. Panel "Activity Latency" zeigt Spike
3. Click auf Spike → "View Traces"
4. Trace zeigt: "process_payment span: 25s"
5. Click auf Span → "View Logs"
6. Log: "ERROR: connection timeout after 20s"
```

### 11.7.2 Temporal Web UI Integration

**Web UI**: `https://cloud.temporal.io` oder `http://localhost:8080`

**Features:**
- Workflow Execution History
- Event Timeline
- Pending Activities
- Stack Traces
- Retry History

**Von Grafana zu Web UI:**

```
Grafana Alert: "Workflow order-workflow-abc failed"
  ↓
Annotation Link: https://cloud.temporal.io/namespaces/default/workflows/order-workflow-abc
  ↓
Web UI: Zeigt komplette Workflow History
```

**Grafana Annotation Setup:**

```python
import requests

def send_workflow_annotation(workflow_id: str, message: str):
    """Send Grafana annotation for workflow event"""

    requests.post(
        'http://grafana:3000/api/annotations',
        json={
            'text': message,
            'tags': ['temporal', 'workflow', workflow_id],
            'time': int(time.time() * 1000),  # Unix timestamp ms
        },
        headers={
            'Authorization': 'Bearer <GRAFANA_API_KEY>',
            'Content-Type': 'application/json'
        }
    )


@activity.defn
async def critical_activity():
    workflow_id = activity.info().workflow_id

    try:
        result = await do_something()
        send_workflow_annotation(
            workflow_id,
            f"✓ Critical activity completed"
        )
        return result
    except Exception as e:
        send_workflow_annotation(
            workflow_id,
            f"❌ Critical activity failed: {e}"
        )
        raise
```

### 11.7.3 Correlation Queries

**Problem**: Metrics/Traces/Logs sind isoliert.

**Lösung**: Queries mit Correlation IDs.

**Find all data for a workflow:**

```bash
# 1. Prometheus: Get workflow start time
workflow_start_time=$(
  promtool query instant \
    'temporal_workflow_started_time{workflow_id="order-abc"}'
)

# 2. Tempo: Find traces for workflow
curl -G http://tempo:3200/api/search \
  --data-urlencode 'q={workflow_id="order-abc"}'

# 3. Loki: Find logs for workflow
curl -G http://loki:3100/loki/api/v1/query_range \
  --data-urlencode 'query={job="workers"} | json | workflow_id="order-abc"' \
  --data-urlencode "start=$workflow_start_time"
```

**In Grafana Explore** (einfacher):

```
1. Data Source: Prometheus
2. Query: temporal_workflow_started{workflow_id="order-abc"}
3. Click auf Datapoint → "View in Tempo"
4. Trace öffnet sich → Click auf Span → "View in Loki"
5. Logs erscheinen für diesen Span
```

### 11.7.4 Common Debugging Scenarios

**Scenario 1: "Workflows are slow"**

```
1. Check: Workflow p95 latency metric
   → Which workflow type is slow?

2. Check: Activity latency breakdown
   → Which activity is the bottleneck?

3. Check: Traces for slow workflow instances
   → Is it always slow or intermittent?

4. Check: Logs for slow activity executions
   → What error/timeout is occurring?

5. Check: External service metrics
   → Is downstream service degraded?
```

**Scenario 2: "High failure rate"**

```
1. Check: Workflow failure rate by type
   → Which workflow is failing?

2. Check: Activity failure rate
   → Which activity is failing?

3. Check: Error logs
   → What error messages appear?

4. Check: Temporal Web UI
   → Look at failed workflow history

5. Check: Deployment timeline
   → Did failure start after deployment?
```

**Scenario 3: "Task queue is backing up"**

```
1. Check: Task queue lag metric
   → How large is the backlog?

2. Check: Worker availability
   → Are workers up?

3. Check: Worker task slots
   → Are workers saturated?

4. Check: Activity execution rate
   → Is processing rate dropping?

5. Check: Worker logs
   → Are workers crashing/restarting?
```

---

## 11.8 Zusammenfassung

### Was Sie gelernt haben

**SDK Metrics:**
- ✅ Prometheus Export aus Python Workers konfigurieren
- ✅ Wichtige Metrics: Workflow/Activity Rate, Latency, Success Rate
- ✅ Custom Business Metrics in Activities
- ✅ Prometheus Scraping für Kubernetes

**Grafana:**
- ✅ Community Dashboards installieren
- ✅ Custom Dashboards erstellen
- ✅ PromQL Queries für Temporal Metrics
- ✅ Alerting Rules definieren

**OpenTelemetry:**
- ✅ Distributed Tracing Setup
- ✅ Automatic Instrumentation für Workflows
- ✅ Manual Spans in Activities
- ✅ Tempo Integration
- ✅ Correlation: Metrics + Traces + Logs

**Logging:**
- ✅ Structured Logging mit `structlog`
- ✅ Temporal Logger mit Auto-Context
- ✅ Loki für Log Aggregation
- ✅ LogQL Queries
- ✅ Replay-Safe Logging

**SLO-basiertes Alerting:**
- ✅ SLI/SLO/SLA Konzepte
- ✅ Error Budget Tracking
- ✅ Multi-Window Multi-Burn-Rate Alerts
- ✅ Activity-specific SLOs
- ✅ Alertmanager Configuration

**Temporal Cloud:**
- ✅ Cloud Metrics API
- ✅ Prometheus Scraping
- ✅ SDK vs. Cloud Metrics
- ✅ Billing Metrics

**Debugging:**
- ✅ Von Metrics zu Traces zu Logs
- ✅ Temporal Web UI Integration
- ✅ Correlation Queries
- ✅ Common Debugging Scenarios

### Production Checklist

**Monitoring Setup:**

- [ ] SDK Metrics Export konfiguriert
- [ ] Prometheus scraping Workers
- [ ] Grafana Dashboards deployed
- [ ] Alerting Rules definiert
- [ ] Alertmanager konfiguriert (Slack/PagerDuty)
- [ ] On-Call Rotation definiert

**Observability:**

- [ ] Structured Logging implementiert
- [ ] Log Aggregation (Loki/ELK) läuft
- [ ] OpenTelemetry Tracing aktiviert
- [ ] Trace Backend (Tempo/Jaeger) deployed
- [ ] Correlation IDs in allen Logs

**SLOs:**

- [ ] SLIs für kritische Workflows definiert
- [ ] SLOs festgelegt (99.9%? 99.5%?)
- [ ] Error Budget Dashboard erstellt
- [ ] Multi-Burn-Rate Alerts konfiguriert
- [ ] Activity-specific SLOs dokumentiert

**Dashboards:**

- [ ] Workflow Overview Dashboard
- [ ] Worker Health Dashboard
- [ ] Activity Performance Dashboard
- [ ] Business Metrics Dashboard
- [ ] SLO Tracking Dashboard

**Alerts:**

- [ ] High Workflow Failure Rate
- [ ] Task Queue Backlog
- [ ] Worker Unavailable
- [ ] Activity Latency Spike
- [ ] SLO Burn Rate Critical
- [ ] Error Budget Exhausted

### Häufige Fehler

❌ **Zu wenig monitoren**
```
Problem: Nur Server-Metrics, keine SDK Metrics
Folge: Keine Sicht auf Ihre Application-Performance
```

✅ **Richtig:**
```
Beide monitoren: Server + SDK Metrics
SDK Metrics = Source of Truth für Application Performance
```

❌ **Nur Metrics, keine Traces**
```
Problem: Wissen, dass es langsam ist, aber nicht wo
Folge: Debugging dauert Stunden
```

✅ **Richtig:**
```
Metrics → Traces → Logs Pipeline
Correlation IDs überall
```

❌ **Alert Fatigue**
```
Problem: 100 Alerts pro Tag
Folge: Wichtige Alerts werden ignoriert
```

✅ **Richtig:**
```
SLO-basiertes Alerting
Multi-Burn-Rate Alerts (weniger False Positives)
Alert nur auf SLO-Verletzungen
```

❌ **Keine Correlation**
```
Problem: Metrics, Logs, Traces sind isoliert
Folge: Müssen manuell korrelieren
```

✅ **Richtig:**
```
Exemplars in Metrics
Trace IDs in Logs
Grafana-Integration
```

### Best Practices

1. **Metriken hierarchisch organisieren**
   ```
   System Metrics (Server CPU, Memory)
     → Temporal Metrics (Workflows, Activities)
       → Business Metrics (Orders, Revenue)
   ```

2. **Alerts nach Severity gruppieren**
   ```
   Critical → Page immediately (SLO breach)
   Warning → Page during business hours
   Info → Ticket for next sprint
   ```

3. **Dashboards für Rollen**
   ```
   Executive: Business KPIs (Orders/hour, Revenue)
   Engineering: Technical Metrics (Latency, Error Rate)
   SRE: Operational (Worker Health, Queue Depth)
   On-Call: Incident Response (Recent Alerts, Anomalies)
   ```

4. **Retention Policies**
   ```
   Metrics: 30 days high-res, 1 year downsampled
   Logs: 7 days full, 30 days search indices
   Traces: 7 days (sampling: 10% background, 100% errors)
   ```

5. **Cost Optimization**
   ```
   - Use sampling for traces (not every request)
   - Downsample old metrics
   - Compress logs
   - Use Cloud Metrics API efficiently (max 1 req/min)
   ```

### Weiterführende Ressourcen

**Temporal Docs:**
- [Observability Guide](https://docs.temporal.io/develop/python/observability)
- [Cloud Metrics API](https://docs.temporal.io/cloud/metrics)
- [Prometheus Setup](https://docs.temporal.io/self-hosted-guide/monitoring)

**Grafana:**
- [Community Dashboards](https://github.com/temporalio/dashboards)
- [Grafana Docs](https://grafana.com/docs/)

**OpenTelemetry:**
- [Python Instrumentation](https://opentelemetry.io/docs/instrumentation/python/)
- [Temporal OTel Guide](https://docs.temporal.io/develop/python/observability#opentelemetry)

**SRE:**
- [Google SRE Book - Monitoring](https://sre.google/sre-book/monitoring-distributed-systems/)
- [SRE Workbook - Alerting](https://sre.google/workbook/alerting-on-slos/)

### Nächste Schritte

Sie können jetzt Production-ready Monitoring aufsetzen! Aber Observability ist nur ein Teil des Betriebsalltags.

**Weiter geht's mit:**

- **Kapitel 12: Testing Strategies** – Wie Sie Workflows umfassend testen
- **Kapitel 13: Best Practices und Anti-Muster** – Production-ready Temporal-Anwendungen
- **Kapitel 14-15: Kochbuch** – Konkrete Patterns und Rezepte für häufige Use Cases

---

**[⬆ Zurück zum Inhaltsverzeichnis](README.md)**

**Nächstes Kapitel**: [Kapitel 12: Testing Strategies](part-04-chapter-12.md)

**Code-Beispiele für dieses Kapitel**: [`examples/part-04/chapter-11/`](../examples/part-04/chapter-11/)

**💡 Tipp**: Monitoring ist nicht "set and forget". Review your dashboards and alerts regularly:
- Monatlich: SLO Review (wurden sie eingehalten?)
- Quarterly: Alert Review (zu viele False Positives?)
- Nach Incidents: Post-Mortem → Update Alerts/Dashboards
