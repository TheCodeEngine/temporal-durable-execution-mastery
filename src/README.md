# Temporal.io – Durable Execution Mastery

**Ein umfassender Deep Dive in die Orchestrierung verteilter Systeme mit Temporal**

## Über dieses Buch

Dieses Buch bietet eine vollständige Einführung in Temporal.io, die führende Plattform für Durable Execution. Sie lernen, wie Sie zuverlässige, skalierbare und wartbare verteilte Systeme entwickeln, indem Sie komplexe Workflows als einfachen Code schreiben.

Das Buch kombiniert theoretische Grundlagen mit praktischen Python-Beispielen, die Sie direkt ausführen können. Jedes Kapitel enthält lauffähige Code-Beispiele, die Temporal-Konzepte demonstrieren.

## Voraussetzungen

- Python 3.13+
- uv package manager
- Temporal CLI oder Docker (für lokale Entwicklung)
- Grundkenntnisse in Python und verteilten Systemen

## Schnellstart

```bash
# Repository klonen
git clone https://github.com/your-org/temporal-book.git
cd temporal-book

# Beispiel ausführen (z.B. Kapitel 1)
cd part-i-grundlagen/examples/chapter-01
uv sync
uv run python simple_workflow.py
```

## Inhaltsverzeichnis

### Teil I: Grundlagen der Durable Execution

Lernen Sie die Kernkonzepte von Temporal kennen und verstehen Sie, warum Durable Execution die Zukunft verteilter Systeme ist.

- [Kapitel 1: Einführung in Temporal](./part-i-grundlagen/chapter-01.md)
- [Kapitel 2: Kernbausteine: Workflows, Activities, Worker](./part-i-grundlagen/chapter-02.md)
- [Kapitel 3: Architektur des Temporal Service](./part-i-grundlagen/chapter-03.md)

### Teil II: Entwicklung von Temporal-Anwendungen (SDK-Fokus)

Tauchen Sie ein in die praktische Entwicklung mit dem Temporal Python SDK.

- [Kapitel 4: Entwicklungs-Setup und SDK-Auswahl](./part-ii-sdk-fokus/chapter-04.md)
- [Kapitel 5: Workflows programmieren](./part-ii-sdk-fokus/chapter-05.md)
- [Kapitel 6: Kommunikation (Signale und Queries)](./part-ii-sdk-fokus/chapter-06.md)

### Teil III: Resilienz, Evolution und Muster

Meistern Sie fortgeschrittene Muster für robuste, evolvierbare Systeme.

- [Kapitel 7: Fehlerbehandlung und Retries](./part-iii-resilienz/chapter-07.md)
- [Kapitel 8: SAGA Pattern](./part-iii-resilienz/chapter-08.md)
- [Kapitel 9: Workflow-Evolution und Versionierung](./part-iii-resilienz/chapter-09.md)

### Teil IV: Betrieb, Skalierung und Best Practices

Bringen Sie Ihre Temporal-Anwendungen in die Produktion.

- [Kapitel 10: Produktions-Deployment](./part-iv-betrieb/chapter-10.md)
- [Kapitel 11: Skalierung der Worker](./part-iv-betrieb/chapter-11.md)
- [Kapitel 12: Observability und Monitoring](./part-iv-betrieb/chapter-12.md)
- [Kapitel 13: Best Practices und Anti-Muster](./part-iv-betrieb/chapter-13.md)

### Teil V: Das Temporal Kochbuch

Praktische Rezepte für häufige Anwendungsfälle.

- [Kapitel 14: Muster-Rezepte (Human-in-Loop, Cron, Order Fulfillment)](./part-v-kochbuch/chapter-14.md)
- [Kapitel 15: Erweiterte Rezepte (AI Agents, Lambda, Polyglot)](./part-v-kochbuch/chapter-15.md)

## Projektstruktur

```
temporal-book/
├── README.md                          # Dieses Dokument
├── shared/                            # Gemeinsame Utilities für alle Beispiele
│   ├── temporal_helpers.py            # Temporal Client Setup
│   └── examples_common.py             # Gemeinsame Hilfsfunktionen
│
├── part-i-grundlagen/                 # Teil I
│   ├── chapter-01.md                  # Kapitel-Inhalte
│   ├── examples/                      # Python-Beispiele
│   │   └── chapter-01/
│   │       ├── pyproject.toml
│   │       ├── .python-version
│   │       └── *.py
│   └── assets/                        # Bilder, Diagramme
│
├── part-ii-sdk-fokus/                 # Teil II
├── part-iii-resilienz/                # Teil III
├── part-iv-betrieb/                   # Teil IV
└── part-v-kochbuch/                   # Teil V
```

## Beispiele ausführen

Jedes Kapitel enthält ein eigenes Python-Projekt mit ausführbaren Beispielen:

```bash
# In ein Kapitel navigieren
cd part-i-grundlagen/examples/chapter-01/

# Dependencies installieren
uv sync

# Beispiel ausführen
uv run python simple_workflow.py
```

**Voraussetzungen für Beispiele**:
- Temporal Server läuft (lokal: `temporal server start-dev`)
- Python 3.13 installiert
- uv package manager installiert

## Beiträge

Wir freuen uns über Beiträge! Bitte lesen Sie [CONTRIBUTING.md](CONTRIBUTING.md) für Details zum Beitragsprozess.

## Lizenz

[Lizenz wird noch festgelegt]

## Ressourcen

- **Temporal Documentation**: https://docs.temporal.io/
- **Temporal Python SDK**: https://docs.temporal.io/develop/python
- **Temporal Community**: https://community.temporal.io/

---

**Viel Erfolg beim Lernen von Temporal!** 🚀
