from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog


def get_player_stats(player_name, season):
    matches = players.find_players_by_full_name(player_name)

    if not matches:
        return None

    player = matches[0]
    player_id = player["id"]
    full_name = player["full_name"]

    try:
        gamelog = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=season
            timeout=8
        )
        df = gamelog.get_data_frames()[0]
    except Exception:
        return None

    if df.empty:
        return None

    stats = {
        "name": full_name,
        "season": season,
        "PPG": float(round(df["PTS"].mean(), 2)),
        "RPG": float(round(df["REB"].mean(), 2)),
        "APG": float(round(df["AST"].mean(), 2)),
        "SPG": float(round(df["STL"].mean(), 2)),
        "BPG": float(round(df["BLK"].mean(), 2)),
        "FG%": float(round(df["FG_PCT"].mean() * 100, 1)),
        "3P%": float(round(df["FG3_PCT"].mean() * 100, 1))
    }

    return stats


def compare_players(name1, season1, name2, season2):
    p1 = get_player_stats(name1, season1)
    p2 = get_player_stats(name2, season2)

    if p1 is None:
        return {
            "success": False,
            "error": (
                f"Player not found or no games available: "
                f"{name1} ({season1})"
            )
        }

    if p2 is None:
        return {
            "success": False,
            "error": (
                f"Player not found or no games available: "
                f"{name2} ({season2})"
            )
        }

    categories = ["PPG", "RPG", "APG", "SPG", "BPG", "FG%", "3P%"]

    p1_wins = 0
    p2_wins = 0
    comparison_rows = []

    for category in categories:
        p1_value = p1[category]
        p2_value = p2[category]

        if p1_value > p2_value:
            category_winner = "player1"
            p1_wins += 1
        elif p2_value > p1_value:
            category_winner = "player2"
            p2_wins += 1
        else:
            category_winner = "tie"

        comparison_rows.append({
            "category": category,
            "player1_value": p1_value,
            "player2_value": p2_value,
            "winner": category_winner
        })

    if p1_wins > p2_wins:
        overall_winner = "player1"
    elif p2_wins > p1_wins:
        overall_winner = "player2"
    else:
        overall_winner = "tie"

    return {
        "success": True,
        "player1": p1,
        "player2": p2,
        "rows": comparison_rows,
        "player1_wins": p1_wins,
        "player2_wins": p2_wins,
        "overall_winner": overall_winner
    }