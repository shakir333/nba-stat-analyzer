from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog

player_name=input('Enter the player name:')

matches=players.find_players_by_full_name(player_name)

if not matches:
    print('Player not found')

else:
    player=matches[0]
    player_id=player['id']
    full_name=player['full_name']

    print(f'\nFound player:{full_name}')

    gamelog=playergamelog.PlayerGameLog(player_id=player_id)

    df=gamelog.get_data_frames()[0]

    print('\nSeason averages')

    print("PPG:", round(df["PTS"].mean(), 2))
    print("RPG:", round(df["REB"].mean(), 2))
    print("APG:", round(df["AST"].mean(), 2))

    last5 = df.head(5)

    print("\nLast 5 games")

    print("PPG:", round(last5["PTS"].mean(), 2))
    print("RPG:", round(last5["REB"].mean(), 2))
    print("APG:", round(last5["AST"].mean(), 2))