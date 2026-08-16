import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY")

if not TELEGRAM_TOKEN or not API_FOOTBALL_KEY:
    raise ValueError("TELEGRAM_TOKEN and API_FOOTBALL_KEY must be set")

API_BASE_URL = "https://v3.football.api-sports.io"
