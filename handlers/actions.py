from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import AsyncSessionLocal
from models import User, UserIdol, IdolTemplate, IdolStatus, GlobalEvent
from services.economy import (
    gacha_pull, perform_comeback, start_world_tour,
    train_idol, greet_idol, rest_idol, buy_idol, cancel_sale, list_idol_for_sale
)
from utils.formatter import format_idol_card, format_market_listing
from sqlalchemy import select
from config import RARITY_CONFIG

# ─── GACHA ───
async def gacha_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import asyncio
    import random
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    async with AsyncSessionLocal() as session:
        u = (await session.execute(select(User).where(User.id == uid))).scalar_one()
        if u.points < 500:
            await q.answer("❌ Necesitas 500 pts.", show_alert=True)
            return
        
        u.points -= 500
        await session.commit() # Commit point deduction before animation

        # Animation sequence
        frames = ["🎰 ✨", "🎰 🌟", "🎰 💎", "🎰 🌈"]
        for frame in frames:
            try:
                await q.edit_message_text(f"GIRANDO RULETA...\n\n{frame}")
            except:
                pass
            await asyncio.sleep(0.3)

        tmpl = await gacha_pull(session, uid)
        
        # Premium visuals based on rarity
        rarity_themes = {
            "C":  {"emoji": "⭐",       "border": "⚪", "title": "NUEVA ROOKIE"},
            "B":  {"emoji": "⭐⭐",      "border": "🟢", "title": "RISING STAR"},
            "A":  {"emoji": "⭐⭐⭐",     "border": "🔵", "title": "TALENTO ELITE"},
            "S":  {"emoji": "🌟🌟🌟🌟",    "border": "🟣", "title": "SUPERSTAR"},
            "SS": {"emoji": "💎💎💎💎💎", "border": "👑", "title": "DIOSA LEGENDARIA"},
        }
        theme = rarity_themes.get(tmpl.rarity, rarity_themes["C"])
        
        name = tmpl.name.replace("_", " ")
        group = tmpl.group_name.replace("_", " ")

        reveal_text = (
            f"{theme['border']} *{theme['title']}* {theme['border']}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✨ *{name.upper()}*\n"
            f"🏢 {group}\n"
            f"📊 Rareza: {theme['emoji']} ({tmpl.rarity})\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎤 {tmpl.base_vocal} | 💃 {tmpl.base_dance} | 🎧 {tmpl.base_rap}\n\n"
            f"💰 Puntos restantes: {u.points}"
        )

        await q.edit_message_text(
            reveal_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎰 Otro Gacha (500 pts)", callback_data="gacha")],
                [InlineKeyboardButton("🔙 Menú", callback_data="back_main")]
            ]), parse_mode="Markdown")

# ─── IDOL NAVIGATION (flat, with prev/next) ───
async def idols_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    idx = int(q.data.split("_")[1])
    uid = q.from_user.id
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserIdol, IdolTemplate).join(IdolTemplate).where(UserIdol.user_id == uid)
        )
        all_idols = result.all()
        if not all_idols:
            await q.edit_message_text("📉 No tienes idols. ¡Usa el Gacha!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data="back_main")]]))
            return
        idx = max(0, min(idx, len(all_idols) - 1))
        idol, tmpl = all_idols[idx]

        # Auto-refresh status if busy time passed
        import datetime
        if idol.status == IdolStatus.WORLD_TOUR and idol.busy_until:
            if datetime.datetime.utcnow() >= idol.busy_until:
                idol.status = IdolStatus.ACTIVE
                idol.busy_until = None
                await session.commit()

        # Store current idol index
        context.user_data["current_idol_id"] = idol.id
        context.user_data["current_idol_idx"] = idx
        text = format_idol_card(idol, tmpl, idx + 1, len(all_idols))
        nav = []
        if idx > 0:
            nav.append(InlineKeyboardButton("◀️", callback_data=f"idols_{idx - 1}"))
        nav.append(InlineKeyboardButton(f"{idx+1}/{len(all_idols)}", callback_data="noop"))
        if idx < len(all_idols) - 1:
            nav.append(InlineKeyboardButton("▶️", callback_data=f"idols_{idx + 1}"))
        kb = [
            nav,
            [InlineKeyboardButton("💿 Comeback", callback_data=f"cb_{idol.id}_{idx}"),
             InlineKeyboardButton("💪 Entrenar", callback_data=f"tr_{idol.id}_{idx}")],
            [InlineKeyboardButton("💬 Saludar", callback_data=f"gr_{idol.id}_{idx}"),
             InlineKeyboardButton("😴 Descansar", callback_data=f"rs_{idol.id}_{idx}")],
            [InlineKeyboardButton("✈️ Tour", callback_data=f"tour_{idol.id}_{idx}"),
             InlineKeyboardButton("🏷️ Vender", callback_data=f"sell_{idol.id}_{idx}")],
            [InlineKeyboardButton("🔙 Menú", callback_data="back_main")],
        ]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

# ─── COMEBACK ───
async def comeback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])
    async with AsyncSessionLocal() as session:
        r = await perform_comeback(session, q.from_user.id, iid)
        if r == "puntos_insuficientes":
            await q.answer("❌ Necesitas 500 pts.", show_alert=True); return
        if r == "sin_energia":
            await q.answer("😴 Sin energía. Descansa a tu idol.", show_alert=True); return
        if r == "ocupada":
            await q.answer("✈️ Idol en Tour. Espera a que regrese.", show_alert=True); return
        if r == "no_disponible":
            await q.answer("❌ Idol no disponible (hiatus o mercado).", show_alert=True); return
        if r == "error":
            await q.answer("❌ Error.", show_alert=True); return
        await q.edit_message_text(
            f"💿 *COMEBACK de {r['idol_name']}*\n━━━━━━━━━━━━━━━━━━\n"
            f"Resultado: *{r['type']}*\n📈 Score: `{r['score']}`\n💰 Ganancia: `+{r['reward']} pts`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}")]]),
            parse_mode="Markdown")

# ─── TRAIN ───
async def train_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])
    async with AsyncSessionLocal() as session:
        r = await train_idol(session, q.from_user.id, iid)
        if r == "puntos_insuficientes":
            await q.answer("❌ Necesitas 200 pts.", show_alert=True); return
        if r == "sin_energia":
            await q.answer("😴 Sin energía.", show_alert=True); return
        if r == "ocupada":
            await q.answer("✈️ Idol en Tour. Espera a que regrese.", show_alert=True); return
        if r == "error":
            await q.answer("❌ Error.", show_alert=True); return
        await q.edit_message_text(
            f"💪 *ENTRENAMIENTO de {r['idol_name']}*\n━━━━━━━━━━━━━━━━━━\n"
            f"{r['emoji']} {r['stat'].title()} subió `+{r['boost']}` → `{r['new_val']}`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}")]]),
            parse_mode="Markdown")

# ─── GREET ───
async def greet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])
    async with AsyncSessionLocal() as session:
        r = await greet_idol(session, q.from_user.id, iid)
        if r == "ocupada":
            await q.answer("✈️ Idol en Tour. Espera a que regrese.", show_alert=True); return
        if r == "error":
            await q.answer("❌ Error.", show_alert=True); return
        await q.edit_message_text(
            f"💬 *¡{r['idol_name']} está feliz!*\n❤️ Moral +{r['morale_gain']} → `{r['new_morale']}/100`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}")]]),
            parse_mode="Markdown")

# ─── REST ───
async def rest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])
    async with AsyncSessionLocal() as session:
        r = await rest_idol(session, q.from_user.id, iid)
        if r == "ocupada":
            await q.answer("✈️ Idol en Tour. Espera a que regrese.", show_alert=True); return
        if r == "error":
            await q.answer("❌ Error.", show_alert=True); return
        await q.edit_message_text(
            f"😴 *{r['idol_name']} descansó*\n⚡ Energía +{r['energy_gain']} → `{r['new_energy']}/100`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}")]]),
            parse_mode="Markdown")

# ─── TOUR ───
async def tour_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])
    async with AsyncSessionLocal() as session:
        r = await start_world_tour(session, q.from_user.id, iid)
        if isinstance(r, dict):
            # Show unlock time
            until = r['until'].strftime("%H:%M")
            t = f"✈️ *TOUR INICIADO*\n\nTu idol ha comenzado una gira mundial. Generará beneficios pasivos y regresará a las `{until} UTC`."
        elif r == "ya_en_tour":
            t = "✈️ Esta idol ya está en medio de un tour."
        else:
            t = "❌ No disponible para tour (debe estar activa y no en el mercado)."
        
        await q.edit_message_text(t,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}")]]),
            parse_mode="Markdown")

# ─── SELL (put on market) ───
async def sell_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])
    # Ask for price via preset buttons
    kb = [
        [InlineKeyboardButton("500 pts", callback_data=f"listsell_{iid}_{idx}_500"),
         InlineKeyboardButton("1000 pts", callback_data=f"listsell_{iid}_{idx}_1000")],
        [InlineKeyboardButton("2000 pts", callback_data=f"listsell_{iid}_{idx}_2000"),
         InlineKeyboardButton("5000 pts", callback_data=f"listsell_{iid}_{idx}_5000")],
        [InlineKeyboardButton("🔙 Cancelar", callback_data=f"idols_{idx}")],
    ]
    await q.edit_message_text("🏷️ *¿A qué precio quieres vender esta idol?*",
        reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def list_sell_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx, price = int(parts[1]), int(parts[2]), int(parts[3])
    async with AsyncSessionLocal() as session:
        r = await list_idol_for_sale(session, q.from_user.id, iid, price)
        if r == "listed":
            t = f"✅ Idol puesta en venta por `{price} pts`."
        else:
            t = "❌ No se pudo listar."
        await q.edit_message_text(t,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data="back_main")]]),
            parse_mode="Markdown")

# ─── MARKET ───
async def market_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    idx = int(q.data.split("_")[1])
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserIdol, IdolTemplate, User)
            .join(IdolTemplate, UserIdol.template_id == IdolTemplate.id)
            .join(User, UserIdol.user_id == User.id)
            .where(UserIdol.for_sale == True)
        )
        listings = result.all()
        if not listings:
            await q.edit_message_text("🏪 *MERCADO*\nNo hay idols en venta.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data="back_main")]]),
                parse_mode="Markdown")
            return
        idx = max(0, min(idx, len(listings) - 1))
        idol, tmpl, seller = listings[idx]
        text = f"🏪 *MERCADO* ({idx+1}/{len(listings)})\n━━━━━━━━━━━━━━━━━━\n"
        text += format_market_listing(idol, tmpl, seller.username)
        nav = []
        if idx > 0:
            nav.append(InlineKeyboardButton("◀️", callback_data=f"market_{idx-1}"))
        nav.append(InlineKeyboardButton(f"{idx+1}/{len(listings)}", callback_data="noop"))
        if idx < len(listings) - 1:
            nav.append(InlineKeyboardButton("▶️", callback_data=f"market_{idx+1}"))
        kb = [nav,
              [InlineKeyboardButton(f"💰 Comprar ({idol.sale_price} pts)", callback_data=f"buy_{idol.id}")],
              [InlineKeyboardButton("🔙 Menú", callback_data="back_main")]]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    iid = int(q.data.split("_")[1])
    async with AsyncSessionLocal() as session:
        r = await buy_idol(session, q.from_user.id, iid)
        if r == "no_points":
            await q.answer("❌ Puntos insuficientes.", show_alert=True); return
        if r == "own_idol":
            await q.answer("❌ No puedes comprar tu propia idol.", show_alert=True); return
        if isinstance(r, str):
            await q.answer(f"❌ {r}", show_alert=True); return
        await q.edit_message_text(f"✅ *¡Compraste a {r['idol_name']}!*",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data="back_main")]]),
            parse_mode="Markdown")

# ─── CLAIM GLOBAL EVENT ───
async def claim_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    eid = int(q.data.split("_")[1])
    uid = q.from_user.id
    async with AsyncSessionLocal() as session:
        ev = (await session.execute(select(GlobalEvent).where(GlobalEvent.id == eid))).scalar_one_or_none()
        if not ev or ev.is_taken:
            await q.answer("❌ ¡Tarde! Ya lo reclamaron.", show_alert=True); return
        u = (await session.execute(select(User).where(User.id == uid))).scalar_one_or_none()
        if not u:
            await q.answer("❌ Usa /start primero.", show_alert=True); return
        idol_r = await session.execute(
            select(UserIdol, IdolTemplate).join(IdolTemplate)
            .where(UserIdol.user_id == uid).order_by(IdolTemplate.rarity.desc()))
        data = idol_r.first()
        if not data:
            await q.answer("❌ Necesitas una idol.", show_alert=True); return
        idol, tmpl = data
        ev.is_taken = True
        ev.taken_by_user_id = uid
        rb = {"C":1,"B":1.2,"A":1.5,"S":2,"SS":3}.get(tmpl.rarity, 1)
        if ev.event_type == "CHARITY":
            if u.points < ev.points:
                await q.answer("❌ Puntos insuficientes.", show_alert=True); return
            u.points -= ev.points
            idol.morale = 100
            result_text = (f"💖 *{u.username}* aceptó la gala benéfica con *{tmpl.name}*!\n"
                          f"❤️ Moral restaurada al MÁXIMO.\n💸 Gastó `{ev.points} pts`.")
        else:
            fp = int(ev.points * rb)
            u.points += fp
            idol.morale = max(0, idol.morale - 30)
            result_text = (f"🔞 *{u.username}* aceptó el contrato con *{tmpl.name}*!\n"
                          f"💰 Ganó `{fp} pts` (x{rb} por rareza {tmpl.rarity}).\n"
                          f"📉 Moral de {tmpl.name} bajó.")
        await session.commit()
        await q.edit_message_text(result_text, parse_mode="Markdown")

# ─── NOOP (for page indicators) ───
async def noop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
