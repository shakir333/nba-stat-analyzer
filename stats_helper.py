from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog

def get_player_stats(player_name):
    matches = players.find_players_by_full_name(player_name)

    if not matches:
        return None
    
    player = matches[0]
    player_id = player["id"]
    full_name = player["full_name"]

    gamelog = playergamelog.PlayerGameLog(player_id=player_id)
    df = gamelog.get_data_frames()[0]

    season_stats = {
        "PPG": round(df["PTS"].mean(), 2),
        "RPG": round(df["REB"].mean(), 2),
        "APG": round(df["AST"].mean(), 2),
    }

    last5 = df.head(5)

    last5_stats = {
        "PPG": round(last5["PTS"].mean(), 2),
        "RPG": round(last5["REB"].mean(), 2),
        "APG": round(last5["AST"].mean(), 2),
    }

    return {
        "name": full_name,
        "season": season_stats,
        "last5": last5_stats,
    }
