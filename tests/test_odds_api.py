import os, requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("ODDS_API_KEY")
print("ODDS_API_KEY:", key[:6] + "..." if key else None)

url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
params = {"regions":"us,eu,br","markets":"h2h","oddsFormat":"decimal","apiKey":key}
r = requests.get(url, params=params, timeout=25)
print("HTTP:", r.status_code)
print(r.text[:600])
