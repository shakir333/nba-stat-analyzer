from flask import Flask, render_template, request
from stats_helper import get_player_stats
from compare import compare_players


app = Flask(__name__)


SEASONS = [
    "2025-26", "2024-25", "2023-24", "2022-23", "2021-22",
    "2020-21", "2019-20", "2018-19", "2017-18", "2016-17",
    "2015-16", "2014-15", "2013-14", "2012-13", "2011-12",
    "2010-11", "2009-10", "2008-09", "2007-08", "2006-07",
    "2005-06", "2004-05", "2003-04", "2002-03", "2001-02",
    "2000-01", "1999-00", "1998-99", "1997-98", "1996-97",
    "1995-96", "1994-95", "1993-94", "1992-93", "1991-92",
    "1990-91"
]


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/player")
def player():
    player_name = request.args.get("name")
    season = request.args.get("season", "2023-24")

    if not player_name:
        return render_template(
            "player.html",
            error="No player name entered.",
            seasons=SEASONS
        )

    stats = get_player_stats(player_name, season)

    if not stats:
        return render_template(
            "player.html",
            error="Player not found.",
            seasons=SEASONS
        )

    return render_template(
        "player.html",
        stats=stats,
        seasons=SEASONS
    )


@app.route("/compare", methods=["GET", "POST"])
def compare():
    result = None
    error = None

    player1_name = ""
    player2_name = ""
    player1_season = "2025-26"
    player2_season = "2025-26"

    if request.method == "POST":
        player1_name = request.form.get("player1", "").strip()
        player2_name = request.form.get("player2", "").strip()

        player1_season = request.form.get(
            "player1_season",
            "2025-26"
        )

        player2_season = request.form.get(
            "player2_season",
            "2025-26"
        )

        if not player1_name or not player2_name:
            error = "Please enter both player names."

        elif (
            player1_name.lower() == player2_name.lower()
            and player1_season == player2_season
        ):
            error = "Please choose different players or different seasons."

        else:
            result = compare_players(
                player1_name,
                player1_season,
                player2_name,
                player2_season
            )

            if not result["success"]:
                error = result["error"]
                result = None

    return render_template(
        "compare.html",
        result=result,
        error=error,
        seasons=SEASONS,
        player1_name=player1_name,
        player2_name=player2_name,
        player1_season=player1_season,
        player2_season=player2_season
    )


if __name__ == "__main__":
    app.run(debug=True)