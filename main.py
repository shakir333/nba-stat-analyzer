import pandas as pd #im guessing it transforms pandas into pd

from src.stats_engine import compute_averages, compare_players, leaderboard #pulling info from src

def main():
    df=pd.read_csv("data/games.csv")

    df["game_date"]=pd.todate(df["game_date"])

    print("1-Player Stats")
    