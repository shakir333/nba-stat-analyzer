# NBA Player Analytics

A Flask web application for exploring stored NBA player statistics, comparing players, and browsing team rosters. Normal page requests read a compact SQLite database, so deployed searches do not depend on a live statistics API.

## Features

- Player season averages, last-five averages, and game logs
- Historical season selection for downloaded seasons
- Two-player, seven-category comparisons
- Directory of all 30 NBA teams
- Current roster pages linked to player lookup
- Offline production reads from SQLite

## Local setup

```bash
py -m pip install -r requirements.txt
py app.py
```

Open `http://127.0.0.1:5000`.

## Rebuild the data

Download the CSV files from the Kaggle **Historical NBA Data and Player Box Scores** dataset. Create a local `kaggle_data` folder and place these files inside it:

- `PlayerStatistics.csv`
- `Players.csv`
- `TeamHistories.csv`

`kaggle_data/` is ignored by Git because the original CSVs are large. Build the deployable database with the default 10-season range (`2016-17` through `2025-26`):

```bash
py update_data.py
```

To choose a smaller or different range, list the seasons explicitly:

```bash
py update_data.py --seasons 2023-24 2024-25 2025-26
```

The importer replaces `data/nba_stats.db` only after a successful build. Commit that compact database so Render receives it during deployment. Do not commit the original Kaggle CSV files.

## Render

Use this start command:

```bash
gunicorn app:app
```

After pushing code and `data/nba_stats.db`, Render can deploy normally. The updater should be run locally, not as part of the web start command.

## Architecture

```text
Kaggle CSVs -> update_data.py -> SQLite -> Flask routes -> HTML templates
```

## Technology

Python, Flask, SQLite, HTML/CSS, Gunicorn, Render
