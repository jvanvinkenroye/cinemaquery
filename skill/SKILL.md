---
name: cinemaquery
description: Query cinema showtimes, movies and cinema info for German cinemas via the cinemaquery CLI. Use when the user asks about movies in cinemas, showtimes, what's playing in a city or cinema, or wants info about a specific movie. Triggers on questions like "was läuft heute/diese Woche im Kino", "Vorstellungen in [Stadt]", "wann läuft [Film]", "Kinos in [Stadt]", "was kommt nächste Woche".
---

# cinemaquery Skill

Nutze das `cinemaquery` CLI-Tool um Kinoabfragen zu beantworten. Das Tool fragt die Cineamo API ab und liefert JSON-Output.

## Workflow

### 1. Kino-IDs ermitteln (wenn Stadt, aber keine konkrete Kino-ID bekannt)

```bash
cinemaquery cinemas --city "<Stadt>" --format json
```

Extrahiere `id` und `name` aus dem Result. Frage alle relevanten Kinos parallel ab.

### 2. Showtimes abfragen

```bash
# Einzelner Tag (default: heute):
cinemaquery showtimes --cinema-id <ID> --date <YYYY-MM-DD> --format json

# Datumsbereich (z.B. eine Woche):
cinemaquery showtimes --cinema-id <ID> --date <YYYY-MM-DD> --end-date <YYYY-MM-DD> --format json
```

`--end-date` ist inklusiv. Das aktuelle Datum ist im Kontext verfügbar.

### 3. Film-Details bei Nachfrage

```bash
cinemaquery movies --query "<Titel>" --format json
```

Relevante Felder: `overview` (Inhalt), `genres`, `runtime`, `releaseDate`, `credits.crew` (Regisseur), `credits.cast`.

## Output-Format der Showtimes (`--all`-Pfad)

```json
{"items": [{"datetime": "2026-03-23 19:30", "name": "Filmtitel", "language": "deu", "original": "OV", "id": "..."}]}
```

## Output-Format der Showtimes (Single-Page-Pfad)

```json
{"items": [{"name": "Filmtitel", "startDatetime": "2026-03-23T18:30:00Z", "language": "deu", ...}]}
```

## Ergebnis aufbereiten

- Nach Kino und Tag gruppieren
- Uhrzeiten in lokaler Zeit anzeigen (CET = UTC+1, CEST = UTC+2)
- Prägnante Markdown-Tabelle oder Liste
- Bei mehreren Kinos: pro Kino eine Sektion

## Typische Abfragen

| User-Anfrage | Vorgehen |
|---|---|
| "Was läuft heute in Stuttgart?" | cinemas --city Stuttgart → showtimes --date heute für alle Kinos |
| "Was kommt nächste Woche im Corso?" | ID 781, --date Mo --end-date So |
| "Um was geht es bei Film X?" | movies --query X → overview ausgeben |
| "Wann läuft Hoppers in München?" | cinemas --city München → showtimes filtern nach "Hoppers" |
