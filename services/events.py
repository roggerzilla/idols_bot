import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from models import User, UserIdol, IdolTemplate, GlobalEvent, BotGroup
from database import AsyncSessionLocal
from config import NSFW_EVENTS, CHARITY_EVENTS, RARITY_CONFIG

async def create_and_broadcast_event(application, force_type=None):
    """
    Creates a global event and sends it to ALL registered groups.
    Called by scheduler automatically or by admin /evento command.
    force_type: "nsfw" or "charity" (None = random)
    """
    async with AsyncSessionLocal() as session:
        # Decide event type
        if force_type == "nsfw":
            is_charity = False
        elif force_type == "charity":
            is_charity = True
        else:
            is_charity = random.random() < 0.25  # 25% charity, 75% nsfw
        
        if is_charity:
            event_data = random.choice(CHARITY_EVENTS)
            points = random.randint(1000, 3000)  # Cost to participate
            event_type = "CHARITY"
        else:
            event_data = random.choice(NSFW_EVENTS)
            points = random.randint(3000, 15000)  # Reward
            event_type = "NSFW_SPONSOR"
        
        new_event = GlobalEvent(
            event_type=event_type,
            description=event_data["desc"],
            points=points
        )
        session.add(new_event)
        await session.commit()
        await session.refresh(new_event)
        
        # Build message
        if is_charity:
            text = (
                f"💖 *EVENTO GLOBAL: {event_data['title']}*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"{event_data['desc']}\n\n"
                f"💸 *Costo:* `{points} pts`\n"
                f"❤️ *Beneficio:* Moral de tu idol al MÁXIMO\n\n"
                f"⚡ _¡El primero en aceptar se lo lleva!_"
            )
        else:
            text = (
                f"🔥 *EVENTO GLOBAL: {event_data['title']}*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"{event_data['desc']}\n\n"
                f"💰 *Recompensa:* `{points} pts`\n"
                f"📉 *Riesgo:* La moral de tu idol bajará\n\n"
                f"⚡ _¡El primero en reclamar se lo lleva!_"
            )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🤝 ¡RECLAMAR AHORA!", callback_data=f"claim_{new_event.id}")]
        ])
        
        # Send to all registered groups
        groups = (await session.execute(select(BotGroup))).scalars().all()
        
        for group in groups:
            try:
                msg = await application.bot.send_message(
                    chat_id=group.chat_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                # Save message info so we can edit it later
                new_event.chat_id = group.chat_id
                new_event.message_id = msg.message_id
                await session.commit()
            except Exception as e:
                print(f"Error sending event to group {group.chat_id}: {e}")
        
        return new_event.id
