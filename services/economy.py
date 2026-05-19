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
    create_user, get_all_users, get_all_templates
)
from config import (
    TRAIN_COST, COMEBACK_BASE_COST, TRAIN_NSFW_COST,
    RARITY_CONFIG, MAINTENANCE_COST_BASE, INTERACT_OPTIONS, PERSONAL_EVENTS,
    NEXT_RARITY, EVOLUTION_COST, EVOLUTION_SUCCESS_RATE, ALL_STATS_KEYS
)

# NSFW Stat Emojis
NSFW_STAT_EMOJIS = {
    "sensualidad": "❤️",
    "puteria": "💋",
    "firmeza": "🍑",
    "habilidades_cama": "🔥",
    "fetiches": "😈"
}

NSFW_STAT_NAMES = {
    "sensualidad": "Sensualidad",
    "puteria": "Putería",
    "firmeza": "Firmeza culo/tetas",
    "habilidades_cama": "Habilidades en la Cama",
    "fetiches": "Fetiches"
}


def _check_idol_busy(idol: dict) -> str | None:
    """
    Verifica si una idol está ocupada (tour, descanso o comeback).
    Si el tiempo ya pasó, la libera y devuelve None.
    Si sigue ocupada, devuelve el tipo de ocupación.
    """
    status = idol.get("status", "active")
    if status not in ["world_tour", "resting", "comeback"]:
        return None

    if not idol.get("busy_until"):
        idol["status"] = "active"
        update_idol(idol["id"], **{"status": "active", "busy_until": None})
        return None

    now = datetime.utcnow()
    busy_until = datetime.fromisoformat(idol["busy_until"])

    if now >= busy_until:
        if status == "world_tour":
            total_stats = idol.get("vocal", 0) + idol.get("dance", 0) + idol.get("rap", 0)
            rarity_mult = RARITY_CONFIG.get(idol["rarity"], {"mult": 1.0})["mult"]
            tour_reward = int((total_stats * 10) * rarity_mult * random.uniform(0.8, 1.2))
            add_points(idol["user_id"], tour_reward)
            print(f"Tour finalizado para {idol['name']}. Recompensa: {tour_reward} pts")

        elif status == "comeback":
            morale_mult = max(0.1, idol.get("morale", 100) / 100.0)
            total_stats = idol.get("vocal", 0) + idol.get("dance", 0) + idol.get("rap", 0)
            rarity_mult = RARITY_CONFIG.get(idol["rarity"], {"mult": 1.0})["mult"]
            rng_factor = random.uniform(0.5, 1.5)
            score = (total_stats / 300) * rarity_mult * rng_factor * (0.5 + 0.5 * morale_mult)

            if score > 2.0:
                result_type = "MEGA HIT"
                reward = int(COMEBACK_BASE_COST * score * 2)
            elif score > 1.0:
                result_type = "HIT"
                reward = int(COMEBACK_BASE_COST * score * 1.5)
            else:
                result_type = "FLOP"
                reward = int(COMEBACK_BASE_COST * score * 0.5)

            add_points(idol["user_id"], reward)
            idol["comeback_result"] = {"type": result_type, "reward": reward, "score": round(score, 2)}
            update_idol(idol["id"], **{"comeback_result": idol["comeback_result"]})
            print(f"Comeback finalizado para {idol['name']}. {result_type}. Recompensa: {reward} pts")

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
    """Album release: costs points + energy, starts comeback with 30min delay"""
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

    # Verificar límite de 3 comebacks activos
    from storage import can_start_comeback
    if not can_start_comeback(user_id):
        return "limite_comebacks"

    # Deduct costs
    deduct_points(user_id, COMEBACK_BASE_COST)
    idol["energy"] = max(0, idol["energy"] - 20)

    # Set comeback status with 30 min timer
    from config import COMEBACK_DURATION_MINUTES
    until = datetime.utcnow() + timedelta(minutes=COMEBACK_DURATION_MINUTES)

    update_idol(idol["id"], **{
        "energy": idol["energy"],
        "status": "comeback",
        "busy_until": until.isoformat()
    })

    return {
        "type": "pending",
        "until": until,
        "idol_name": template["name"]
    }


def train_idol(user_id: int, idol_id: int, stat_type: str = None) -> dict | str:
    """Training: costs points, boosts a specific stat, uses energy"""
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

    # Stat boost
    possible_stats = ["vocal", "dance", "rap"]
    stat = stat_type if stat_type in possible_stats else random.choice(possible_stats)
    
    boost = random.randint(3, 8)
    current = idol.get(stat, 0)
    new_val = min(100, current + boost)
    idol[stat] = new_val

    update_idol(idol["id"], **{"energy": idol["energy"], stat: new_val})

    stat_emoji = {"vocal": "🎤", "dance": "💃", "rap": "🎧"}.get(stat, "✨")
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

    # Boost random entre 1 y 5 para evitar fiascos
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


def interact_idol(user_id: int, idol_id: int, interact_type: str) -> dict | str:
    """Reemplaza a Greet: Hacer Live o Instagram. Consume energía, sube moral random."""
    idols = get_all_idols()
    if str(idol_id) not in idols:
        return "error"

    idol = idols[str(idol_id)]
    if idol["user_id"] != user_id:
        return "not_owner"

    opt = INTERACT_OPTIONS.get(interact_type)
    if not opt:
        return "error"

    if idol["energy"] < opt["energy_cost"]:
        return "sin_energia"

    # Check busy status
    busy = _check_idol_busy(idol)
    if busy:
        return "ocupada"

    # Consumir energía
    idol["energy"] = max(0, idol["energy"] - opt["energy_cost"])

    # Determinar resultado
    r = random.random()
    cumulative = 0
    chosen_outcome = opt["outcomes"][-1]
    for outcome in opt["outcomes"]:
        cumulative += outcome["chance"]
        if r <= cumulative:
            chosen_outcome = outcome
            break

    # Aplicar moral
    idol["morale"] = min(100, idol.get("morale", 100) + chosen_outcome["moral"])
    update_idol(idol["id"], **{"morale": idol["morale"], "energy": idol["energy"]})

    return {
        "text": chosen_outcome["text"],
        "new_morale": idol["morale"],
        "new_energy": idol["energy"],
        "idol_name": idol["name"]
    }


def apply_personal_event(user_id: int, idol_id: int, event_id: str) -> dict | str:
    """Aplica las consecuencias de aceptar un evento personal (ej. visitar familia)"""
    idols = get_all_idols()
    if str(idol_id) not in idols:
        return "error"

    idol = idols[str(idol_id)]
    if idol["user_id"] != user_id:
        return "not_owner"

    event = next((e for e in PERSONAL_EVENTS if e["id"] == event_id), None)
    if not event:
        return "error"

    user = get_user(user_id)
    if user["points"] < event["cost_points"]:
        return "puntos_insuficientes"

    # Aplicar consecuencias
    deduct_points(user_id, event["cost_points"])
    
    # Perder stats básicos
    idol["vocal"] = max(0, idol["vocal"] - event["stat_loss"])
    idol["dance"] = max(0, idol["dance"] - event["stat_loss"])
    idol["rap"] = max(0, idol["rap"] - event["stat_loss"])
    
    # Ganar moral y energía
    idol["morale"] = min(100, idol.get("morale", 100) + event["moral_gain"])
    idol["energy"] = min(100, idol.get("energy", 100) + event["energy_gain"])
    
    update_idol(idol["id"], **{
        "vocal": idol["vocal"], 
        "dance": idol["dance"], 
        "rap": idol["rap"],
        "morale": idol["morale"],
        "energy": idol["energy"]
    })

    return {
        "title": event["title"],
        "cost": event["cost_points"],
        "stat_loss": event["stat_loss"],
        "moral_gain": event["moral_gain"],
        "energy_gain": event["energy_gain"],
        "idol_name": idol["name"]
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


def gacha_pull(user_id: int, force_rarity: str = None) -> dict | str:
    """Pulls a random idol for the user"""
    r = random.random()
    cumulative = 0
    chosen_rarity = force_rarity if force_rarity else 'C'

    if not force_rarity:
        rarity_order = ['C', 'B', 'A', 'S', 'SS', 'SSS']
        for rarity in rarity_order:
            chance = RARITY_CONFIG[rarity]['chance']
            cumulative += chance
            if r <= cumulative:
                chosen_rarity = rarity
                break

    # Load templates from JSON (Source of Truth)
    all_templates = get_all_templates()
    
    # Filter templates by rarity and can_gacha
    eligible_templates = []
    for tid, t in all_templates.items():
        if t.get("can_gacha", True) and t.get("rarity") == chosen_rarity:
            eligible_templates.append(t)

    # Fallback if no templates found for that rarity
    if not eligible_templates:
        return "error_no_templates"

    # Select random template
    template = random.choice(eligible_templates)
    name = template["name"]
    group = template["group_name"]
    era = template.get("era", "Standard")
    template_id = template["id"]

    # Base stats by rarity (using stats from template if available, or defaults)
    vocal = template.get("base_vocal", 10)
    dance = template.get("base_dance", 10)
    rap = template.get("base_rap", 10)

    idol = create_idol(
        user_id=user_id,
        template_id=template_id,
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
    # Simply reuse the main gacha_pull logic with fixed rarity
    return gacha_pull(user_id, force_rarity=chosen_rarity)


def perform_fusion(user_id: int, idol_ids: List[int]) -> dict | str:
    """Fuses 3 idols into 1 new idol with better rarity chances"""
    if len(idol_ids) != 3:
        return "need_3_idols"

    all_idols = get_all_idols()
    fusing_idols = []
    
    for iid in idol_ids:
        if str(iid) not in all_idols:
            return f"not_found_{iid}"
        idol = all_idols[str(iid)]
        if idol["user_id"] != user_id:
            return f"not_owner_{idol['name']}"
        if idol.get("for_sale"):
            return f"in_market_{idol['name']}"
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


def check_all_stats_100(idol: dict) -> bool:
    """Verifica si una idol tiene todas las stats al 100"""
    for stat in ALL_STATS_KEYS:
        if idol.get(stat, 0) < 100:
            return False
    return True


def evolve_idol(user_id: int, idol_id_a: int, idol_id_b: int) -> dict | str:
    """Evoluciona 2 idols del mismo nombre (era diferente) a la siguiente rareza"""
    idols = get_all_idols()

    if str(idol_id_a) not in idols:
        return "error"
    if str(idol_id_b) not in idols:
        return "error"

    idol_a = idols[str(idol_id_a)]
    idol_b = idols[str(idol_id_b)]

    if idol_a["user_id"] != user_id or idol_b["user_id"] != user_id:
        return "not_owner"

    if idol_a["id"] == idol_b["id"]:
        return "same_idol"

    # Verificar que tengan el mismo nombre
    if idol_a["name"] != idol_b["name"]:
        return "different_name"

    # Verificar que tengan eras diferentes
    if idol_a.get("era", "Standard") == idol_b.get("era", "Standard"):
        return "same_era"

    # Verificar que estén en la misma rareza
    if idol_a["rarity"] != idol_b["rarity"]:
        return "different_rarity"

    # Verificar que la rareza tenga evolución
    current_rarity = idol_a["rarity"]
    if current_rarity not in NEXT_RARITY:
        return "max_rarity"

    # Verificar que ambas tengan todas las stats al 100
    if not check_all_stats_100(idol_a):
        return "stats_low_a"
    if not check_all_stats_100(idol_b):
        return "stats_low_b"

    # Verificar que no estén en venta o en tour/resting
    for idol in [idol_a, idol_b]:
        if idol.get("for_sale"):
            return "in_market"
        busy = _check_idol_busy(idol)
        if busy:
            return "ocupada"

    # Verificar puntos suficientes
    cost = EVOLUTION_COST[current_rarity]
    user = get_user(user_id)
    if not user or user["points"] < cost:
        return "puntos_insuficientes"

    # Deducir puntos (se pierden siempre, éxito o fallo)
    deduct_points(user_id, cost)

    # Calcular probabilidad de éxito
    success_rate = EVOLUTION_SUCCESS_RATE[current_rarity]
    roll = random.random()
    success = roll <= success_rate

    if not success:
        # Fallo: conservar idols, perder puntos
        return {
            "success": False,
            "cost": cost,
            "current_rarity": current_rarity,
            "next_rarity": NEXT_RARITY[current_rarity],
            "idol_name": idol_a["name"]
        }

    # Éxito: buscar template del mismo nombre en la siguiente rareza
    next_rarity = NEXT_RARITY[current_rarity]
    all_templates = get_all_templates()

    # Buscar templates con el mismo nombre en la siguiente rareza
    matching_templates = []
    for tid, t in all_templates.items():
        if (t.get("name") == idol_a["name"] and
            t.get("rarity") == next_rarity and
            t.get("can_gacha", True)):
            matching_templates.append(t)

    # Si no hay del mismo nombre, elegir random de la siguiente rareza
    if not matching_templates:
        for tid, t in all_templates.items():
            if (t.get("rarity") == next_rarity and
                t.get("can_gacha", True)):
                matching_templates.append(t)

    if not matching_templates:
        # No hay templates disponibles, devolver puntos
        add_points(user_id, cost)
        return "no_templates"

    template = random.choice(matching_templates)

    # Eliminar las 2 idols originales
    delete_idols_bulk([idol_id_a, idol_id_b])

    # Crear nueva idol con stats base del template
    new_idol = create_idol(
        user_id=user_id,
        template_id=template["id"],
        name=template["name"].replace("_", " "),
        group_name=template.get("group_name", "Unknown"),
        rarity=next_rarity,
        base_vocal=template.get("base_vocal", 10),
        base_dance=template.get("base_dance", 10),
        base_rap=template.get("base_rap", 10),
        era=template.get("era", "Standard"),
    )

    return {
        "success": True,
        "new_idol": new_idol,
        "cost": cost,
        "current_rarity": current_rarity,
        "next_rarity": next_rarity,
        "idol_name": idol_a["name"]
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

    # Verificar límite de 3 tours activos
    from storage import can_start_tour
    if not can_start_tour(user_id):
        return "limite_tours"

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
    nsfw_stats = (idol.get("sensualidad", 50) + idol.get("puteria", 50) +
                  idol.get("firmeza", 50) + idol.get("habilidades_cama", 50) +
                  idol.get("fetiches", 50))
    
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
