"""
Servicios de eventos usando almacenamiento JSON.
"""

import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
from storage import (
    get_all_groups, create_event, get_event, take_event
)
from config import NSFW_EVENTS, CHARITY_EVENTS, RARITY_CONFIG


def create_and_broadcast_event(application, force_type=None):
    """
    Creates a global event and sends it to ALL registered groups.
    Called by scheduler automatically or by admin /evento command.
    force_type: "nsfw" or "charity" (None = random)
    """
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

    new_event = create_event(
        event_type=event_type,
        description=event_data["desc"],
        points=points
    )

    if not new_event:
        return None

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
        [InlineKeyboardButton("🤝 ¡RECLAMAR AHORA!", callback_data=f"claim_{new_event['id']}")]
    ])

    # Send to all registered groups
    groups = get_all_groups()

    for chat_id, group in groups.items():
        try:
            msg = application.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            # Save message info so we can edit it later
            new_event["chat_id"] = chat_id
            new_event["message_id"] = msg.message_id

        except Exception as e:
            print(f"Error sending event to group {chat_id}: {e}")

    return new_event["id"]


def get_event_by_id(event_id: int) -> dict | None:
    """Obtiene un evento por ID."""
    return get_event(event_id)


def take_event_by_user(event_id: int, user_id: int) -> bool:
    """Marca un evento como tomado por un usuario."""
    return take_event(event_id, user_id)
