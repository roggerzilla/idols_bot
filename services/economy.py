import random
import datetime
from sqlalchemy import select
from models import User, UserIdol, IdolTemplate, IdolStatus, GlobalEvent, BotGroup
from database import AsyncSessionLocal
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

async def process_maintenance(session, user_id):
    """Deducts maintenance fees; puts idols in hiatus if broke"""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user: return

    result = await session.execute(select(UserIdol).where(UserIdol.user_id == user_id))
    idols = result.scalars().all()
    
    total_fee = len(idols) * MAINTENANCE_COST_BASE
    
    if user.points >= total_fee:
        user.points -= total_fee
    else:
        for idol in idols:
            idol.status = IdolStatus.HIATUS
            
    # Passive energy recovery (+10 per day, capped at 100)
    for idol in idols:
        idol.energy = min(100, idol.energy + 10)
            
    await session.commit()

async def perform_comeback(session, user_id, idol_id):
    """Album release: costs points + energy, rewards based on stats/morale/rng"""
    result = await session.execute(
        select(UserIdol, IdolTemplate)
        .join(IdolTemplate)
        .where(UserIdol.id == idol_id, UserIdol.user_id == user_id)
    )
    data = result.first()
    if not data: return "error"
    
    idol, template = data
    
    user_result = await session.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()
    
    if user.points < COMEBACK_BASE_COST:
        return "puntos_insuficientes"
    
    if idol.energy < 20:
        return "sin_energia"
    
    if idol.status == IdolStatus.WORLD_TOUR:
        now = datetime.datetime.utcnow()
        if idol.busy_until and now < idol.busy_until:
            return "ocupada"
        else:
            idol.status = IdolStatus.ACTIVE
            idol.busy_until = None
    
    if idol.status != IdolStatus.ACTIVE:
        return "no_disponible"
    
    user.points -= COMEBACK_BASE_COST
    idol.energy -= 20
    
    # Score = stats * rarity * morale * rng
    morale_mult = max(0.1, idol.morale / 100.0)
    total_stats = idol.vocal + idol.dance + idol.rap
    rarity_mult = RARITY_CONFIG[template.rarity]['mult']
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
        
    user.points += reward
    await session.commit()
    
    return {"type": result_type, "reward": reward, "score": round(score, 2), "idol_name": template.name}

async def train_idol(session, user_id, idol_id):
    """Training: costs points, boosts a random stat, uses energy"""
    result = await session.execute(
        select(UserIdol, IdolTemplate)
        .join(IdolTemplate)
        .where(UserIdol.id == idol_id, UserIdol.user_id == user_id)
    )
    data = result.first()
    if not data: return "error"

    idol, template = data

    user_result = await session.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    if idol.status == IdolStatus.WORLD_TOUR:
        now = datetime.datetime.utcnow()
        if idol.busy_until and now < idol.busy_until:
            return "ocupada"
        else:
            idol.status = IdolStatus.ACTIVE
            idol.busy_until = None

    if user.points < TRAIN_COST:
        return "puntos_insuficientes"
    if idol.energy < 15:
        return "sin_energia"

    user.points -= TRAIN_COST
    idol.energy -= 15

    # Random stat boost
    stat = random.choice(["vocal", "dance", "rap"])
    boost = random.randint(1, 5)
    current = getattr(idol, stat)
    new_val = min(99, current + boost)
    setattr(idol, stat, new_val)

    await session.commit()

    stat_emoji = {"vocal": "🎤", "dance": "💃", "rap": "🎧"}[stat]
    return {"stat": stat, "emoji": stat_emoji, "boost": boost, "new_val": new_val, "idol_name": template.name}


async def train_nsfw(session, user_id, idol_id, stat_type):
    """Entrena un stat NSFW específico (sensitivity, coqueteo, firmeza_culo, habilidades_cama, kinky)"""
    result = await session.execute(
        select(UserIdol, IdolTemplate)
        .join(IdolTemplate)
        .where(UserIdol.id == idol_id, UserIdol.user_id == user_id)
    )
    data = result.first()
    if not data: return "error"

    idol, template = data

    user_result = await session.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    if idol.status == IdolStatus.WORLD_TOUR:
        now = datetime.datetime.utcnow()
        if idol.busy_until and now < idol.busy_until:
            return "ocupada"
        else:
            idol.status = IdolStatus.ACTIVE
            idol.busy_until = None

    if user.points < TRAIN_NSFW_COST:
        return "puntos_insuficientes"
    if idol.energy < 15:
        return "sin_energia"

    user.points -= TRAIN_NSFW_COST
    idol.energy -= 15

    # Boost random en el stat seleccionado
    boost = random.randint(1, 5)
    current = getattr(idol, stat_type)
    new_val = min(100, current + boost)
    setattr(idol, stat_type, new_val)

    await session.commit()

    stat_names = {
        "sensitivity": "Sensibilidad",
        "coqueteo": "Coqueteo",
        "firmeza_culo": "Firmeza del Culo",
        "habilidades_cama": "Habilidades en la Cama",
        "kinky": "Kinky"
    }
    stat_emojis = {
        "sensitivity": "❤️",
        "coqueteo": "💕",
        "firmeza_culo": "🍑",
        "habilidades_cama": "🔥",
        "kinky": "😈"
    }

    return {
        "stat": stat_names.get(stat_type, stat_type),
        "emoji": stat_emojis.get(stat_type, "✨"),
        "boost": boost,
        "new_val": new_val,
        "idol_name": template.name
    }

async def greet_idol(session, user_id, idol_id):
    """Greet: costs a bit of energy, restores morale"""
    result = await session.execute(
        select(UserIdol, IdolTemplate)
        .join(IdolTemplate)
        .where(UserIdol.id == idol_id, UserIdol.user_id == user_id)
    )
    data = result.first()
    if not data: return "error"
    
    idol, template = data
    
    if idol.status == IdolStatus.WORLD_TOUR:
        now = datetime.datetime.utcnow()
        if idol.busy_until and now < idol.busy_until:
            return "ocupada"
        else:
            idol.status = IdolStatus.ACTIVE
            idol.busy_until = None
    
    morale_gain = random.randint(10, 25)
    idol.morale = min(100, idol.morale + morale_gain)
    idol.energy = max(0, idol.energy - 5)
    
    await session.commit()
    return {"morale_gain": morale_gain, "new_morale": idol.morale, "idol_name": template.name}

async def rest_idol(session, user_id, idol_id):
    """Rest: restores energy"""
    result = await session.execute(
        select(UserIdol, IdolTemplate)
        .join(IdolTemplate)
        .where(UserIdol.id == idol_id, UserIdol.user_id == user_id)
    )
    data = result.first()
    if not data: return "error"
    
    idol, template = data
    
    if idol.status == IdolStatus.WORLD_TOUR:
        now = datetime.datetime.utcnow()
        if idol.busy_until and now < idol.busy_until:
            return "ocupada"
        else:
            idol.status = IdolStatus.ACTIVE
            idol.busy_until = None
    
    energy_gain = random.randint(20, 40)
    idol.energy = min(100, idol.energy + energy_gain)
    # Resting slightly reduces morale (idol gets bored)
    idol.morale = max(0, idol.morale - 3)
    
    await session.commit()
    return {"energy_gain": energy_gain, "new_energy": idol.energy, "idol_name": template.name}

async def gacha_pull(session, user_id):
    """Pulls a random idol for the user"""
    r = random.random()
    cumulative = 0
    chosen_rarity = 'C'
    for rarity, cfg in RARITY_CONFIG.items():
        cumulative += cfg['chance']
        if r <= cumulative:
            chosen_rarity = rarity
            break
            
    result = await session.execute(
        select(IdolTemplate).where(IdolTemplate.rarity == chosen_rarity)
    )
    templates = result.scalars().all()
    if not templates: return None
    
    template = random.choice(templates)
    
    new_idol = UserIdol(
        user_id=user_id,
        template_id=template.id,
        vocal=template.base_vocal,
        dance=template.base_dance,
        rap=template.base_rap,
        sensitivity=50,
        coqueteo=50,
        firmeza_culo=50,
        habilidades_cama=50,
        kinky=50,
        contract_expiry=datetime.datetime.utcnow() + datetime.timedelta(days=7)
    )
    
    session.add(new_idol)
    await session.commit()
    return template

async def start_world_tour(session, user_id, idol_id):
    """Locks an idol for world tour (12 hours)"""
    result = await session.execute(
        select(UserIdol).where(UserIdol.id == idol_id, UserIdol.user_id == user_id)
    )
    idol = result.scalar_one_or_none()
    if not idol: return "error"
    
    if idol.status == IdolStatus.WORLD_TOUR:
        now = datetime.datetime.utcnow()
        if idol.busy_until and now < idol.busy_until:
            return "ya_en_tour"
        else:
            idol.status = IdolStatus.ACTIVE
            idol.busy_until = None

    if idol.status != IdolStatus.ACTIVE:
        return "no_disponible"
        
    # Lock for 12 hours
    idol.status = IdolStatus.WORLD_TOUR
    idol.busy_until = datetime.datetime.utcnow() + datetime.timedelta(hours=12)
    await session.commit()
    return {"until": idol.busy_until}

# ─── MARKETPLACE ───

async def list_idol_for_sale(session, user_id, idol_id, price):
    """Put an idol on the market"""
    result = await session.execute(
        select(UserIdol).where(UserIdol.id == idol_id, UserIdol.user_id == user_id)
    )
    idol = result.scalar_one_or_none()
    if not idol: return "not_found"
    if idol.for_sale: return "already_listed"
    
    idol.for_sale = True
    idol.sale_price = price
    await session.commit()
    return "listed"

async def buy_idol(session, buyer_id, idol_id):
    """Buy an idol from the market"""
    result = await session.execute(
        select(UserIdol, IdolTemplate).join(IdolTemplate).where(UserIdol.id == idol_id, UserIdol.for_sale == True)
    )
    data = result.first()
    if not data: return "not_found"
    
    idol, template = data
    if idol.user_id == buyer_id: return "own_idol"
    
    buyer_result = await session.execute(select(User).where(User.id == buyer_id))
    buyer = buyer_result.scalar_one_or_none()
    if not buyer: return "no_buyer"
    
    if buyer.points < idol.sale_price: return "no_points"
    
    # Transfer
    seller_result = await session.execute(select(User).where(User.id == idol.user_id))
    seller = seller_result.scalar_one()
    
    buyer.points -= idol.sale_price
    seller.points += idol.sale_price
    idol.user_id = buyer_id
    idol.for_sale = False
    idol.sale_price = 0
    
    await session.commit()
    return {"idol_name": template.name, "price": idol.sale_price, "seller": seller.username}

async def cancel_sale(session, user_id, idol_id):
    """Remove idol from market"""
    result = await session.execute(
        select(UserIdol).where(UserIdol.id == idol_id, UserIdol.user_id == user_id)
    )
    idol = result.scalar_one_or_none()
    if not idol: return False
    idol.for_sale = False
    idol.sale_price = 0
    await session.commit()
    return True


async def calculate_event_reward(session, user_id, idol_id):
    """Calcula recompensa basada en rareza + stats totales (básicos + NSFW)"""
    result = await session.execute(
        select(UserIdol, IdolTemplate)
        .join(IdolTemplate)
        .where(UserIdol.id == idol_id, UserIdol.user_id == user_id)
    )
    data = result.first()
    if not data: return None

    idol, template = data

    # Stats básicos + NSFW
    basic_stats = idol.vocal + idol.dance + idol.rap
    nsfw_stats = (idol.sensitivity + idol.coqueteo + idol.firmeza_culo +
                  idol.habilidades_cama + idol.kinky)
    total_stats = basic_stats + nsfw_stats

    # Base points según rareza
    rarity_mult = RARITY_CONFIG[template.rarity]['mult']
    base_points = int(1000 * rarity_mult)  # Base: 1000, 1500, 2500, 5000, 10000

    # Bonus por stats (cada 100 stats da +10% de bonus)
    stat_bonus = 1 + (total_stats / 1000)

    reward = int(base_points * stat_bonus)

    return {
        "reward": reward,
        "base_points": base_points,
        "rarity_mult": rarity_mult,
        "stat_bonus": round(stat_bonus, 2),
        "total_stats": total_stats,
        "basic_stats": basic_stats,
        "nsfw_stats": nsfw_stats,
        "idol_name": template.name,
        "rarity": template.rarity
    }
