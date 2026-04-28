from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import AsyncSessionLocal
from models import User, UserIdol, IdolTemplate, IdolStatus, GlobalEvent
from services.economy import gacha_pull, perform_comeback, start_world_tour
from services.events import trigger_sponsor_event
from utils.formatter import format_idol_card
from sqlalchemy import select
import random

async def gacha_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.id == user_id))).scalar_one()
        if user.points < 500:
            await query.answer("❌ No tienes suficientes puntos (500 pts).", show_alert=True)
            return
        user.points -= 500
        template = await gacha_pull(session, user_id)
        await query.edit_message_text(f"🎊 ¡Nueva idol reclutada: *{template.name}* de *{template.group_name}*!", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data="back_main")]]), parse_mode="Markdown")

async def my_idols_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserIdol, IdolTemplate).join(IdolTemplate).where(UserIdol.user_id == query.from_user.id)
        )
        idols = result.all()
        if not idols:
            await query.edit_message_text("📉 No tienes idols en tu staff.", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data="back_main")]]))
            return
        
        keyboard = [[InlineKeyboardButton(f"🎭 Gestionar {i.IdolTemplate.name}", callback_data=f"manage_{i.UserIdol.id}")] for i in idols]
        keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="back_main")])
        await query.edit_message_text("👯 *Tus Idols*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def manage_idol_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    idol_id = int(query.data.split("_")[1])
    async with AsyncSessionLocal() as session:
        data = (await session.execute(
            select(UserIdol, IdolTemplate).join(IdolTemplate).where(UserIdol.id == idol_id)
        )).first()
        text = format_idol_card(data.UserIdol, data.IdolTemplate)
        keyboard = [
            [InlineKeyboardButton("💿 Lanzar Comeback (500 pts)", callback_data=f"comeback_{idol_id}")],
            [InlineKeyboardButton("🤝 Sponsor Event (NSFW)", callback_data=f"sponsor_{idol_id}")],
            [InlineKeyboardButton("💪 Entrenar", callback_data=f"train_{idol_id}"), InlineKeyboardButton("✈️ World Tour", callback_data=f"tour_{idol_id}")],
            [InlineKeyboardButton("🔙 Volver", callback_data="my_idols")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def comeback_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    idol_id = int(query.data.split("_")[1])
    
    # EVENTO AUTOMÁTICO (20% probabilidad)
    if random.random() < 0.20:
        await sponsor_callback(update, context)
        return

    async with AsyncSessionLocal() as session:
        result = await perform_comeback(session, query.from_user.id, idol_id)
        if result == "sin_energia":
            await query.answer("😴 La idol está exhausta. Necesita descansar o entrenar.", show_alert=True)
            return
            
        await query.edit_message_text(f"💿 *RESULTADO:* {result['type']}\n📈 Charts Score: `{result['score']}`\n💰 Ganancia: `+{result['reward']} pts`", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"manage_{idol_id}")]]), parse_mode="Markdown")

async def claim_global_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """First-come-first-serve global event claim"""
    query = update.callback_query
    event_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(GlobalEvent).where(GlobalEvent.id == event_id))
        event = result.scalar_one_or_none()
        
        if not event or event.is_taken:
            await query.answer("❌ ¡Demasiado tarde! Otro CEO ya aceptó la oferta.", show_alert=True)
            return
            
        idol_result = await session.execute(
            select(UserIdol, IdolTemplate).join(IdolTemplate)
            .where(UserIdol.user_id == user_id)
            .order_by(IdolTemplate.rarity.desc())
        )
        data = idol_result.first()
        if not data:
            await query.answer("❌ Necesitas al menos una idol para aceptar patrocinadores.", show_alert=True)
            return
            
        idol, template = data
        event.is_taken = True
        event.taken_by_user_id = user_id
        
        rarity_bonus = {"C": 1, "B": 1.2, "A": 1.5, "S": 2, "SS": 3}.get(template.rarity, 1)
        final_points = int(event.points * rarity_bonus)
        
        user = (await session.execute(select(User).where(User.id == user_id))).scalar_one()
        user.points += final_points
        idol.morale = max(0, idol.morale - 30)
        
        await session.commit()
        
        await query.edit_message_text(
            f"🏆 *¡CONTRATO GLOBAL ASEGURADO!*\n\n"
            f"Tu agencia fue la más rápida. *{template.name}* ha cumplido con el contrato.\n"
            f"💰 Recibes: `{final_points} pts` (Bono x{rarity_bonus} por rareza {template.rarity}).\n"
            f"📉 Moral de {template.name} ha bajado.",
            parse_mode="Markdown"
        )

async def sponsor_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # Extraer ID independientemente del origen (menú o automático)
    idol_id = int(query.data.split("_")[-1])
    async with AsyncSessionLocal() as session:
        event = await trigger_sponsor_event(session, query.from_user.id)
        keyboard = [
            [InlineKeyboardButton("✅ Aceptar Oferta (NSFW)", callback_data=f"acc_sp_{idol_id}_{event['points']}_{event['moral_penalty']}")],
            [InlineKeyboardButton("❌ Rechazar", callback_data=f"manage_{idol_id}")]
        ]
        await query.edit_message_text(event['text'], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def accept_sponsor_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    parts = query.data.split("_")
    idol_id, points, penalty = int(parts[2]), int(parts[3]), int(parts[4])
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.id == query.from_user.id))).scalar_one()
        idol = (await session.execute(select(UserIdol).where(UserIdol.id == idol_id))).scalar_one()
        user.points += points
        idol.morale = max(0, idol.morale - penalty)
        await session.commit()
        
        await query.edit_message_text(f"🔞 *TRATO HECHO*\nHas ganado `{points} pts`. La moral de la idol ha caído por los suelos.", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"manage_{idol_id}")]]), parse_mode="Markdown")

async def tour_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    idol_id = int(query.data.split("_")[1])
    async with AsyncSessionLocal() as session:
        if await start_world_tour(session, query.from_user.id, idol_id):
            text = "✈️ *TOUR INICIADO*\nTu idol está de gira mundial generando beneficios."
        else:
            text = "❌ No se puede iniciar el tour. Verifica el estado de la idol."
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"manage_{idol_id}")]]), parse_mode="Markdown")
