import os
from dotenv import load_dotenv

load_dotenv()

# Bot Token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Admin IDs (tu Telegram ID aquí para comandos de admin)
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# Database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'idols_bot.db')}"

# Game Constants
CONTRACT_DURATION_DAYS = 7
MAINTENANCE_COST_BASE = 50
COMEBACK_BASE_COST = 500
TRAIN_COST = 200
TRAIN_NSFW_COST = 200
GREET_ENERGY_COST = 10
REST_MORALE_COST = 5
REST_DURATION_HOURS = 2

# Rarity Multipliers
RARITY_CONFIG = {
    'C':  {'mult': 1.0,  'chance': 0.40},
    'B':  {'mult': 1.5,  'chance': 0.35},
    'A':  {'mult': 2.5,  'chance': 0.18},
    'S':  {'mult': 5.0,  'chance': 0.06},
    'SS': {'mult': 10.0, 'chance': 0.009},
    'SSS':{'mult': 25.0, 'chance': 0.001},
}

# NSFW Event Texts (variedad)
NSFW_EVENTS = [
    {
        "title": "🔞 PATROCINADOR VIP",
        "desc": "Un multimillonario busca compañía discreta para su fiesta privada en Mónaco.",
    },
    {
        "title": "🔞 SESIÓN EXCLUSIVA",
        "desc": "Una revista para adultos ofrece una portada exclusiva con pago inmediato.",
    },
    {
        "title": "🔞 CITA A CIEGAS",
        "desc": "Un heredero coreano busca una 'acompañante' para la gala anual del Lotte Hotel.",
    },
    {
        "title": "🔞 CONTRATO PRIVADO",
        "desc": "Un CEO de entretenimiento ofrece un 'contrato especial' fuera de cámaras.",
    },
    {
        "title": "🔞 FIESTA SECRETA",
        "desc": "Una celebridad de Hollywood invita a tu idol a una afterparty muy exclusiva.",
    },
]

CHARITY_EVENTS = [
    {
        "title": "💖 GALA BENÉFICA",
        "desc": "UNICEF busca una embajadora K-Pop para su gala anual. ¡Gran oportunidad para la moral!",
    },
    {
        "title": "💖 CONCIERTO SOLIDARIO",
        "desc": "Se organiza un concierto para víctimas de desastres. Tu idol puede participar.",
    },
]
