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
| `shot_clock` | Shot clock (secondi), solo per riferimento — non usato nelle analisi |
| `team1_score` / `team2_score` | Punteggio |
| `team1_p1…5_name` | Giocatori Venezia |
| `team2_p1…5_name` | Giocatori Olimpia |

### 3. Genera le analisi

```bash
python3 analyze.py && python3 analyze_players.py && python3 analyze_defense.py && python3 analyze_pr.py
```

Salva in `output/`: `analisi_playcalls.json`, `analisi_situations.json`, `analisi_giocatori.json`, `analisi_giocatori_difesa.json`, `analisi_difesa.json`, `analisi_pr.json`.

### 4. Avvia la dashboard

```bash
cd dashboard && npm run dev
```
