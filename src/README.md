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
cd examples/part-01/chapter-01
uv sync
uv run python simple_workflow.py
```

## Inhaltsverzeichnis

### Teil I: Grundlagen der Durable Execution

Lernen Sie die Kernkonzepte von Temporal kennen und verstehen Sie, warum Durable Execution die Zukunft verteilter Systeme ist.

- [Kapitel 1: Einführung in Temporal](part-01-chapter-01.md)
- [Kapitel 2: Kernbausteine: Workflows, Activities, Worker](part-01-chapter-02.md)
- [Kapitel 3: Architektur des Temporal Service](part-01-chapter-03.md)

### Teil II: Entwicklung von Temporal-Anwendungen (SDK-Fokus)

Tauchen Sie ein in die praktische Entwicklung mit dem Temporal Python SDK.

- [Kapitel 4: Entwicklungs-Setup und SDK-Auswahl](part-02-chapter-04.md)
- [Kapitel 5: Workflows programmieren](part-02-chapter-05.md)
- [Kapitel 6: Kommunikation (Signale und Queries)](part-02-chapter-06.md)

### Teil III: Resilienz, Evolution und Muster

Meistern Sie fortgeschrittene Muster für robuste, evolvierbare Systeme.

- [Kapitel 7: Fehlerbehandlung und Retries](part-03-chapter-07.md)
- [Kapitel 8: SAGA Pattern](part-03-chapter-08.md)
- [Kapitel 9: Workflow-Evolution und Versionierung](part-03-chapter-09.md)

### Teil IV: Betrieb, Skalierung und Best Practices

Bringen Sie Ihre Temporal-Anwendungen in die Produktion.

- [Kapitel 10: Produktions-Deployment](part-04-chapter-10.md)
- [Kapitel 11: Skalierung der Worker](part-04-chapter-11.md)
- [Kapitel 12: Observability und Monitoring](part-04-chapter-12.md)
- [Kapitel 13: Best Practices und Anti-Muster](part-04-chapter-13.md)

### Teil V: Das Temporal Kochbuch

Praktische Rezepte für häufige Anwendungsfälle.

- [Kapitel 14: Muster-Rezepte (Human-in-Loop, Cron, Order Fulfillment)](part-05-chapter-14.md)
- [Kapitel 15: Erweiterte Rezepte (AI Agents, Lambda, Polyglot)](part-05-chapter-15.md)

## Projektstruktur

```
temporal-book/
├── README.md                          # Repository README
├── book.toml                          # mdBook Konfiguration
├── src/                               # Buch-Inhalt (mdBook)
│   ├── SUMMARY.md                     # Inhaltsverzeichnis
│   ├── README.md                      # Dieses Dokument
│   ├── part-01-chapter-01.md          # Kapitel (flache Struktur)
│   └── images/                        # Bilder und Diagramme
│
├── book/                              # Generierte HTML-Ausgabe (gitignored)
│
├── examples/                          # Python-Beispiele
│   ├── part-01/
│   │   └── chapter-01/
│   │       ├── pyproject.toml
│   │       ├── .python-version
│   │       └── *.py
│   ├── part-02/
│   ├── part-03/
│   └── part-04/
│
└── shared/                            # Gemeinsame Python-Utilities
```

## Beispiele ausführen

Jedes Kapitel enthält ein eigenes Python-Projekt mit ausführbaren Beispielen:

```bash
# In ein Kapitel navigieren
cd examples/part-01/chapter-01/

# Dependencies installieren
uv sync

# Beispiel ausführen
uv run python simple_workflow.py
```

**Voraussetzungen für Beispiele**:
- Temporal Server läuft (lokal: `temporal server start-dev`)
- Python 3.13 installiert
- uv package manager installiert

## Ressourcen

- **Temporal Documentation**: https://docs.temporal.io/
- **Temporal Python SDK**: https://docs.temporal.io/develop/python
- **Temporal Community**: https://community.temporal.io/

---

**Viel Erfolg beim Lernen von Temporal!** 🚀
