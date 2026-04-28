import random
import datetime
from sqlalchemy import select
from models import User, UserIdol, IdolTemplate, IdolStatus
from config import RARITY_CONFIG, COMEBACK_BASE_COST, MAINTENANCE_COST_BASE

async def process_maintenance(session, user_id):
    """Checks and deducts maintenance fees for a user's idols"""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user: return

    result = await session.execute(select(UserIdol).where(UserIdol.user_id == user_id))
    idols = result.scalars().all()
    
    total_fee = len(idols) * MAINTENANCE_COST_BASE
    
    if user.points >= total_fee:
        user.points -= total_fee
        # Update contract logic here if needed
    else:
        # Put idols in hiatus if can't pay
        for idol in idols:
            idol.status = IdolStatus.HIATUS
            
    await session.commit()

async def perform_comeback(session, user_id, idol_id):
    """Calculates results for an album release"""
    result = await session.execute(
        select(UserIdol, IdolTemplate)
        .join(IdolTemplate)
        .where(UserIdol.id == idol_id, UserIdol.user_id == user_id)
    )
    data = result.first()
    if not data: return None
    
    idol, template = data
    
    # Check if user has points
    user_result = await session.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()
    
    if user.points < COMEBACK_BASE_COST:
        return "puntos_insuficientes"
    
    if idol.energy < 20:
        return "sin_energia"
    
    user.points -= COMEBACK_BASE_COST
    idol.energy -= 20
    
    # Logic: Stats + Rarity + RNG + MORALE
    morale_mult = idol.morale / 100.0
    total_stats = idol.vocal + idol.dance + idol.rap
    rarity_mult = RARITY_CONFIG[template.rarity]['mult']
    rng_factor = random.uniform(0.5, 1.5)
    
    # Base score influenced by morale
    score = (total_stats / 300) * rarity_mult * rng_factor * (0.5 + 0.5 * morale_mult)
    
    if score > 2.0:
        result_type = "Mega Hit"
        reward = int(COMEBACK_BASE_COST * score * 2)
    elif score > 1.0:
        result_type = "Hit"
        reward = int(COMEBACK_BASE_COST * score * 1.5)
    else:
        result_type = "Flop"
        reward = int(COMEBACK_BASE_COST * score * 0.5)
        
    user.points += reward
    await session.commit()
    
    return {
        "type": result_type,
        "reward": reward,
        "score": round(score, 2)
    }

async def gacha_pull(session, user_id):
    """Pulls a random idol for the user"""
    # 1. Determine rarity
    r = random.random()
    cumulative = 0
    chosen_rarity = 'C'
    for rarity, cfg in RARITY_CONFIG.items():
        cumulative += cfg['chance']
        if r <= cumulative:
            chosen_rarity = rarity
            break
            
    # 2. Get random template of that rarity
    result = await session.execute(
        select(IdolTemplate).where(IdolTemplate.rarity == chosen_rarity)
    )
    templates = result.scalars().all()
    if not templates: return None # Should not happen if DB is seeded
    
    template = random.choice(templates)
    
    # 3. Create UserIdol
    new_idol = UserIdol(
        user_id=user_id,
        template_id=template.id,
        vocal=template.base_vocal,
        dance=template.base_dance,
        rap=template.base_rap,
        contract_expiry=datetime.datetime.utcnow() + datetime.timedelta(days=7)
    )
    
    session.add(new_idol)
    await session.commit()
    return template

async def start_world_tour(session, user_id, idol_id):
    """Locks an idol for a world tour"""
    result = await session.execute(
        select(UserIdol).where(UserIdol.id == idol_id, UserIdol.user_id == user_id)
    )
    idol = result.scalar_one_or_none()
    if not idol or idol.status != IdolStatus.ACTIVE:
        return False
        
    idol.status = IdolStatus.WORLD_TOUR
    # In a real bot, we'd use a background task to unlock. 
    # For now, we'll just set the status.
    await session.commit()
    return True
