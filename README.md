# Video Sync — Olimpia Analytics

## Installazione

```bash
pip install -r requirements.txt
```

---

## Procedura

### 1. Genera la sync map

Metti i segmenti video in `input/` (nomi: `Segment 1.mp4`, `Segment 2.mp4`, …), poi:

```bash
python3 video-sync.py
```

- Naviga il video con `←` `→` finché il tabellone è visibile, poi `ENTER`
- Disegna un rettangolo attorno al clock, poi `ENTER`
- Lo script processa tutti i segmenti e salva `input/sync.json`

### 2. Arricchisci il CSV

Con `input/input.csv` e `input/lineups.csv` nella cartella:

```bash
python3 start-time-enrich.py && python3 lineup-enrich.py
```

Salva `enriched.csv` con le colonne aggiunte:

| Colonna | Contenuto |
|---|---|
| `ocr_quarter` | Quarto (1–4) |
| `start_time_game_clock` | Orologio `MM:SS` |
| `team1_score` / `team2_score` | Punteggio |
| `team1_p1…5_name` | Giocatori Venezia |
| `team2_p1…5_name` | Giocatori Olimpia |
