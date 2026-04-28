import random
from sqlalchemy import select
from models import User, UserIdol

async def trigger_random_global_event(context):
    """Triggered randomly by the scheduler"""
    async with AsyncSessionLocal() as session:
        points = random.randint(5000, 15000)
        new_event = GlobalEvent(event_type="NSFW_SPONSOR", points=points)
        session.add(new_event)
        await session.commit()
        
        # In a real bot, you'd send this to a main channel or all users
        # For now, let's assume we broadcast a message with a 'Claim' button
        text = (
            "🔥 *EVENTO GLOBAL LIMITADO*\n\n"
            "Un patrocinador VIP busca una compañía discreta para esta noche. "
            "¡La primera agencia en aceptar se lleva el contrato!\n\n"
            f"💰 *Recompensa:* `{points} pts`"
        )
        keyboard = [[InlineKeyboardButton("🤝 ¡ACEPTAR CONTRATO!", callback_data=f"claim_global_{new_event.id}")]]
        
        # We need a way to send to users. This is just a conceptual placeholder
        # In main.py we will register this.
        return text, keyboard

async def trigger_sponsor_event(session, user_id):
    """Event: NSFW Sponsor proposal"""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    
    # Randomize offer
    points_offered = random.randint(2000, 8000)
    
    event_text = (
        "🔞 *PROPUESTA DE PATROCINADOR*\n\n"
        "Un CEO de una marca de lujo ha contactado con tu agencia. "
        "Está dispuesto a financiar tu próximo comeback con una cifra astronómica... "
        "a cambio de una 'noche privada' con una de tus idols.\n\n"
        f"💰 *Oferta:* `{points_offered} pts`\n"
        "⚠️ *Consecuencia:* La moral de la idol bajará drásticamente."
    )
    
    return {
        "text": event_text,
        "points": points_offered,
        "moral_penalty": random.randint(30, 60)
    }

async def trigger_fan_scandal(session, user_id):
    """Event: Idol scandal (NSFW/Suggestive context)"""
    scandals = [
        "Se han filtrado fotos 'privadas' de tu idol en un club nocturno.",
        "Un paparazzi captó a tu idol saliendo de un hotel con un actor famoso.",
        "Tu idol publicó por error una foto sugerente en sus redes sociales."
    ]
    
    event_text = (
        "🔥 *ESCÁNDALO EN REDES*\n\n"
        f"{random.choice(scandals)}\n\n"
        "📉 El fandom está dividido. Pierdes puntos de reputación y moral."
    )
    
    return {
        "text": event_text,
        "moral_penalty": random.randint(15, 25),
        "point_loss": random.randint(500, 1500)
    }
