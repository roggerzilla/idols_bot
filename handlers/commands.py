from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import AsyncSessionLocal
from models import User, UserIdol, IdolTemplate, BotGroup
from sqlalchemy import select
from utils.formatter import format_user_profile
from config import ADMIN_IDS
from services.events import create_and_broadcast_event

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    chat = update.effective_chat
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_tg.id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(id=user_tg.id, username=user_tg.username or user_tg.first_name)
            session.add(user)
            await session.commit()
        if chat.type in ("group", "supergroup"):
            existing = await session.execute(select(BotGroup).where(BotGroup.chat_id == chat.id))
            if not existing.scalar_one_or_none():
                session.add(BotGroup(chat_id=chat.id, title=chat.title or ""))
                await session.commit()
        kb = [
            [InlineKeyboardButton("👤 Perfil", callback_data="profile")],
            [InlineKeyboardButton("👯 Mis Idols", callback_data="idols_0")],
            [InlineKeyboardButton("🎰 Gacha (500 pts)", callback_data="gacha")],
            [InlineKeyboardButton("🏪 Mercado", callback_data="market_0")],
        ]
        await update.message.reply_text(
            f"🏠 *Panel de CEO — {user.username}*\n💰 Puntos: `{user.points}`",
            reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def admin_evento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if ADMIN_IDS and uid not in ADMIN_IDS:
        await update.message.reply_text("❌ Sin permisos.")
        return
    ft = context.args[0].lower() if context.args else None
    eid = await create_and_broadcast_event(context.application, force_type=ft)
    await update.message.reply_text(f"✅ Evento #{eid} lanzado." if eid else "❌ Error.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = ("📖 *COMANDOS*\n/start — Menú\n/ayuda — Ayuda\n"
         "/vender [precio] — Vender idol actual\n/quitarventa — Quitar del mercado\n"
         "👑 *ADMIN:*\n/evento — Evento NSFW\n/evento charity — Evento caridad")
    await update.message.reply_text(t, parse_mode="Markdown")

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    async with AsyncSessionLocal() as session:
        u = (await session.execute(select(User).where(User.id == q.from_user.id))).scalar_one()
        ic = len((await session.execute(select(UserIdol).where(UserIdol.user_id == u.id))).scalars().all())
        await q.edit_message_text(format_user_profile(u, ic),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data="back_main")]]),
            parse_mode="Markdown")

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    async with AsyncSessionLocal() as session:
        u = (await session.execute(select(User).where(User.id == q.from_user.id))).scalar_one()
        kb = [
            [InlineKeyboardButton("👤 Perfil", callback_data="profile")],
            [InlineKeyboardButton("👯 Mis Idols", callback_data="idols_0")],
            [InlineKeyboardButton("🎰 Gacha (500 pts)", callback_data="gacha")],
            [InlineKeyboardButton("🏪 Mercado", callback_data="market_0")],
        ]
        await q.edit_message_text(f"🏠 *Panel de CEO*\n💰 Puntos: `{u.points}`",
            reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
