from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog

def get_player_stats(player_name):
    matches = players.find_players_by_full_name(player_name)

    if not matches:
        print(f'Player not found: {player_name}')
        return None

    player = matches[0]
    player_id = player['id']
    full_name = player['full_name']

    gamelog = playergamelog.PlayerGameLog(player_id=player_id)
    df = gamelog.get_data_frames()[0]

    stats = {
        'name': full_name,
        'PPG':  round(df["PTS"].mean(), 2),
        'RPG':  round(df["REB"].mean(), 2),
        'APG':  round(df["AST"].mean(), 2),
        'SPG':  round(df["STL"].mean(), 2),
        'BPG':  round(df["BLK"].mean(), 2),
        'FG%':  round(df["FG_PCT"].mean() * 100, 1),
        '3P%':  round(df["FG3_PCT"].mean() * 100, 1),
    }

    return stats

def compare_players(name1, name2):
    print(f'\nFetching {name1}...')
    p1 = get_player_stats(name1)

    print(f'\nFetching {name2}...')
    p2 = get_player_stats(name2)

    if not p1 or not p2:
        print('Comparison could not be completed.')
        return

    categories = ['PPG', 'RPG', 'APG', 'SPG', 'BPG', 'FG%', '3P%']

    p1_wins = 0
    p2_wins = 0

    print(f"\n{'Category':<10} {p1['name']:>20} {p2['name']:>20} {'Winner':<25}")
    print('-' * 80)

    for cat in categories:
        v1 = p1[cat]
        v2 = p2[cat]

        if v1 > v2:
            winner = p1['name']
            p1_wins += 1
        elif v2 > v1:
            winner = p2['name']
            p2_wins += 1
        else:
            winner = 'Tie'

        print(f'{cat:<10} {v1:>20} {v2:>20} {winner:<25}')

    print('-' * 80)

    if p1_wins > p2_wins:
        print(f'Overall Winner: {p1["name"]} ({p1_wins}-{p2_wins})')
    elif p2_wins > p1_wins:
        print(f'Overall Winner: {p2["name"]} ({p2_wins}-{p1_wins})')
    else:
        print('Overall Result: Tie')


# --- Run it ---
name1 = input('Enter first player name: ')
name2 = input('Enter second player name: ')

compare_players(name1, name2)