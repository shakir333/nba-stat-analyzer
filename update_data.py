import argparse
import csv
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_ROOT / "data" / "nba_stats.db"
DEFAULT_SOURCE = PROJECT_ROOT / "kaggle_data"
DEFAULT_SEASONS = [
    "2016-17", "2017-18", "2018-19", "2019-20", "2020-21",
    "2021-22", "2022-23", "2023-24", "2024-25", "2025-26",
]
STANDINGS_FILENAME = "LeagueStandings.csv"


def season_for_date(date_text):
    year, month = map(int, date_text[:7].split("-"))
    start_year = year if month >= 7 else year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def integer(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def decimal(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def position_for(player):
    positions = []
    if player.get("guard") == "1":
        positions.append("G")
    if player.get("forward") == "1":
        positions.append("F")
    if player.get("center") == "1":
        positions.append("C")
    return "/".join(positions)


def create_database(connection):
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        DROP TABLE IF EXISTS game_logs;
        DROP TABLE IF EXISTS player_seasons;
        DROP TABLE IF EXISTS team_seasons;
        DROP TABLE IF EXISTS players;
        DROP TABLE IF EXISTS teams;
        DROP TABLE IF EXISTS metadata;

        CREATE TABLE teams (
            team_id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            abbreviation TEXT NOT NULL UNIQUE,
            city TEXT NOT NULL,
            nickname TEXT NOT NULL
        );

        CREATE TABLE players (
            player_id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            jersey TEXT,
            position TEXT
        );

        CREATE TABLE player_seasons (
            player_id INTEGER NOT NULL,
            season TEXT NOT NULL,
            team_id INTEGER,
            team_name TEXT,
            team_abbreviation TEXT,
            jersey TEXT,
            position TEXT,
            roster_status INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (player_id, season),
            FOREIGN KEY (player_id) REFERENCES players(player_id)
        );

        CREATE TABLE team_seasons (
            team_id INTEGER NOT NULL,
            season TEXT NOT NULL,
            team_name TEXT NOT NULL,
            conference TEXT NOT NULL,
            conference_rank INTEGER NOT NULL,
            wins INTEGER NOT NULL,
            losses INTEGER NOT NULL,
            win_percentage REAL NOT NULL,
            home_record TEXT,
            road_record TEXT,
            conference_record TEXT,
            streak TEXT,
            PRIMARY KEY (team_id, season),
            FOREIGN KEY (team_id) REFERENCES teams(team_id)
        );

        CREATE TABLE game_logs (
            player_id INTEGER NOT NULL,
            season TEXT NOT NULL,
            game_id TEXT NOT NULL,
            game_date TEXT NOT NULL,
            game_date_iso TEXT NOT NULL,
            matchup TEXT NOT NULL,
            win_loss TEXT,
            points INTEGER,
            rebounds INTEGER,
            assists INTEGER,
            steals INTEGER,
            blocks INTEGER,
            field_goals_made INTEGER,
            field_goals_attempted INTEGER,
            three_points_made INTEGER,
            three_points_attempted INTEGER,
            PRIMARY KEY (player_id, season, game_id),
            FOREIGN KEY (player_id) REFERENCES players(player_id)
        );

        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE INDEX idx_players_name ON players(full_name COLLATE NOCASE);
        CREATE INDEX idx_games_season_player ON game_logs(season, player_id);
        CREATE INDEX idx_player_seasons_team ON player_seasons(season, team_id);
        CREATE INDEX idx_team_seasons_conference
            ON team_seasons(season, conference, conference_rank);
        """
    )


def download_standings(seasons, output_path):
    try:
        from nba_api.stats.endpoints import leaguestandingsv3
    except ImportError as error:
        raise RuntimeError(
            "nba_api is required to download standings. Run: py -m pip install nba_api"
        ) from error

    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, season in enumerate(sorted(seasons)):
        print(f"Downloading official {season} standings...")
        frame = leaguestandingsv3.LeagueStandingsV3(
            season=season,
            season_type="Regular Season",
            timeout=60,
        ).get_data_frames()[0]
        if len(frame.index) != 30:
            raise RuntimeError(
                f"Expected 30 teams for {season}, but NBA.com returned {len(frame.index)}."
            )
        for record in frame.to_dict("records"):
            rows.append({"season": season, **record})
        if index < len(seasons) - 1:
            time.sleep(1)

    # The 2019-20 bubble standings include extra seeding-game fields that are
    # absent from normal seasons, so collect the columns from every row.
    fieldnames = list(dict.fromkeys(key for row in rows for key in row))
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def import_standings(connection, path, selected_seasons):
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            season = row.get("season", "").strip()
            if season not in selected_seasons:
                continue
            team_name = (
                f"{row.get('TeamCity', '').strip()} {row.get('TeamName', '').strip()}"
            ).strip()
            rows.append(
                (
                    integer(row.get("TeamID")), season, team_name,
                    row.get("Conference", "").strip(), integer(row.get("PlayoffRank")),
                    integer(row.get("WINS")), integer(row.get("LOSSES")),
                    decimal(row.get("WinPCT")), row.get("HOME", "").strip(),
                    row.get("ROAD", "").strip(), row.get("ConferenceRecord", "").strip(),
                    row.get("strCurrentStreak", "").strip(),
                )
            )

    expected = len(selected_seasons) * 30
    if len(rows) != expected:
        raise RuntimeError(
            f"Expected {expected} standings rows, but found {len(rows)} in {path}. "
            "Delete the cached file and rerun to download it again."
        )
    connection.executemany(
        """
        INSERT INTO team_seasons (
            team_id, season, team_name, conference, conference_rank,
            wins, losses, win_percentage, home_record, road_record,
            conference_record, streak
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)


def load_player_bios(path):
    bios = {}
    with path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            bios[integer(row["personId"])] = {
                "jersey": row.get("jersey", "").strip(),
                "position": position_for(row),
            }
    return bios


def load_team_history(path, season_start):
    history = defaultdict(list)
    with path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            if row.get("league") != "NBA":
                continue
            # Standard NBA franchises use the 16106127xx ID range. The history
            # file also contains temporary All-Star teams with reused abbreviations.
            if integer(row.get("teamId")) < 1_610_612_700:
                continue
            founded = integer(row.get("seasonFounded"))
            active_till = integer(row.get("seasonActiveTill")) or 9999
            if founded <= season_start <= active_till:
                history[integer(row["teamId"])].append(row)
    return {
        team_id: rows[-1]
        for team_id, rows in history.items()
    }


def import_player_statistics(connection, path, selected_seasons, bios):
    players = {}
    season_teams = defaultdict(lambda: defaultdict(int))
    game_rows = []

    with path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            if row.get("gameType") != "Regular Season":
                continue
            # Some historical rows represent DNP/inactive appearances. They
            # belong to the team roster, but not to a player's game log or
            # season-average calculation.
            if integer(row.get("numMinutes")) <= 0:
                continue
            season = season_for_date(row["gameDate"])
            if season not in selected_seasons:
                continue

            player_id = integer(row["personId"])
            team_id = integer(row["playerteamId"])
            full_name = f"{row['firstName']} {row['lastName']}".strip()
            team_name = f"{row['playerteamCity']} {row['playerteamName']}".strip()
            opponent = f"{row['opponentteamCity']} {row['opponentteamName']}".strip()
            matchup = f"vs. {opponent}" if row.get("home") == "1" else f"@ {opponent}"

            players[player_id] = full_name
            season_teams[(player_id, season)][(team_id, team_name)] += 1
            game_rows.append(
                (
                    player_id, season, row["gameId"], row["gameDate"][:10],
                    row["gameDate"][:10], matchup,
                    "W" if row.get("win") == "1" else "L",
                    integer(row.get("points")), integer(row.get("reboundsTotal")),
                    integer(row.get("assists")), integer(row.get("steals")),
                    integer(row.get("blocks")), integer(row.get("fieldGoalsMade")),
                    integer(row.get("fieldGoalsAttempted")),
                    integer(row.get("threePointersMade")),
                    integer(row.get("threePointersAttempted")),
                )
            )

    connection.executemany(
        "INSERT INTO players (player_id, full_name, jersey, position) VALUES (?, ?, ?, ?)",
        [
            (player_id, name, bios.get(player_id, {}).get("jersey", ""),
             bios.get(player_id, {}).get("position", ""))
            for player_id, name in players.items()
        ],
    )
    connection.executemany(
        """
        INSERT INTO game_logs (
            player_id, season, game_id, game_date, game_date_iso, matchup,
            win_loss, points, rebounds, assists, steals, blocks,
            field_goals_made, field_goals_attempted,
            three_points_made, three_points_attempted
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        game_rows,
    )
    return season_teams, len(players), len(game_rows)


def save_season_metadata(connection, season_teams, bios, team_history):
    latest_season = max(season for _, season in season_teams)
    teams_by_name = {
        f"{team['teamCity']} {team['teamName']}".strip().casefold(): (team_id, team)
        for team_id, team in team_history.items()
    }
    rows = []
    for (player_id, season), team_counts in season_teams.items():
        (team_id, team_name), _ = max(team_counts.items(), key=lambda item: item[1])
        team = team_history.get(team_id, {})

        # Kaggle's PlayerStatistics.csv has blank playerteamId values for most
        # 2021-22 rows. The city and team name are still present, so recover
        # the official NBA team ID from TeamHistories.csv when needed.
        if not team:
            team_id, team = teams_by_name.get(team_name.casefold(), (0, {}))

        abbreviation = team.get("teamAbbrev", "").strip()
        rows.append(
            (
                player_id, season, team_id, team_name, abbreviation,
                bios.get(player_id, {}).get("jersey", ""),
                bios.get(player_id, {}).get("position", ""),
                1 if season == latest_season else 0,
            )
        )
    connection.executemany(
        """
        INSERT INTO player_seasons (
            player_id, season, team_id, team_name, team_abbreviation,
            jersey, position, roster_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def save_teams(connection, team_history):
    rows = []
    for team_id, team in team_history.items():
        city = team["teamCity"].strip()
        nickname = team["teamName"].strip()
        rows.append((team_id, f"{city} {nickname}", team["teamAbbrev"].strip(), city, nickname))
    connection.executemany(
        "INSERT INTO teams (team_id, full_name, abbreviation, city, nickname) VALUES (?, ?, ?, ?, ?)",
        rows,
    )


def main():
    parser = argparse.ArgumentParser(description="Build a compact NBA SQLite database from Kaggle CSV files.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE,
                        help="Folder containing the Kaggle CSV files")
    parser.add_argument(
        "--seasons",
        nargs="+",
        default=DEFAULT_SEASONS,
        help=(
            "Seasons to import. By default, the most recent 10 completed "
            "seasons are included. Example: 2024-25 2025-26"
        ),
    )
    parser.add_argument(
        "--refresh-standings", action="store_true",
        help="Download standings again even if LeagueStandings.csv already exists",
    )
    args = parser.parse_args()

    required = {
        "PlayerStatistics.csv": args.source / "PlayerStatistics.csv",
        "Players.csv": args.source / "Players.csv",
        "TeamHistories.csv": args.source / "TeamHistories.csv",
    }
    missing = [name for name, path in required.items() if not path.exists()]
    if missing:
        parser.error(f"Missing CSV files in {args.source}: {', '.join(missing)}")

    selected = set(args.seasons)
    standings_path = args.source / STANDINGS_FILENAME
    if args.refresh_standings or not standings_path.exists():
        downloaded = download_standings(selected, standings_path)
        print(f"Saved {downloaded} standings rows to {standings_path}")
    else:
        print(f"Using cached standings from {standings_path}")

    season_start = max(int(season[:4]) for season in selected)
    print(f"Reading player biographies and team history...")
    bios = load_player_bios(required["Players.csv"])
    teams = load_team_history(required["TeamHistories.csv"], season_start)

    DATABASE_PATH.parent.mkdir(exist_ok=True)
    temporary_path = DATABASE_PATH.with_suffix(".building.db")
    temporary_path.unlink(missing_ok=True)

    print(f"Importing regular-season player games for {', '.join(sorted(selected))}...")
    with sqlite3.connect(temporary_path) as connection:
        create_database(connection)
        season_teams, player_count, game_count = import_player_statistics(
            connection, required["PlayerStatistics.csv"], selected, bios
        )
        if not game_count:
            raise RuntimeError("No matching games were found. Check the season values.")
        save_season_metadata(connection, season_teams, bios, teams)
        save_teams(connection, teams)
        standings_count = import_standings(connection, standings_path, selected)
        connection.executemany(
            "INSERT INTO metadata (key, value) VALUES (?, ?)",
            [
                ("last_updated", datetime.now(timezone.utc).isoformat()),
                ("source", "Kaggle player data; NBA.com LeagueStandingsV3 standings"),
                ("seasons", ",".join(sorted(selected))),
            ],
        )
        connection.commit()
        connection.execute("VACUUM")

    temporary_path.replace(DATABASE_PATH)
    print(
        f"Stored {player_count:,} players, {game_count:,} regular-season game rows, "
        f"and {standings_count:,} standings rows."
    )
    print(f"Database updated at {DATABASE_PATH}")


if __name__ == "__main__":
    main()
