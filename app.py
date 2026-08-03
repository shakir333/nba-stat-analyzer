from flask import Flask, abort, render_template, request

from compare import compare_players
from stats_helper import (
    get_available_seasons,
    get_player_stats,
    get_standings,
    get_team,
    get_teams,
)


app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/player")
def player():
    seasons = get_available_seasons()
    player_name = request.args.get("name", "").strip()
    season = request.args.get("season") or (seasons[0] if seasons else "2025-26")

    if not player_name:
        return render_template(
            "player.html", error="No player name entered.", seasons=seasons
        )

    stats = get_player_stats(player_name, season)
    if not stats:
        return render_template(
            "player.html",
            error=f"No stored data found for {player_name} in {season}.",
            seasons=seasons,
        )

    return render_template("player.html", stats=stats, seasons=seasons)


@app.route("/compare", methods=["GET", "POST"])
def compare():
    seasons = get_available_seasons()
    default_season = seasons[0] if seasons else "2025-26"
    result = None
    error = None
    player1_name = ""
    player2_name = ""
    player1_season = default_season
    player2_season = default_season

    if request.method == "POST":
        player1_name = request.form.get("player1", "").strip()
        player2_name = request.form.get("player2", "").strip()
        player1_season = request.form.get("player1_season", default_season)
        player2_season = request.form.get("player2_season", default_season)

        if not player1_name or not player2_name:
            error = "Please enter both player names."
        elif (
            player1_name.casefold() == player2_name.casefold()
            and player1_season == player2_season
        ):
            error = "Please choose different players or different seasons."
        else:
            result = compare_players(
                player1_name, player1_season, player2_name, player2_season
            )
            if not result["success"]:
                error = result["error"]
                result = None

    return render_template(
        "compare.html",
        result=result,
        error=error,
        seasons=seasons,
        player1_name=player1_name,
        player2_name=player2_name,
        player1_season=player1_season,
        player2_season=player2_season,
    )


@app.route("/teams")
def teams():
    return render_template("teams.html", teams=get_teams())


@app.route("/standings")
def standings():
    standings_data = get_standings(request.args.get("season"))
    if standings_data is None:
        return render_template(
            "standings.html",
            error="Standings data has not been imported yet.",
        )
    return render_template("standings.html", **standings_data)


@app.route("/teams/<abbreviation>")
def team(abbreviation):
    team_data = get_team(abbreviation)
    if team_data is None:
        abort(404)
    return render_template("team.html", team=team_data)


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
