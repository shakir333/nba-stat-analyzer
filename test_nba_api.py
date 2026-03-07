from nba_api.stats.static import players

from nba_api.stats.endpoints import playergamelog

# ask for a player name

player_name=input('Enter player name:')

#search for matching player

matches=players.find_players_by_full_name(player_name)

if not matches:
    print('Player not found.')

else:
    player=matches[0]
    player_id=player['id']
    full_name=player['full_name']

    print(f'\nFound player: {full_name}')
    print(f'Player ID: {player_id}')

    # get game log

    gamelog=playergamelog.PlayerGameLog(player_id=player_id)

    df=gamelog.get_data_frames()[0]

    #print(df.columns.tolist())

    print('Season Averages:')
    print("PPG:  ", round(df["PTS"].mean(), 2))
    print("RPG:  ", round(df["REB"].mean(), 2))
    print("APG:  ", round(df["AST"].mean(), 2))
    print("SPG:  ", round(df["STL"].mean(), 2))
    print("BPG:  ", round(df["BLK"].mean(), 2))
    print("FG%:  ", round(df["FG_PCT"].mean() * 100, 1))
    print("3P%:  ", round(df["FG3_PCT"].mean() * 100, 1))
    print("TOV:  ", round(df["TOV"].mean(), 2))

    # --- Last 5 Games ---
    last5 = df.head(5)
    print('\n--- Last 5 Games ---')
    print("PPG:  ", round(last5["PTS"].mean(), 2))
    print("RPG:  ", round(last5["REB"].mean(), 2))
    print("APG:  ", round(last5["AST"].mean(), 2))
    print("SPG:  ", round(last5["STL"].mean(), 2))
    print("BPG:  ", round(last5["BLK"].mean(), 2))
    print("FG%:  ", round(last5["FG_PCT"].mean() * 100, 1))
    print("3P%:  ", round(last5["FG3_PCT"].mean() * 100, 1))
    print("TOV:  ", round(last5["TOV"].mean(), 2))
    



