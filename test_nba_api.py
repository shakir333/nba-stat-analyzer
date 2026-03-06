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

    print('\nFirst 5 games:')

    print(df[['GAME_DATE','MATCHUP','PTS','REB','AST']].head())

    print(f"\n{full_name} averages:")
    
    print("PPG:", round(df["PTS"].mean(), 2))
    
    print("RPG:", round(df["REB"].mean(), 2))
    
    print("APG:", round(df["AST"].mean(), 2))


