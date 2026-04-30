"""
Handlers de comandos usando almacenamiento JSON.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from storage import get_user, create_user, add_group, get_all_groups, get_user_idols
from utils.formatter import format_user_profile
from config import ADMIN_IDS, PERSONAL_EVENTS
from services.events import create_and_broadcast_event
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    chat = update.effective_chat

    # Crear usuario si no existe
    user = get_user(user_tg.id)
    if not user:
        create_user(user_tg.id, username=user_tg.username or user_tg.first_name)
        user = get_user(user_tg.id)

    # Fallback por si user sigue siendo None
    if not user:
        user = {
            "id": user_tg.id,
            "username": user_tg.username or user_tg.first_name or "Unknown",
            "points": 1000,
            "wins": 0,
            "last_maintenance_check": datetime.utcnow().isoformat(),
            "idols": []
        }

    # Registrar grupo si es nuevo
    if chat.type in ("group", "supergroup"):
        groups = get_all_groups()
        if chat.id not in groups:
            add_group(chat.id, title=chat.title or "")

    kb = [
        [InlineKeyboardButton("👤 Perfil", callback_data=f"profile_{user_tg.id}"),
         InlineKeyboardButton("📖 Ayuda", callback_data=f"help_game_{user_tg.id}")],
        [InlineKeyboardButton("👯 Mis Idols", callback_data=f"idols_0_{user_tg.id}"),
         InlineKeyboardButton("🎰 Gacha (500 pts)", callback_data=f"gacha_{user_tg.id}")],
        [InlineKeyboardButton("🏪 Mercado", callback_data=f"market_0_{user_tg.id}"),
         InlineKeyboardButton("🧪 Fusión", callback_data=f"fusion_main_{user_tg.id}")],
        [InlineKeyboardButton("💰 Ganar Puntos", callback_data=f"help_pts_{user_tg.id}")],
    ]

    # Retry logic for flaky PythonAnywhere proxy
    for _ in range(3):
        try:
            await update.message.reply_text(
                f"🏠 *Panel de CEO — {user.get('username', user_tg.username)}*\n💰 Puntos: `{user.get('points', 0)}`",
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode="Markdown"
            )
            break
        except Exception as e:
            if "503" in str(e):
                import asyncio
                await asyncio.sleep(1)
                continue
            raise e


async def admin_evento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if ADMIN_IDS and uid not in ADMIN_IDS:
        await update.message.reply_text("❌ Sin permisos.")
        return

    ft = context.args[0].lower() if context.args else None
    eid = await create_and_broadcast_event(context.application, force_type=ft)

    if eid:
        await update.message.reply_text(f"✅ Evento #{eid} lanzado.")
    else:
        await update.message.reply_text("❌ Error al crear evento.")


async def admin_personal_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fuerza un evento personal para el admin (para pruebas)"""
    uid = update.effective_user.id

    if ADMIN_IDS and uid not in ADMIN_IDS:
        await update.message.reply_text("❌ Sin permisos.")
        return

    idols = get_user_idols(uid)
    if not idols:
        await update.message.reply_text("❌ No tienes idols para el evento.")
        return

    # Priorizar la que se está viendo, o elegir una al azar si no
    idx = context.user_data.get("current_idol_idx")
    if idx is None or idx >= len(idols):
        idx = random.randint(0, len(idols) - 1)
    
    idol = idols[idx]

    event = random.choice(PERSONAL_EVENTS)
    event_text = (
        f"⚡ *FORZAR EVENTO PERSONAL (Admin)*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✨ *{idol['name'].upper()}*\n\n"
        f"{event['desc']}\n\n"
        f"💰 Costo: `{event['cost_points']} pts`\n"
        f"📉 Talento: `-{event['stat_loss']}`\n"
        f"❤️ Moral: `+{event['moral_gain']}`\n"
        f"⚡ Energía: `+{event['energy_gain']}`\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    kb = [
        [InlineKeyboardButton("✅ Permitir", callback_data=f"pev_acc_{event['id']}_{idol['id']}_{idx}_{uid}")],
        [InlineKeyboardButton("❌ Denegar", callback_data=f"idols_{idx}_{uid}")]
    ]
    await update.message.reply_text(event_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = (
        "📖 *GUÍA DEL CEO DE IDOLS*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🎰 *Gacha:* Consigue nuevas idols por 500 pts.\n"
        "📀 *Comebacks:* Lanza álbumes. Dependen de Vocal, Dance y Rap.\n"
        "💪 *Entrenar:* Mejora las stats de tu idol por 200 pts.\n"
        "🔞 *Stats NSFW:* Influyen en los premios de Eventos Globales.\n"
        "✈️ *World Tour:* Envía a tu idol de gira (12h) para ganar puntos pasivos.\n"
        "🏪 *Mercado:* Compra y vende idols con otros jugadores.\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "👑 *COMANDOS DE ADMIN:*\n"
        "/evento — Lanza evento aleatorio\n"
        "/evento nsfw — Fuerza evento NSFW\n"
        "/evento charity — Fuerza evento de caridad"
    )
    await update.message.reply_text(t, parse_mode="Markdown")


async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    owner_id = int(parts[1]) if len(parts) > 1 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Este no es tu perfil.", show_alert=True)
        return

    user = get_user(q.from_user.id)
    if not user:
        create_user(q.from_user.id)
        user = get_user(q.from_user.id)

    # Contar idols del usuario
    from storage import get_user_idols
    idol_count = len(get_user_idols(q.from_user.id))

    text = format_user_profile(user, idol_count)

    await q.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{q.from_user.id}")]]),
        parse_mode="Markdown"
    )


async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    owner_id = int(parts[2]) if len(parts) > 2 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ No puedes usar el menú de otro CEO.", show_alert=True)
        return

    await q.answer()

    user = get_user(q.from_user.id)
    if not user:
        create_user(q.from_user.id)
        user = get_user(q.from_user.id)

    kb = [
        [InlineKeyboardButton("👤 Perfil", callback_data=f"profile_{q.from_user.id}"),
         InlineKeyboardButton("📖 Ayuda", callback_data=f"help_game_{q.from_user.id}")],
        [InlineKeyboardButton("👯 Mis Idols", callback_data=f"idols_0_{q.from_user.id}"),
         InlineKeyboardButton("🎰 Gacha (500 pts)", callback_data=f"gacha_{q.from_user.id}")],
        [InlineKeyboardButton("🏪 Mercado", callback_data=f"market_0_{q.from_user.id}"),
         InlineKeyboardButton("💰 Ganar Puntos", callback_data=f"help_pts_{q.from_user.id}")],
    ]

    for _ in range(3):
        try:
            await q.edit_message_text(
                f"🏠 *Panel de CEO*\n💰 Puntos: `{user.get('points', 0)}`",
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode="Markdown"
            )
            break
        except Exception as e:
            if "503" in str(e):
                import asyncio
                await asyncio.sleep(1)
                continue
            raise e
