# Temporal.io – Durable Execution Mastery

**Ein umfassender Deep Dive in die Orchestrierung verteilter Systeme mit Temporal**

## Über dieses Projekt

Dieses Repository enthält ein vollständiges Lernbuch über Temporal.io, die führende Plattform für Durable Execution. Das Buch richtet sich an Entwickler, die lernen möchten, wie man zuverlässige, skalierbare und wartbare verteilte Systeme mit Temporal entwickelt.

### Entstehung

Dieses Buch entstand als persönliches Lernprojekt in Zusammenarbeit mit generativer KI (Claude by Anthropic). Es dokumentiert meine Lernreise durch Temporal.io – von den Grundlagen bis zu fortgeschrittenen Produktions-Patterns. Die KI diente als interaktiver Lernpartner, der half, komplexe Konzepte zu strukturieren und in verständliche Erklärungen zu übersetzen.

**Wichtig**: Alle Inhalte wurden kritisch geprüft, Code-Beispiele getestet und die technische Korrektheit sichergestellt. Dieses Buch ist das Ergebnis aktiven Lernens, nicht bloßer Textgenerierung.

## Voraussetzungen

- Python 3.13+
- uv package manager
- Temporal CLI oder Docker (für lokale Entwicklung)
- Grundkenntnisse in Python und verteilten Systemen

## Schnellstart

### Das Buch lesen

**Online (empfohlen)**:
- Besuchen Sie die veröffentlichte Version auf GitHub Pages: https://thecodeengine.github.io/temporal-durable-execution-mastery/

**Lokal bauen**:
```bash
# Repository klonen
git clone https://github.com/TheCodeEngine/temporal-durable-execution-mastery.git
cd temporal-durable-execution-mastery

# mdBook installieren (falls noch nicht vorhanden)
brew install mdbook  # macOS
# oder: cargo install mdbook

# Mermaid-Preprocessor installieren
cargo install mdbook-mermaid
mdbook-mermaid install .

# Buch lokal bauen und öffnen
mdbook build
open book/index.html

# Oder mit Live-Reload während der Bearbeitung
mdbook serve --open
```

### Code-Beispiele ausführen

```bash
# Beispiel ausführen (z.B. Kapitel 1)
cd examples/part-01/chapter-01
uv sync
uv run python simple_workflow.py
```

## Inhaltsverzeichnis

### Teil I: Grundlagen der Durable Execution

Lernen Sie die Kernkonzepte von Temporal kennen und verstehen Sie, warum Durable Execution die Zukunft verteilter Systeme ist.

- [Kapitel 1: Einführung in Temporal](src/part-01-chapter-01.md)
- [Kapitel 2: Kernbausteine: Workflows, Activities, Worker](src/part-01-chapter-02.md)
- [Kapitel 3: Architektur des Temporal Service](src/part-01-chapter-03.md)

### Teil II: Entwicklung von Temporal-Anwendungen (SDK-Fokus)

Tauchen Sie ein in die praktische Entwicklung mit dem Temporal Python SDK.

- [Kapitel 4: Entwicklungs-Setup und SDK-Auswahl](src/part-02-chapter-04.md)
- [Kapitel 5: Workflows programmieren](src/part-02-chapter-05.md)
- [Kapitel 6: Kommunikation (Signale und Queries)](src/part-02-chapter-06.md)

### Teil III: Resilienz, Evolution und Muster

Meistern Sie fortgeschrittene Muster für robuste, evolvierbare Systeme.

- [Kapitel 7: Fehlerbehandlung und Retries](src/part-03-chapter-07.md)
- [Kapitel 8: SAGA Pattern](src/part-03-chapter-08.md)
- [Kapitel 9: Workflow-Evolution und Versionierung](src/part-03-chapter-09.md)

### Teil IV: Betrieb, Skalierung und Best Practices

Bringen Sie Ihre Temporal-Anwendungen in die Produktion.

- [Kapitel 10: Produktions-Deployment](src/part-04-chapter-10.md)
- [Kapitel 11: Skalierung der Worker](src/part-04-chapter-11.md)
- [Kapitel 12: Observability und Monitoring](src/part-04-chapter-12.md)
- [Kapitel 13: Best Practices und Anti-Muster](src/part-04-chapter-13.md)

### Teil V: Das Temporal Kochbuch

Praktische Rezepte für häufige Anwendungsfälle.

- [Kapitel 14: Muster-Rezepte (Human-in-Loop, Cron, Order Fulfillment)](src/part-05-chapter-14.md)
- [Kapitel 15: Erweiterte Rezepte (AI Agents, Lambda, Polyglot)](src/part-05-chapter-15.md)

## Projektstruktur

```
temporal-book/
├── README.md                          # Dieses Dokument
├── book.toml                          # mdBook Konfiguration
├── src/                               # Buch-Inhalt (mdBook)
│   ├── SUMMARY.md                     # Inhaltsverzeichnis
│   ├── README.md                      # Einleitung
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
├── shared/                            # Gemeinsame Python-Utilities
└── .github/workflows/                 # GitHub Actions für Deployment
    └── deploy-mdbook.yml
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

## GitHub Pages Deployment

Das Buch wird automatisch über GitHub Actions auf GitHub Pages veröffentlicht:

1. **Automatische Builds**: Bei jedem Push zum `develop` Branch wird das Buch neu gebaut
2. **Deployment**: Die generierte Website wird automatisch auf GitHub Pages deployed
3. **URL**: Das Buch ist verfügbar unter https://thecodeengine.github.io/temporal-durable-execution-mastery/

### Setup (einmalig erforderlich)

1. In den Repository-Einstellungen → Pages
2. Source auf "GitHub Actions" setzen
3. Workflow wird automatisch ausgeführt bei Push zu `develop`

## Beiträge

Dieses ist ein persönliches Lernprojekt. Wenn Sie Fehler finden oder Verbesserungsvorschläge haben, öffnen Sie gerne ein Issue!

## Lizenz

[Lizenz wird noch festgelegt]

## Ressourcen

- **Temporal Documentation**: https://docs.temporal.io/
- **Temporal Python SDK**: https://docs.temporal.io/develop/python
- **Temporal Community**: https://community.temporal.io/

---

**Viel Erfolg beim Lernen von Temporal!** 🚀
