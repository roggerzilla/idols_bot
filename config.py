import os
from dotenv import load_dotenv

load_dotenv()

# Bot Token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


# Database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'idols_bot.db')}"

# Game Constants
CONTRACT_DURATION_DAYS = 7
MAINTENANCE_COST_BASE = 50
MORALE_DECREASE_RATE = 5 # Daily
HIATUS_THRESHOLD_HOURS = 48

# Rarity Multipliers
RARITY_CONFIG = {
    'C': {'mult': 1.0, 'chance': 0.50},
    'B': {'mult': 1.5, 'chance': 0.30},
    'A': {'mult': 2.5, 'chance': 0.15},
    'S': {'mult': 5.0, 'chance': 0.04},
    'SS': {'mult': 10.0, 'chance': 0.01},
}

# Comeback Costs
COMEBACK_BASE_COST = 500
