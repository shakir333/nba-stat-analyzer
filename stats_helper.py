import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "data" / "nba_stats.db"


def _connect():
    if not DATABASE_PATH.exists():
        return None
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def get_available_seasons():
    connection = _connect()
    if connection is None:
        return []
    with connection:
        rows = connection.execute(
            "SELECT DISTINCT season FROM game_logs ORDER BY season DESC"
        ).fetchall()
    return [row["season"] for row in rows]


def _find_player(connection, player_name, season):
    exact = connection.execute(
        """
        SELECT p.player_id, p.full_name,
               ps.team_id, ps.team_name, ps.team_abbreviation,
               ps.jersey, ps.position
        FROM players AS p
        JOIN player_seasons AS ps
          ON ps.player_id = p.player_id AND ps.season = ?
        JOIN game_logs AS g ON g.player_id = p.player_id
        WHERE lower(p.full_name) = lower(?) AND g.season = ?
        LIMIT 1
        """,
        (season, player_name, season),
    ).fetchone()
    if exact:
        return exact

    matches = connection.execute(
        """
        SELECT DISTINCT p.player_id, p.full_name,
               ps.team_id, ps.team_name, ps.team_abbreviation,
               ps.jersey, ps.position
        FROM players AS p
        JOIN player_seasons AS ps
          ON ps.player_id = p.player_id AND ps.season = ?
        JOIN game_logs AS g ON g.player_id = p.player_id
        WHERE lower(p.full_name) LIKE lower(?) AND g.season = ?
        ORDER BY p.full_name
        LIMIT 2
        """,
        (season, f"%{player_name}%", season),
    ).fetchall()
    return matches[0] if len(matches) == 1 else None


def _percentage(rows, made_key, attempted_key):
    made = sum(row[made_key] or 0 for row in rows)
    attempted = sum(row[attempted_key] or 0 for row in rows)
    return round(made / attempted * 100, 1) if attempted else 0.0


def _averages(rows):
    if not rows:
        return {}
    count = len(rows)
    return {
        "PPG": round(sum(row["points"] or 0 for row in rows) / count, 1),
        "RPG": round(sum(row["rebounds"] or 0 for row in rows) / count, 1),
        "APG": round(sum(row["assists"] or 0 for row in rows) / count, 1),
        "SPG": round(sum(row["steals"] or 0 for row in rows) / count, 1),
        "BPG": round(sum(row["blocks"] or 0 for row in rows) / count, 1),
        "FG%": _percentage(rows, "field_goals_made", "field_goals_attempted"),
        "3P%": _percentage(rows, "three_points_made", "three_points_attempted"),
    }


def get_player_stats(player_name, season):
    connection = _connect()
    if connection is None:
        return None

    with connection:
        player = _find_player(connection, player_name, season)
        if player is None:
            return None
        games = connection.execute(
            """
            SELECT * FROM game_logs
            WHERE player_id = ? AND season = ?
            ORDER BY game_date_iso DESC, game_id DESC
            """,
            (player["player_id"], season),
        ).fetchall()

    if not games:
        return None

    team_id = player["team_id"]
    return {
        "name": player["full_name"],
        "season_year": season,
        "image_url": (
            "https://cdn.nba.com/headshots/nba/latest/1040x760/"
            f"{player['player_id']}.png"
        ),
        "team": player["team_name"] or "Free Agent",
        "team_abbreviation": player["team_abbreviation"] or "",
        "team_logo": (
            f"https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg"
            if team_id
            else None
        ),
        "jersey": player["jersey"] or "—",
        "position": player["position"] or "—",
        "season": _averages(games),
        "last5": _averages(games[:5]),
        "game_log": [
            {
                "date": game["game_date"],
                "matchup": game["matchup"],
                "wl": game["win_loss"] or "—",
                "pts": game["points"] or 0,
                "reb": game["rebounds"] or 0,
                "ast": game["assists"] or 0,
                "stl": game["steals"] or 0,
                "blk": game["blocks"] or 0,
            }
            for game in games
        ],
    }


def get_teams():
    connection = _connect()
    if connection is None:
        return []
    with connection:
        rows = connection.execute(
            "SELECT * FROM teams ORDER BY city, nickname"
        ).fetchall()
    return [dict(row) for row in rows]


def get_standings(season=None):
    connection = _connect()
    if connection is None:
        return None

    with connection:
        table_exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'team_seasons'"
        ).fetchone()
        if table_exists is None:
            return None

        seasons = [
            row["season"]
            for row in connection.execute(
                "SELECT DISTINCT season FROM team_seasons ORDER BY season DESC"
            ).fetchall()
        ]
        if not seasons:
            return None
        selected_season = season if season in seasons else seasons[0]
        rows = connection.execute(
            """
            SELECT ts.*, t.abbreviation
            FROM team_seasons AS ts
            JOIN teams AS t ON t.team_id = ts.team_id
            WHERE ts.season = ?
            ORDER BY ts.conference, ts.conference_rank
            """,
            (selected_season,),
        ).fetchall()

    return {
        "season": selected_season,
        "seasons": seasons,
        "east": [dict(row) for row in rows if row["conference"] == "East"],
        "west": [dict(row) for row in rows if row["conference"] == "West"],
    }


def get_team(abbreviation):
    connection = _connect()
    if connection is None:
        return None
    with connection:
        team = connection.execute(
            "SELECT * FROM teams WHERE upper(abbreviation) = upper(?)",
            (abbreviation,),
        ).fetchone()
        if team is None:
            return None
        latest_season = connection.execute(
            "SELECT MAX(season) AS season FROM player_seasons"
        ).fetchone()["season"]
        roster = connection.execute(
            """
            SELECT p.player_id, p.full_name, ps.jersey, ps.position
            FROM player_seasons AS ps
            JOIN players AS p ON p.player_id = ps.player_id
            WHERE ps.team_id = ? AND ps.season = ? AND ps.roster_status = 1
            ORDER BY p.full_name
            """,
            (team["team_id"], latest_season),
        ).fetchall()
    result = dict(team)
    result["roster"] = [dict(player) for player in roster]
    return result
