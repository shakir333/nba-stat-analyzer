def compute_averages(df, player_name, last_n=10):

    matches = df[df["player_name"].str.lower().str.contains(player_name.lower())]

    if matches.empty:
        return None

    unique_players = sorted(matches["player_name"].unique())

    if len(unique_players) > 1:
        return {"multiple": unique_players}

    player = unique_players[0]

    player_df = df[df["player_name"] == player].sort_values("game_date", ascending=False)

    last_games = player_df.head(last_n)

    stats = {
        "player": player,
        "games": len(last_games),
        "pts": last_games["pts"].mean(),
        "reb": last_games["reb"].mean(),
        "ast": last_games["ast"].mean()
    }

    return stats


def compare_players(df, player1, player2):

    stats1 = compute_averages(df, player1)
    stats2 = compute_averages(df, player2)

    print("\nPlayer Comparison\n")

    print(stats1["player"])
    print("PPG:", round(stats1["pts"], 2))
    print("RPG:", round(stats1["reb"], 2))
    print("APG:", round(stats1["ast"], 2))

    print("\n")

    print(stats2["player"])
    print("PPG:", round(stats2["pts"], 2))
    print("RPG:", round(stats2["reb"], 2))
    print("APG:", round(stats2["ast"], 2))

    def leaderboard(df, stat="pts"):

    players = df["player_name"].unique()

    results = []

    for player in players:

        player_df = df[df["player_name"] == player]

        avg = player_df[stat].mean()

        results.append((player, avg))

    results.sort(key=lambda x: x[1], reverse=True)

    print("\nLeaderboard\n")

    for i, (player, value) in enumerate(results, start=1):

        print(f"{i}. {player} - {round(value,2)}")