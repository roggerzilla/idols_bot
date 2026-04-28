from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import AsyncSessionLocal
from models import User, UserIdol
from sqlalchemy import select
from utils.formatter import format_user_profile

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg = update.effective_user
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_tg.id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(id=user_tg.id, username=user_tg.username or user_tg.first_name)
            session.add(user)
            await session.commit()
        
        keyboard = [
            [InlineKeyboardButton("👤 Mi Perfil", callback_data="profile"), InlineKeyboardButton("🚩 Fandoms", callback_data="fandoms_menu")],
            [InlineKeyboardButton("👯 Mis Idols", callback_data="my_idols")],
            [InlineKeyboardButton("🎰 Gacha (500 pts)", callback_data="gacha_pull")],
        ]
        await update.message.reply_text(f"🏠 *Panel de CEO - {user.username}*", 
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def fandoms_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🍭 ONCE", callback_data="join_ONCE"), InlineKeyboardButton("🦋 FEARNOT", callback_data="join_FEARNOT")],
        [InlineKeyboardButton("✨ DIVE", callback_data="join_DIVE")],
        [InlineKeyboardButton("🔙 Volver", callback_data="back_main")]
    ]
    await query.edit_message_text("🚩 *CENTRAL DE FANDOMS*\nÚnete a uno para ganar reputación y bonos globales.", 
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def join_fandom_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    f_name = query.data.split("_")[1]
    await query.edit_message_text(f"✅ ¡Bienvenido a la familia *{f_name}*!\nAhora tus idols representarán a este fandom.", 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data="back_main")]]), parse_mode="Markdown")

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.id == query.from_user.id))).scalar_one()
        idols_result = await session.execute(select(UserIdol).where(UserIdol.user_id == user.id))
        idols_count = len(idols_result.scalars().all())
        await query.edit_message_text(format_user_profile(user, idols_count), 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data="back_main")]]), parse_mode="Markdown")

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("👤 Mi Perfil", callback_data="profile"), InlineKeyboardButton("🚩 Fandoms", callback_data="fandoms_menu")],
        [InlineKeyboardButton("👯 Mis Idols", callback_data="my_idols")],
        [InlineKeyboardButton("🎰 Gacha (500 pts)", callback_data="gacha_pull")],
    ]
    await query.edit_message_text("🏠 *Menú Principal*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
