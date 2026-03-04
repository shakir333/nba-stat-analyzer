import requests

BASE_URL = "https://data.nba.net/prod/v1"


def search_player(name):

    url = BASE_URL + "/2023/players.json"

    response = requests.get(url)

    data = response.json()

    players = data["league"]["standard"]

    for player in players:

        full_name = player["firstName"] + " " + player["lastName"]

        if name.lower() in full_name.lower():
            return full_name

    return None