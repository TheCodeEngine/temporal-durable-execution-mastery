# GitHub Pages Hosting für Temporal-Book

**Erstellt:** 2025-11-19
**Status:** Geplant
**Ziel:** Das Temporal-Buch als interaktive Website über GitHub Pages veröffentlichen

## Zusammenfassung

Das temporal-book soll als professionell gehostete Website über GitHub Pages zugänglich gemacht werden. Die Lösung kombiniert mdBook (für minimalen Umbau-Aufwand) mit interaktiven Python-Beispielen.

## Technologie-Entscheidungen

### Haupt-Tool: mdBook
**Gewählt wegen:**
- Minimaler Umbau-Aufwand (1-2 Stunden)
- Speziell für Bücher entwickelt
- Automatisches Inhaltsverzeichnis
- Mermaid-Diagramm-Unterstützung
- Schneller Build-Prozess
- Perfekt für die vorhandene Markdown-Struktur

**Alternativen erwogen:**
- MkDocs (2-3h Aufwand) - mehr Features, aber mehr Konfiguration
- Docusaurus (1-2 Tage Aufwand) - modernste Features, aber zu viel Umbau nötig

### Interaktive Code-Beispiele: Hybrid-Ansatz

**Problem:** Temporal benötigt einen laufenden Server (localhost:7233), der im Browser nicht verfügbar ist.

**Lösung:**
1. **JupyterLite** - Für einfache Python-Grundlagen ohne Temporal
   - Läuft komplett clientseitig im Browser
   - Keine Server-Abhängigkeiten
   - Perfekt für Syntax-Demos

2. **Binder/Colab** - Für vollständige Temporal-Beispiele
   - Startet komplette Umgebung mit Temporal Server
   - "Try it!" Buttons bei jedem Beispiel
   - Leser können Code direkt im Browser ausführen

3. **GitHub Download-Links** - Für lokale Entwicklung
   - Alle Beispiele als downloadbare Projekte
   - Mit README und Setup-Anleitung
   - Nutzung von `uv` für einfache Installation

### Deployment: GitHub Actions

**Automatisches Deployment:**
- Bei jedem Push auf `main` Branch
- Automatischer Build mit mdBook
- Deployment auf `gh-pages` Branch
- Website verfügbar unter: `konstantinstoldt.github.io/temporal-book`

## Projekt-Struktur (Nach Umbau)

```
temporal-book/
├── book.toml                     # mdBook Konfiguration
├── src/                          # Buch-Inhalte (mdBook Standard)
│   ├── SUMMARY.md               # Automatisches Inhaltsverzeichnis
│   ├── README.md                # Startseite
│   ├── part-i/                  # Teil 1: Grundlagen
│   │   ├── README.md
│   │   ├── chapter-01.md
│   │   ├── chapter-02.md
│   │   └── chapter-03.md
│   ├── part-ii/                 # Teil 2: SDK Focus
│   ├── part-iii/                # Teil 3: Resilienz
│   ├── part-iv/                 # Teil 4: Betrieb
│   └── part-v/                  # Teil 5: Kochbuch
├── examples/                     # Code-Beispiele (wie vorher)
│   ├── chapter-01/
│   ├── chapter-02/
│   └── ...
├── shared/                       # Shared Utilities (wie vorher)
├── theme/                        # Custom mdBook Theme
│   ├── custom.css
│   └── book.js
├── .github/
│   └── workflows/
│       └── deploy.yml           # GitHub Actions Workflow
└── docs/                         # Generierte Website (nicht im Git)
```

## Implementierungsplan

### Phase 1: mdBook Basis-Setup (30 Min)

1. **Installation & Konfiguration**
   - [ ] `book.toml` erstellen mit:
     - Titel: "Temporal - Das umfassende Handbuch"
     - Autor, Sprache (de)
     - Theme-Einstellungen
     - Mermaid-Plugin Aktivierung
     - Syntax-Highlighting für Python

2. **Verzeichnisstruktur**
   - [ ] `src/` Verzeichnis erstellen
   - [ ] `SUMMARY.md` erstellen (Inhaltsverzeichnis-Generator)
   - [ ] Vorhandene Markdown-Dateien nach `src/` strukturieren
   - [ ] Navigation zwischen Kapiteln beibehalten

3. **Inhaltsverzeichnis (`SUMMARY.md`)**
   ```markdown
   # Summary

   [Einführung](README.md)

   # Teil I: Grundlagen

   - [Einführung in Temporal](part-i/chapter-01.md)
   - [Kernbausteine](part-i/chapter-02.md)
   - [Architektur des Temporal Service](part-i/chapter-03.md)

   # Teil II: SDK im Focus
   # Teil III: Resilienz und Fehlerbehandlung
   # Teil IV: Betrieb und Deployment
   # Teil V: Kochbuch
   ```

### Phase 2: GitHub Pages Deployment (20 Min)

4. **GitHub Actions Workflow** (`.github/workflows/deploy.yml`)
   - [ ] Workflow erstellen:
     - Trigger: Push auf `main`
     - mdBook installieren
     - `mdbook build` ausführen
     - GitHub Pages deployen
   - [ ] Workflow testen

5. **Repository Settings**
   - [ ] GitHub Pages aktivieren
   - [ ] Source: `gh-pages` Branch setzen
   - [ ] Optional: Custom Domain konfigurieren

### Phase 3: Interaktive Beispiele (40 Min)

6. **JupyterLite Setup**
   - [ ] JupyterLite Konfiguration
   - [ ] Embed-Code für mdBook-Seiten
   - [ ] Test-Notebook für Python-Grundlagen

7. **Binder/Colab Integration**
   - [ ] Binder Badge-Generator
   - [ ] Colab Links für jedes Beispiel
   - [ ] "Try it!" Buttons in Markdown einfügen
   - [ ] Environment-Dateien für Binder (environment.yml)

8. **Code-Beispiel Verbesserungen**
   - [ ] README für jedes Beispiel-Projekt
   - [ ] Setup-Anleitungen ergänzen
   - [ ] Download-Buttons mit direkten GitHub-Links

### Phase 4: Design & Polish (30 Min)

9. **Custom Styling**
   - [ ] `theme/custom.css` erstellen
   - [ ] Temporal Branding-Farben einbauen
   - [ ] Responsive Design testen
   - [ ] Print-Styles für PDF-Export

10. **Navigation & Features**
    - [ ] Search-Plugin aktivieren
    - [ ] Footer mit Vor/Zurück-Navigation
    - [ ] "Edit on GitHub" Links
    - [ ] Social Media Meta-Tags

### Phase 5: Testing & Launch (10 Min)

11. **Lokales Testing**
    - [ ] `mdbook serve` starten
    - [ ] Alle Links überprüfen
    - [ ] Mobile Ansicht testen
    - [ ] Mermaid-Diagramme testen

12. **Deployment**
    - [ ] Push auf `main` Branch
    - [ ] GitHub Actions beobachten
    - [ ] Website aufrufen und final testen
    - [ ] URL teilen: `konstantinstoldt.github.io/temporal-book`

## Technische Details

### mdBook Konfiguration (`book.toml`)

```toml
[book]
title = "Temporal - Das umfassende Handbuch"
authors = ["Konstantin Stoldt"]
language = "de"
multilingual = false
src = "src"

[build]
build-dir = "docs"

[output.html]
default-theme = "light"
preferred-dark-theme = "navy"
git-repository-url = "https://github.com/konstantinstoldt/temporal-book"
edit-url-template = "https://github.com/konstantinstoldt/temporal-book/edit/main/{path}"

[output.html.search]
enable = true
limit-results = 30
use-boolean-and = true

[preprocessor.mermaid]
command = "mdbook-mermaid"

[output.html.playground]
editable = true
line-numbers = true
```

### GitHub Actions Workflow (Beispiel)

```yaml
name: Deploy mdBook to GitHub Pages

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - name: Setup mdBook
        uses: peaceiris/actions-mdbook@v1
        with:
          mdbook-version: 'latest'

      - name: Install mdbook-mermaid
        run: cargo install mdbook-mermaid

      - name: Build book
        run: mdbook build

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
```

## Vorteile dieser Lösung

### Für Leser
- ✅ Kostenlos und öffentlich zugänglich
- ✅ Professionelle Navigation und Suche
- ✅ Interaktive Code-Beispiele zum Ausprobieren
- ✅ Mobile-optimiert
- ✅ Schnelle Ladezeiten (statische Website)

### Für Entwicklung
- ✅ Minimaler Umbau-Aufwand (1-2 Stunden)
- ✅ Markdown bleibt weitgehend unverändert
- ✅ Automatisches Deployment bei jedem Push
- ✅ Einfache Wartung und Updates
- ✅ Versionskontrolle durch Git

### Für die Zukunft
- ✅ Einfach erweiterbar
- ✅ Mehrsprachigkeit möglich
- ✅ Analytics integrierbar
- ✅ Custom Domain möglich
- ✅ PDF-Export unterstützt

## Einschränkungen & Lösungen

### Einschränkung: JupyterLite kann nicht mit Temporal Server kommunizieren
**Lösung:** Hybrid-Ansatz mit Binder für vollständige Temporal-Beispiele

### Einschränkung: Binder hat längere Startzeiten (1-2 Min)
**Lösung:** Klare Hinweise für Nutzer + Download-Option für lokale Ausführung

### Einschränkung: Keine Backend-Funktionalität auf GitHub Pages
**Lösung:** Nicht benötigt - alle Interaktivität läuft über externe Services (Binder/Colab)

## Nächste Schritte

1. ✅ Idee dokumentiert
2. ⏳ Plan mit User bestätigen
3. ⏳ Implementation starten (siehe Phase 1-5)
4. ⏳ Testing & Launch

## Ressourcen

- [mdBook Dokumentation](https://rust-lang.github.io/mdBook/)
- [mdBook-Mermaid Plugin](https://github.com/badboy/mdbook-mermaid)
- [GitHub Pages Docs](https://docs.github.com/en/pages)
- [JupyterLite](https://jupyterlite.readthedocs.io/)
- [Binder](https://mybinder.org/)

## Geschätzter Gesamtaufwand

**Initial Setup:** 1.5 - 2 Stunden
**Laufende Wartung:** Minimal (automatisches Deployment)

---

*Dieses Dokument wurde erstellt, um die Planung für das GitHub Pages Hosting des Temporal-Buchs zu dokumentieren.*
