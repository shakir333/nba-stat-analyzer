from stats_helper import get_player_stats


CATEGORIES = ["PPG", "RPG", "APG", "SPG", "BPG", "FG%", "3P%"]


def _summary(stats):
    return {
        "name": stats["name"],
        "season": stats["season_year"],
        **stats["season"],
    }


def compare_players(name1, season1, name2, season2):
    first = get_player_stats(name1, season1)
    second = get_player_stats(name2, season2)

    if first is None:
        return {
            "success": False,
            "error": f"No stored data found for {name1} ({season1}).",
        }
    if second is None:
        return {
            "success": False,
            "error": f"No stored data found for {name2} ({season2}).",
        }

    player1 = _summary(first)
    player2 = _summary(second)
    player1_wins = 0
    player2_wins = 0
    rows = []

    for category in CATEGORIES:
        value1 = player1[category]
        value2 = player2[category]
        if value1 > value2:
            winner = "player1"
            player1_wins += 1
        elif value2 > value1:
            winner = "player2"
            player2_wins += 1
        else:
            winner = "tie"
        rows.append(
            {
                "category": category,
                "player1_value": value1,
                "player2_value": value2,
                "winner": winner,
            }
        )

    overall_winner = (
        "player1"
        if player1_wins > player2_wins
        else "player2"
        if player2_wins > player1_wins
        else "tie"
    )
    return {
        "success": True,
        "player1": player1,
        "player2": player2,
        "rows": rows,
        "player1_wins": player1_wins,
        "player2_wins": player2_wins,
        "overall_winner": overall_winner,
    }
