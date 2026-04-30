"""
Servicios de economía usando almacenamiento JSON.
"""

import random
from typing import List
from datetime import datetime, timedelta
from storage import (
    get_user, update_user, add_points, deduct_points,
    get_all_idols, get_user_idols, get_idol, update_idol, create_idol, delete_idol,
    delete_idols_bulk,
    get_event, take_event, calculate_event_reward,
    create_user, get_all_users
)
from config import RARITY_CONFIG, COMEBACK_BASE_COST, MAINTENANCE_COST_BASE, TRAIN_COST, TRAIN_NSFW_COST

# NSFW Stat Emojis
NSFW_STAT_EMOJIS = {
    "sensitivity": "❤️",
    "coqueteo": "💕",
    "firmeza_culo": "🍑",
    "habilidades_cama": "🔥",
    "kinky": "😈"
}

NSFW_STAT_NAMES = {
    "sensitivity": "Sensibilidad",
    "coqueteo": "Coqueteo",
    "firmeza_culo": "Firmeza del Culo",
    "habilidades_cama": "Habilidades en la Cama",
    "kinky": "Kinky"
}


def _check_idol_busy(idol: dict) -> str | None:
    """
    Verifica si una idol está ocupada (tour o descanso).
    Si el tiempo ya pasó, la libera y devuelve None.
    Si sigue ocupada, devuelve el tipo de ocupación.
    """
    status = idol.get("status", "active")
    if status not in ["world_tour", "resting"]:
        return None

    if not idol.get("busy_until"):
        # Si no tiene tiempo pero el estado dice ocupada, la liberamos por seguridad
        idol["status"] = "active"
        update_idol(idol["id"], **{"status": "active", "busy_until": None})
        return None

    now = datetime.utcnow()
    busy_until = datetime.fromisoformat(idol["busy_until"])

    if now >= busy_until:
        # Ya terminó el tiempo
        idol["status"] = "active"
        idol["busy_until"] = None
        update_idol(idol["id"], **{"status": "active", "busy_until": None})
        return None

    return status


def process_maintenance(user_id: int) -> dict:
    """Dedica fees de mantenimiento; pone idols en hiatus si broke"""
    user = get_user(user_id)
    if not user:
        return {"success": False, "error": "user_not_found"}

    # Obtener todas las idols del usuario
    idols = get_user_idols(user_id)
    total_fee = len(idols) * MAINTENANCE_COST_BASE

    if user["points"] >= total_fee:
        deduct_points(user_id, total_fee)
        return {"success": True, "fee_paid": total_fee}
    else:
        # Poner todas las idols en hiatus
        for idol in idols:
            update_idol(idol["id"], status="hiatus")

        # Passive energy recovery (+10 per day, capped at 100)
        for idol in idols:
            idol["energy"] = min(100, idol["energy"] + 10)
            update_idol(idol["id"], **{"energy": idol["energy"]})

        return {"success": True, "fee_paid": total_fee, "hiatus_applied": True}


def perform_comeback(user_id: int, idol_id: int) -> dict | str:
    """Album release: costs points + energy, rewards based on stats/morale/rng"""
    idols = get_all_idols()
    if str(idol_id) not in idols:
        return "error"

    idol = idols[str(idol_id)]
    if idol["user_id"] != user_id:
        return "not_owner"

    template = {
        "rarity": idol["rarity"],
        "name": idol["name"]
    }

    user = get_user(user_id)
    if not user:
        return "error"

    if user["points"] < COMEBACK_BASE_COST:
        return "puntos_insuficientes"

    if idol["energy"] < 20:
        return "sin_energia"

    # Check busy status
    busy = _check_idol_busy(idol)
    if busy:
        return "ocupada"

    if idol["status"] != "active":
        return "no_disponible"

    # Deduct costs
    deduct_points(user_id, COMEBACK_BASE_COST)
    idol["energy"] = max(0, idol["energy"] - 20)
    update_idol(idol["id"], **{"energy": idol["energy"]})

    # Calculate score
    morale_mult = max(0.1, idol["morale"] / 100.0)
    total_stats = idol["vocal"] + idol["dance"] + idol["rap"]
    rarity_mult = RARITY_CONFIG[template["rarity"]]["mult"]
    rng_factor = random.uniform(0.5, 1.5)

    score = (total_stats / 300) * rarity_mult * rng_factor * (0.5 + 0.5 * morale_mult)

    if score > 2.0:
        result_type = "🏆 MEGA HIT"
        reward = int(COMEBACK_BASE_COST * score * 2)
    elif score > 1.0:
        result_type = "💿 HIT"
        reward = int(COMEBACK_BASE_COST * score * 1.5)
    else:
        result_type = "📉 FLOP"
        reward = int(COMEBACK_BASE_COST * score * 0.5)

    add_points(user_id, reward)

    return {
        "type": result_type,
        "reward": reward,
        "score": round(score, 2),
        "idol_name": template["name"]
    }


def train_idol(user_id: int, idol_id: int) -> dict | str:
    """Training: costs points, boosts a random stat, uses energy"""
    idols = get_all_idols()
    if str(idol_id) not in idols:
        return "error"

    idol = idols[str(idol_id)]
    if idol["user_id"] != user_id:
        return "not_owner"

    template = {"name": idol["name"]}
    user = get_user(user_id)
    if not user:
        return "error"

    # Check busy status
    busy = _check_idol_busy(idol)
    if busy:
        return "ocupada"

    if user["points"] < TRAIN_COST:
        return "puntos_insuficientes"
    if idol["energy"] < 15:
        return "sin_energia"

    # Deduct costs
    deduct_points(user_id, TRAIN_COST)
    idol["energy"] = max(0, idol["energy"] - 15)

    # Random stat boost
    stat = random.choice(["vocal", "dance", "rap"])
    boost = random.randint(1, 5)
    current = idol[stat]
    new_val = min(99, current + boost)
    idol[stat] = new_val

    update_idol(idol["id"], **{"energy": idol["energy"], stat: new_val})

    stat_emoji = {"vocal": "🎤", "dance": "💃", "rap": "🎧"}[stat]
    return {
        "stat": stat,
        "emoji": stat_emoji,
        "boost": boost,
        "new_val": new_val,
        "idol_name": template["name"]
    }


def train_nsfw(user_id: int, idol_id: int, stat_type: str) -> dict | str:
    """Entrena un stat NSFW específico"""
    idols = get_all_idols()
    if str(idol_id) not in idols:
        return "error"

    idol = idols[str(idol_id)]
    if idol["user_id"] != user_id:
        return "not_owner"

    template = {"name": idol["name"]}
    user = get_user(user_id)
    if not user:
        return "error"

    # Check busy status
    busy = _check_idol_busy(idol)
    if busy:
        return "ocupada"

    if user["points"] < TRAIN_NSFW_COST:
        return "puntos_insuficientes"
    if idol["energy"] < 15:
        return "sin_energia"

    # Deduct costs
    deduct_points(user_id, TRAIN_NSFW_COST)
    idol["energy"] = max(0, idol["energy"] - 15)

    # Boost random en el stat seleccionado
    boost = random.randint(1, 5)
    current = idol.get(stat_type, 50)
    new_val = min(100, current + boost)
    idol[stat_type] = new_val

    update_idol(idol["id"], **{"energy": idol["energy"], stat_type: new_val})

    return {
        "stat": NSFW_STAT_NAMES.get(stat_type, stat_type),
        "emoji": NSFW_STAT_EMOJIS.get(stat_type, "✨"),
        "boost": boost,
        "new_val": new_val,
        "idol_name": template["name"]
    }


def greet_idol(user_id: int, idol_id: int) -> dict | str:
    """Greet: costs a bit of energy, restores morale"""
    idols = get_all_idols()
    if str(idol_id) not in idols:
        return "error"

    idol = idols[str(idol_id)]
    if idol["user_id"] != user_id:
        return "not_owner"

    template = {"name": idol["name"]}

    # Check busy status
    busy = _check_idol_busy(idol)
    if busy:
        return "ocupada"

    morale_gain = random.randint(10, 25)
    energy_loss = random.randint(3, 8)
    idol["morale"] = min(100, idol.get("morale", 100) + morale_gain)
    idol["energy"] = max(0, idol.get("energy", 100) - energy_loss)

    update_idol(idol["id"], **{"morale": idol["morale"], "energy": idol["energy"]})

    return {
        "morale_gain": morale_gain,
        "new_morale": idol["morale"],
        "idol_name": template["name"]
    }


def rest_idol(user_id: int, idol_id: int) -> dict | str:
    """Rest: restores energy"""
    idols = get_all_idols()
    if str(idol_id) not in idols:
        return "error"

    idol = idols[str(idol_id)]
    if idol["user_id"] != user_id:
        return "not_owner"

    template = {"name": idol["name"]}

    # Check busy status
    busy = _check_idol_busy(idol)
    if busy:
        return "ocupada"

    from config import REST_DURATION_HOURS

    energy_gain = random.randint(20, 40)
    morale_loss = random.randint(1, 5)
    
    until = datetime.utcnow() + timedelta(hours=REST_DURATION_HOURS)
    
    idol["energy"] = min(100, idol.get("energy", 100) + energy_gain)
    idol["morale"] = max(0, idol.get("morale", 100) - morale_loss)
    idol["status"] = "resting"
    idol["busy_until"] = until.isoformat()

    update_idol(idol["id"], **{
        "energy": idol["energy"], 
        "morale": idol["morale"],
        "status": "resting",
        "busy_until": idol["busy_until"]
    })

    return {
        "energy_gain": energy_gain,
        "new_energy": idol["energy"],
        "idol_name": template["name"],
        "until": until
    }


def gacha_pull(user_id: int) -> dict | str:
    """Pulls a random idol for the user"""
    r = random.random()
    cumulative = 0
    chosen_rarity = 'C'

    rarity_order = ['C', 'B', 'A', 'S', 'SS', 'SSS']
    for rarity in rarity_order:
        chance = RARITY_CONFIG[rarity]['chance']
        cumulative += chance
        if r <= cumulative:
            chosen_rarity = rarity
            break

    # Get real idol templates
    template_names = {
        'C': [
            ("Haewon", "NMIXX"), ("Bae", "NMIXX"), ("Jiwoo", "NMIXX"), ("Kyujin", "NMIXX"),
            ("Mashiro", "Kep1er"), ("Chaehyun", "Kep1er"), ("Hikaru", "Kep1er"), ("Huening_Bahiyyih", "Kep1er"),
            ("Isa", "STAYC"), ("Seeun", "STAYC"), ("Sumin", "STAYC"), ("J", "STAYC"),
            ("Belle", "KISS OF LIFE"), ("Julie", "KISS OF LIFE"), ("Haneul", "KISS OF LIFE"),
            ("Iroha", "ILLIT"), ("Wonhee", "ILLIT"), ("Minju", "ILLIT"), ("Moka", "ILLIT"), ("Yunah", "ILLIT")
        ],
        'B': [
            ("Minji", "NewJeans"), ("Danielle", "NewJeans"), ("Liz", "IVE"), ("Eunchae", "LE SSERAFIM"),
            ("Xiaoting", "Kep1er"), ("Hyein", "NewJeans"), ("Lily", "NMIXX"), ("Sieun", "STAYC"), ("Yoon", "STAYC")
        ],
        'A': [
            ("Ryujin", "ITZY"), ("Rei", "IVE"), ("Yeji", "ITZY"), ("Nayeon", "TWICE"),
            ("Sana", "TWICE"), ("Natty", "KISS OF LIFE"), ("Yunjin", "LE SSERAFIM")
        ],
        'S': [
            ("Hanni", "NewJeans"), ("Winter", "aespa"), ("Sakura", "LE SSERAFIM"), ("Yujin", "IVE"),
            ("Kazuha", "LE SSERAFIM"), ("Mina", "TWICE"), ("Jihyo", "TWICE"), ("Haerin", "NewJeans")
        ],
        'SS': [
            ("Karina", "aespa", "Standard"), ("Wonyoung", "IVE", "Standard"), ("Yuna", "ITZY", "Standard"), ("Chaewon", "LE SSERAFIM", "Standard"),
            ("Lisa", "BLACKPINK", "Standard"), ("Jennie", "BLACKPINK", "Standard"), ("Momo", "TWICE", "Standard"), ("Sullyoon", "NMIXX", "Standard")
        ],
        'SSS': [
            ("Karina", "aespa", "Waterbomb"), ("Eunbi", "Soloist", "Waterbomb")
        ]
    }

    # Add default era to other rarities if they don't have it
    for rty in ['C', 'B', 'A', 'S']:
        template_names[rty] = [(t[0], t[1], "Standard") for t in template_names[rty]]
        
    # Overwrite some specific C rarities for the user request
    if chosen_rarity == 'C':
        template_names['C'].append(("Karina", "aespa", "Debut"))
        template_names['C'].append(("Eunbi", "IZ*ONE", "Produce 48"))

    name, group, era = random.choice(template_names[chosen_rarity])

    # Base stats by rarity
    base_stats = {
        'C': (10, 10, 10),
        'B': (20, 20, 20),
        'A': (35, 35, 35),
        'S': (50, 50, 50),
        'SS': (70, 70, 70),
        'SSS': (95, 95, 95)
    }

    vocal, dance, rap = base_stats[chosen_rarity]

    idol = create_idol(
        user_id=user_id,
        template_id=random.randint(1, 100),
        name=name.replace("_", " "),
        group_name=group,
        rarity=chosen_rarity,
        base_vocal=vocal,
        base_dance=dance,
        base_rap=rap,
        era=era
    )

    return idol


def gacha_pull_by_rarity(user_id: int, chosen_rarity: str) -> dict:
    """Pulls a random idol of a SPECIFIC rarity for the user"""
    
    # Template library (reused from gacha_pull logic)
    template_names = {
        'C': [
            ("Haewon", "NMIXX", "Standard"), ("Bae", "NMIXX", "Standard"), ("Jiwoo", "NMIXX", "Standard"), ("Kyujin", "NMIXX", "Standard"),
            ("Mashiro", "Kep1er", "Standard"), ("Chaehyun", "Kep1er", "Standard"), ("Hikaru", "Kep1er", "Standard"), ("Huening_Bahiyyih", "Kep1er", "Standard"),
            ("Isa", "STAYC", "Standard"), ("Seeun", "STAYC", "Standard"), ("Sumin", "STAYC", "Standard"), ("J", "STAYC", "Standard"),
            ("Belle", "KISS OF LIFE", "Standard"), ("Julie", "KISS OF LIFE", "Standard"), ("Haneul", "KISS OF LIFE", "Standard"),
            ("Iroha", "ILLIT", "Standard"), ("Wonhee", "ILLIT", "Standard"), ("Minju", "ILLIT", "Standard"), ("Moka", "ILLIT", "Standard"), ("Yunah", "ILLIT", "Standard"),
            ("Karina", "aespa", "Debut"), ("Eunbi", "IZ*ONE", "Produce 48")
        ],
        'B': [
            ("Minji", "NewJeans", "Standard"), ("Danielle", "NewJeans", "Standard"), ("Liz", "IVE", "Standard"), ("Eunchae", "LE SSERAFIM", "Standard"),
            ("Xiaoting", "Kep1er", "Standard"), ("Hyein", "NewJeans", "Standard"), ("Lily", "NMIXX", "Standard"), ("Sieun", "STAYC", "Standard"), ("Yoon", "STAYC", "Standard")
        ],
        'A': [
            ("Ryujin", "ITZY", "Standard"), ("Rei", "IVE", "Standard"), ("Yeji", "ITZY", "Standard"), ("Nayeon", "TWICE", "Standard"),
            ("Sana", "TWICE", "Standard"), ("Natty", "KISS OF LIFE", "Standard"), ("Yunjin", "LE SSERAFIM", "Standard")
        ],
        'S': [
            ("Hanni", "NewJeans", "Standard"), ("Winter", "aespa", "Standard"), ("Sakura", "LE SSERAFIM", "Standard"), ("Yujin", "IVE", "Standard"),
            ("Kazuha", "LE SSERAFIM", "Standard"), ("Mina", "TWICE", "Standard"), ("Jihyo", "TWICE", "Standard"), ("Haerin", "NewJeans", "Standard")
        ],
        'SS': [
            ("Karina", "aespa", "Standard"), ("Wonyoung", "IVE", "Standard"), ("Yuna", "ITZY", "Standard"), ("Chaewon", "LE SSERAFIM", "Standard"),
            ("Lisa", "BLACKPINK", "Standard"), ("Jennie", "BLACKPINK", "Standard"), ("Momo", "TWICE", "Standard"), ("Sullyoon", "NMIXX", "Standard")
        ],
        'SSS': [
            ("Karina", "aespa", "Waterbomb"), ("Eunbi", "Soloist", "Waterbomb")
        ]
    }

    name, group, era = random.choice(template_names[chosen_rarity])

    base_stats = {
        'C': (10, 10, 10), 'B': (20, 20, 20), 'A': (35, 35, 35),
        'S': (50, 50, 50), 'SS': (70, 70, 70), 'SSS': (95, 95, 95)
    }

    vocal, dance, rap = base_stats[chosen_rarity]

    return create_idol(
        user_id=user_id,
        template_id=random.randint(1, 1000),
        name=name.replace("_", " "),
        group_name=group,
        rarity=chosen_rarity,
        base_vocal=vocal,
        base_dance=dance,
        base_rap=rap,
        era=era
    )


def perform_fusion(user_id: int, idol_ids: List[int]) -> dict | str:
    """Fuses 3 idols into 1 new idol with better rarity chances"""
    if len(idol_ids) != 3:
        return "need_3_idols"

    all_idols = get_all_idols()
    fusing_idols = []
    
    for iid in idol_ids:
        if str(iid) not in all_idols:
            return "not_found"
        idol = all_idols[str(iid)]
        if idol["user_id"] != user_id:
            return "not_owner"
        if idol.get("for_sale"):
            return "idol_in_market"
        fusing_idols.append(idol)

    # Calculate Fusion Score
    # C=1, B=4, A=15, S=50, SS=150, SSS=500
    rarity_values = {'C': 1, 'B': 4, 'A': 15, 'S': 50, 'SS': 150, 'SSS': 500}
    total_score = sum(rarity_values[i["rarity"]] for i in fusing_idols)

    # Determine Result Rarity based on Score
    # 3x C (3 pts) -> C(60%), B(35%), A(5%)
    # 3x B (12 pts) -> B(50%), A(40%), S(9%), SS(1%)
    # 3x A (45 pts) -> A(50%), S(40%), SS(9%), SSS(1%)
    # Mixed: 1S + 2C (50 + 2 = 52 pts) -> Similar to 3x A
    
    r = random.random()
    if total_score < 10: # Tier 3C
        probs = {'C': 0.60, 'B': 0.95, 'A': 1.0}
    elif total_score < 30: # Tier 3B
        probs = {'B': 0.50, 'A': 0.90, 'S': 0.99, 'SS': 1.0}
    elif total_score < 100: # Tier 3A
        probs = {'A': 0.50, 'S': 0.90, 'SS': 0.99, 'SSS': 1.0}
    elif total_score < 300: # Tier 3S
        probs = {'S': 0.40, 'SS': 0.85, 'SSS': 1.0}
    else: # Tier 3SS+
        probs = {'SS': 0.30, 'SSS': 1.0}

    result_rarity = 'C'
    for rarity, threshold in probs.items():
        if r <= threshold:
            result_rarity = rarity
            break

    # Delete old idols in bulk
    delete_idols_bulk(idol_ids)

    # Pull new idol
    new_idol = gacha_pull_by_rarity(user_id, result_rarity)
    
    return {
        "new_idol": new_idol,
        "fused_names": [i["name"] for i in fusing_idols],
        "result_rarity": result_rarity
    }


def start_world_tour(user_id: int, idol_id: int) -> dict | str:
    """Locks an idol for world tour (12 hours)"""
    idols = get_all_idols()
    if str(idol_id) not in idols:
        return "error"

    idol = idols[str(idol_id)]
    if idol["user_id"] != user_id:
        return "not_owner"

    now = datetime.utcnow()

    # Check busy status
    busy = _check_idol_busy(idol)
    if busy == "world_tour":
        return "ya_en_tour"
    if busy:
        return "ocupada"

    if idol["status"] != "active":
        return "no_disponible"

    # Lock for 12 hours
    until = now + timedelta(hours=12)
    idol["status"] = "world_tour"
    idol["busy_until"] = until.isoformat()
    update_idol(idol["id"], **{"status": idol["status"], "busy_until": idol["busy_until"]})

    return {"until": until}


def list_idol_for_sale(user_id: int, idol_id: int, price: int) -> str:
    """Put an idol on the market"""
    idols = get_all_idols()
    if str(idol_id) not in idols:
        return "not_found"

    idol = idols[str(idol_id)]
    if idol["user_id"] != user_id:
        return "not_owner"

    if idol.get("for_sale", False):
        return "already_listed"

    idol["for_sale"] = True
    idol["sale_price"] = price
    update_idol(idol["id"], **{"for_sale": True, "sale_price": price})

    return "listed"


def buy_idol(buyer_id: int, idol_id: int) -> dict | str:
    """Buy an idol from the market"""
    idols = get_all_idols()
    if str(idol_id) not in idols:
        return "not_found"

    idol = idols[str(idol_id)]
    if not idol.get("for_sale", False):
        return "not_listed"

    seller_id = idol["user_id"]
    if seller_id == buyer_id:
        return "own_idol"

    buyer = get_user(buyer_id)
    if not buyer:
        return "no_buyer"

    if buyer["points"] < idol.get("sale_price", 0):
        return "no_points"

    seller = get_user(seller_id)

    # Transfer
    deduct_points(buyer_id, idol["sale_price"])
    add_points(seller_id, idol["sale_price"])
    idol["user_id"] = buyer_id
    idol["for_sale"] = False
    idol["sale_price"] = 0
    update_idol(idol["id"], **{"user_id": buyer_id, "for_sale": False, "sale_price": 0})

    return {
        "idol_name": idol["name"],
        "price": idol["sale_price"],
        "seller": seller.get("username", f"user_{seller_id}") if seller else "Unknown"
    }


def cancel_sale(user_id: int, idol_id: int) -> bool:
    """Remove idol from market"""
    idols = get_all_idols()
    if str(idol_id) not in idols:
        return False

    idol = idols[str(idol_id)]
    if idol["user_id"] != user_id:
        return False

    idol["for_sale"] = False
    idol["sale_price"] = 0
    update_idol(idol["id"], **{"for_sale": False, "sale_price": 0})

    return True


def calculate_event_reward(user_id: int, idol_id: int) -> dict | None:
    """Calcula recompensa basada en rareza + stats totales (básicos + NSFW)"""
    idols = get_all_idols()
    if str(idol_id) not in idols:
        return None

    idol = idols[str(idol_id)]
    if idol["user_id"] != user_id:
        return None

    # Stats básicos y NSFW
    basic_stats = idol.get("vocal", 0) + idol.get("dance", 0) + idol.get("rap", 0)
    nsfw_stats = (idol.get("sensitivity", 50) + idol.get("coqueteo", 50) +
                  idol.get("firmeza_culo", 50) + idol.get("habilidades_cama", 50) +
                  idol.get("kinky", 50))
    
    # En eventos NSFW, las stats NSFW pesan 3 veces más que las básicas
    weighted_total = (basic_stats * 0.5) + (nsfw_stats * 1.5)

    # Base points según rareza
    rarity_mult = RARITY_CONFIG[idol["rarity"]]["mult"]
    base_points = int(1000 * rarity_mult)

    # Bonus por stats (basado en el total pesado)
    stat_bonus = 1 + (weighted_total / 500)

    reward = int(base_points * stat_bonus)

    return {
        "reward": reward,
        "base_points": base_points,
        "rarity_mult": rarity_mult,
        "stat_bonus": round(stat_bonus, 2),
        "total_stats": int(weighted_total),
        "basic_stats": basic_stats,
        "nsfw_stats": nsfw_stats,
        "idol_name": idol["name"],
        "rarity": idol["rarity"]
    }
