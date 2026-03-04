import pandas as pd


def main():
    df = pd.read_csv("data/games.csv")

    # Make sure game_date is treated like a date
    df["game_date"] = pd.to_datetime(df["game_date"])

    name = input("Enter player name: ").strip().lower()

    # Filter rows where the player's name contains what the user typed
    matches = df[df["player_name"].str.lower().str.contains(name)]

    if matches.empty:
        print("No matching player found.")
        return

    # If multiple players match, show them
    unique_players = sorted(matches["player_name"].unique())
    if len(unique_players) > 1:
        print("\nMultiple players matched. Did you mean:")
        for p in unique_players:
            print("-", p)
        print("\nTry typing more of the name (example: 'stephen curry').")
        return

    player = unique_players[0]
    player_df = df[df["player_name"] == player].sort_values("game_date", ascending=False)

    # Choose last N games (N=10, but your sample data might be fewer)
    n = 10
    last_n = player_df.head(n)

    ppg = last_n["pts"].mean()
    rpg = last_n["reb"].mean()
    apg = last_n["ast"].mean()

    print(f"\nPlayer: {player}")
    print(f"Games used: {len(last_n)} (last {n} if available)")
    print(f"PPG: {ppg:.2f}")
    print(f"RPG: {rpg:.2f}")
    print(f"APG: {apg:.2f}")


if __name__ == "__main__":
    main()