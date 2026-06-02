from flask import Flask, render_template, request
from stats_helper import get_player_stats

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
    stats = get_player_stats(player_name, season)

    print("Selected player:", player_name)
    print("Selected season:", season)
                              

    if not player_name:
        return render_template("player.html", error="No player name entered.", seasons=SEASONS)

    stats = get_player_stats(player_name, season)

    if not stats:
        return render_template("player.html", error="Player not found.", seasons=SEASONS)

    return render_template("player.html", stats=stats, seasons=SEASONS)


if __name__ == "__main__":
    app.run(debug=True)