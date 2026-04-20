# NBA Player Analytics

A web-based NBA analytics tool that allows users to search players, view performance stats, and analyze trends.

## Features

- 🔍 Search for any NBA player
- 📊 View season averages (PPG, RPG, APG)
- 📈 Last 5 game performance tracking
- 🎨 Clean dark-themed UI

## Tech Stack

- Python (Flask)
- nba_api
- Pandas
- HTML / CSS

## How It Works

- User enters a player name
- Flask processes the request
- nba_api retrieves player game data
- Pandas calculates averages
- Results are displayed dynamically

## Future Improvements

- Player comparison tool
- Award race tracker (MVP, Finals MVP)
- Trending players section
- Advanced stats (FG%, 3P%, SPG, BPG)
- Custom award ranking system based on performance

## Run Locally

pip install flask nba_api pandas  
python app.py  

Then open: http://127.0.0.1:5000