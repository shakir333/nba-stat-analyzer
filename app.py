from flask import Flask, render_template, request
from stats_helper import get_player_stats

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/player")
def player():
    player_name = request.args.get("name")

    if not player_name:
        return render_template("player.html", error="No player name entered.")

    stats = get_player_stats(player_name)

    if not stats:
        return render_template("player.html", error="Player not found.")

    return render_template("player.html", stats=stats)


if __name__ == "__main__":
    app.run(debug=True)