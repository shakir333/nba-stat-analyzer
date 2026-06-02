from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog, commonplayerinfo


def get_player_stats(player_name, season):
    matches = players.find_players_by_full_name(player_name)

    if not matches:
        return None

    player = matches[0]
    player_id = player["id"]
    full_name = player["full_name"]

    # Player info: team, position, jersey, logo
    info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
    info_df = info.get_data_frames()[0]

    team_id = int(info_df.loc[0, "TEAM_ID"])
    team_name = info_df.loc[0, "TEAM_NAME"]
    team_abbreviation = info_df.loc[0, "TEAM_ABBREVIATION"]
    jersey = info_df.loc[0, "JERSEY"]
    position = info_df.loc[0, "POSITION"]

    team_logo = f"https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg"

    # Player game log for selected season
    gamelog = playergamelog.PlayerGameLog(
        player_id=player_id,
        season=season,
        season_type_all_star="Regular Season"
    )

    df = gamelog.get_data_frames()[0]

    if df.empty:
        return {
            "name": full_name,
            "season_year": season,
            "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png",
            "team": team_name,
            "team_abbreviation": team_abbreviation,
            "team_logo": team_logo,
            "jersey": jersey,
            "position": position,
            "season": {},
            "last5": {},
            "game_log": []
        }

    season_stats = {
        "PPG": round(df["PTS"].mean(), 1),
        "RPG": round(df["REB"].mean(), 1),
        "APG": round(df["AST"].mean(), 1),
        "SPG": round(df["STL"].mean(), 1),
        "BPG": round(df["BLK"].mean(), 1),
        "FG%": round(df["FG_PCT"].mean() * 100, 1),
        "3P%": round(df["FG3_PCT"].mean() * 100, 1),
    }

    last5 = df.head(5)

    last5_stats = {
        "PPG": round(last5["PTS"].mean(), 1),
        "RPG": round(last5["REB"].mean(), 1),
        "APG": round(last5["AST"].mean(), 1),
        "SPG": round(last5["STL"].mean(), 1),
        "BPG": round(last5["BLK"].mean(), 1),
        "FG%": round(last5["FG_PCT"].mean() * 100, 1),
        "3P%": round(last5["FG3_PCT"].mean() * 100, 1),
    }

    game_log = []

    for _, row in df.iterrows():
        game_log.append({
            "date": row["GAME_DATE"],
            "matchup": row["MATCHUP"],
            "wl": row["WL"],
            "pts": int(row["PTS"]),
            "reb": int(row["REB"]),
            "ast": int(row["AST"]),
            "stl": int(row["STL"]),
            "blk": int(row["BLK"]),
        })

    return {
        "name": full_name,
        "season": season_stats,
        "last5": last5_stats,
        "season_year": season,
        "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png",
        "team": team_name,
        "team_abbreviation": team_abbreviation,
        "team_logo": team_logo,
        "jersey": jersey,
        "position": position,
        "game_log": game_log
    }