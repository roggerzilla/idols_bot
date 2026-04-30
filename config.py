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

# Eventos Personales (Random al ver la idol)
# Si se aceptan: pierden dinero y stats, pero ganan mucha moral y energía.
PERSONAL_EVENTS = [
    {
        "id": "family_visit",
        "title": "🏠 VISITA FAMILIAR",
        "desc": "Tu idol extraña a su familia y quiere ir a visitarlos por unos días.",
        "cost_points": 1000,
        "stat_loss": 5,
        "moral_gain": 50,
        "energy_gain": 50
    },
    {
        "id": "vacation",
        "title": "🏖️ MINI VACACIONES",
        "desc": "Tu idol se siente agotada y pide permiso para ir a la playa el fin de semana.",
        "cost_points": 1500,
        "stat_loss": 8,
        "moral_gain": 70,
        "energy_gain": 80
    },
    {
        "id": "birthday_party",
        "title": "🎂 FIESTA DE CUMPLEAÑOS",
        "desc": "Es el cumpleaños de tu idol y quiere organizar una fiesta privada con sus amigos.",
        "cost_points": 800,
        "stat_loss": 3,
        "moral_gain": 40,
        "energy_gain": 30
    },
    {
        "id": "mental_health",
        "title": "🧠 DESCANSO MENTAL",
        "desc": "Tu idol está bajo mucho estrés y necesita terapia y desconexión total.",
        "cost_points": 2000,
        "stat_loss": 10,
        "moral_gain": 90,
        "energy_gain": 100
    }
]

# Opciones de Interacción (Reemplaza a Saludar)
INTERACT_OPTIONS = {
    "instagram": {
        "name": "📸 Publicar en Instagram",
        "energy_cost": 10,
        "outcomes": [
            {"type": "flop", "chance": 0.2, "moral": 5, "text": "La publicación tuvo poco alcance... (Moral +5)"},
            {"type": "normal", "chance": 0.6, "moral": 15, "text": "¡A los fans les gustó la foto! (Moral +15)"},
            {"type": "viral", "chance": 0.2, "moral": 30, "text": "🔥 ¡LA FOTO SE HIZO VIRAL! Todo el mundo habla de ella. (Moral +30)"}
        ]
    },
    "live": {
        "name": "🎥 Hacer un Live (Weverse)",
        "energy_cost": 25,
        "outcomes": [
            {"type": "flop", "chance": 0.1, "moral": 10, "text": "Casi no hubo espectadores conectados... (Moral +10)"},
            {"type": "normal", "chance": 0.5, "moral": 35, "text": "¡Muchos fans enviaron corazones durante el live! (Moral +35)"},
            {"type": "viral", "chance": 0.4, "moral": 60, "text": "👑 ¡EL LIVE FUE ÉXITO TOTAL! Millones de corazones y tendencia global. (Moral +60)"}
        ]
    }
}
