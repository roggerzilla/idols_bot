"""
Handlers de comandos usando almacenamiento JSON.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from storage import get_user, create_user, add_group, get_all_groups
from utils.formatter import format_user_profile
from config import ADMIN_IDS
from services.events import create_and_broadcast_event


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
        [InlineKeyboardButton("👤 Perfil", callback_data="profile")],
        [InlineKeyboardButton("👯 Mis Idols", callback_data="idols_0"),
         InlineKeyboardButton("🎰 Gacha (500 pts)", callback_data="gacha")],
        [InlineKeyboardButton("🏪 Mercado", callback_data="market_0"),
         InlineKeyboardButton("💰 Ganar Puntos", callback_data="help_pts")],
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
    eid = create_and_broadcast_event(context.application, force_type=ft)

    if eid:
        await update.message.reply_text(f"✅ Evento #{eid} lanzado.")
    else:
        await update.message.reply_text("❌ Error al crear evento.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = ("📖 *COMANDOS*\n/startidols — Menú principal\n/ayuda — Ayuda\n"
         "👑 *ADMIN:*\n/evento — Evento aleatorio\n/evento nsfw — Forzar NSFW\n"
         "/evento charity — Forzar caridad")
    await update.message.reply_text(t, parse_mode="Markdown")


async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

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
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data="back_main")]]),
        parse_mode="Markdown"
    )


async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user = get_user(q.from_user.id)
    if not user:
        create_user(q.from_user.id)
        user = get_user(q.from_user.id)

    kb = [
        [InlineKeyboardButton("👤 Perfil", callback_data="profile")],
        [InlineKeyboardButton("👯 Mis Idols", callback_data="idols_0"),
         InlineKeyboardButton("🎰 Gacha (500 pts)", callback_data="gacha")],
        [InlineKeyboardButton("🏪 Mercado", callback_data="market_0"),
         InlineKeyboardButton("💰 Ganar Puntos", callback_data="help_pts")],
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
