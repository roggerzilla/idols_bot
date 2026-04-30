"""
Handlers usando almacenamiento JSON.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import random
import asyncio
import time
from datetime import datetime
from storage import (
    get_user, update_user, add_points, deduct_points,
    get_all_idols, get_user_idols, get_idol, update_idol, create_idol, delete_idol,
    get_event, take_event, get_all_events, get_all_groups, add_group
)
from services.economy import (
    gacha_pull, perform_comeback, start_world_tour,
    train_idol, rest_idol, buy_idol, cancel_sale, list_idol_for_sale,
    train_nsfw, calculate_event_reward, perform_fusion,
    interact_idol, apply_personal_event
)
from utils.formatter import format_idol_card, format_market_listing
from config import RARITY_CONFIG, PERSONAL_EVENTS, INTERACT_OPTIONS

# NSFW Stat Emojis
NSFW_STAT_EMOJIS = {
    "sensitivity": "❤️",
    "coqueteo": "💕",
    "firmeza_culo": "🍑",
    "habilidades_cama": "🔥",
    "kinky": "😈"
}

NSFW_STAT_NAMES = {
    "sensitivity": "Sensibilidad",
    "coqueteo": "Coqueteo",
    "firmeza_culo": "Firmeza del Culo",
    "habilidades_cama": "Habilidades en la Cama",
    "kinky": "Kinky"
}

# ─── GACHA ───
async def gacha_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    owner_id = int(parts[1]) if len(parts) > 1 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Este no es tu menú de Gacha.", show_alert=True)
        return

    uid = q.from_user.id

    u = get_user(uid)
    if not u or u.get("points", 0) < 500:
        await q.edit_message_text(
            f"❌ *PUNTOS INSUFICIENTES*\n\nNecesitas `500 pts` para usar el Gacha.\n💰 Tus puntos: `{u['points'] if u else 0}`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data="back_main")]]),
            parse_mode="Markdown"
        )
        return

    await q.answer()

    # Deduct points
    deduct_points(uid, 500)

    # Pull idol
    new_idol = gacha_pull(uid)

    if not new_idol:
        await q.answer("❌ Error en gacha", show_alert=True)
        return

    # Premium visuals based on rarity
    rarity_themes = {
        "C":  {"emoji": "⭐",       "border": "⚪", "title": "NUEVA ROOKIE"},
        "B":  {"emoji": "⭐⭐",      "border": "🟢", "title": "RISING STAR"},
        "A":  {"emoji": "⭐⭐⭐",     "border": "🔵", "title": "TALENTO ELITE"},
        "S":  {"emoji": "🌟🌟🌟🌟",    "border": "🟣", "title": "SUPERSTAR"},
        "SS": {"emoji": "💎💎💎💎💎", "border": "👑", "title": "DIOSA LEGENDARIA"},
        "SSS":{"emoji": "👑👑👑👑👑👑", "border": "✨", "title": "ENTIDAD DIVINA"},
    }

    theme = rarity_themes.get(new_idol["rarity"], rarity_themes["C"])

    name = new_idol["name"].replace("_", " ")
    group = new_idol["group_name"].replace("_", " ")

    u = get_user(uid)

    reveal_text = (
        f"{theme['border']} *{theme['title']}* {theme['border']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✨ *{name.upper()}*\n"
        f"🏢 {group}\n"
        f"📊 Rareza: {theme['emoji']} ({new_idol['rarity']})\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎤 {new_idol['vocal']} | 💃 {new_idol['dance']} | 🎧 {new_idol['rap']}\n\n"
        f"💰 Puntos restantes: `{u.get('points', 0)}`"
    )

    await q.edit_message_text(
        reveal_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎰 Otro Gacha (500 pts)", callback_data=f"gacha_{uid}")],
            [InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{uid}")]
        ]), parse_mode="Markdown")


# ─── IDOL NAVIGATION (flat, with prev/next) ───
async def idols_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    idx = int(parts[1]) if len(parts) > 1 else 0
    owner_id = int(parts[2]) if len(parts) > 2 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ No puedes mover las idols de otro CEO.", show_alert=True)
        return

    uid = q.from_user.id
    all_idols = get_user_idols(uid)

    if not all_idols:
        await q.edit_message_text("📉 No tienes idols. ¡Usa el Gacha!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{uid}")]]))
        return

    idx = max(0, min(idx, len(all_idols) - 1))
    idol = all_idols[idx]

    # --- NUEVO: Trigger de Evento Personal (5% chance + Cooldown) ---
    now = time.time()
    last_event = context.user_data.get("last_personal_event", 0)
    
    if (now - last_event > 30) and random.random() < 0.05:
        context.user_data["last_personal_event"] = now
        # Buscar una idol que necesite el evento (prioridad moral baja)
        available_idols = [i for i in all_idols if i["status"] == "active" and not i.get("for_sale")]
        
        if available_idols:
            # Priorizar las que tienen moral < 50
            low_morale = [i for i in available_idols if i.get("morale", 100) < 50]
            target_idol = random.choice(low_morale if low_morale else available_idols)
            
            # Encontrar el índice real de la target_idol en la lista completa para el botón "Denegar"
            target_idx = next((i for i, d in enumerate(all_idols) if d["id"] == target_idol["id"]), idx)
            
            event = random.choice(PERSONAL_EVENTS)
            event_text = (
                f"⚡ *MENSAJE DE MANAGER*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"✨ *{target_idol['name'].upper()}* tiene una petición:\n\n"
                f"*{event['title']}*\n"
                f"{event['desc']}\n\n"
                f"💰 Costo: `{event['cost_points']} pts`\n"
                f"📉 Talento: `-{event['stat_loss']}` (V/D/R)\n"
                f"❤️ Moral: `+{event['moral_gain']}`\n"
                f"⚡ Energía: `+{event['energy_gain']}`\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"¿Permites que se tome este descanso?"
            )
            event_kb = [
                [InlineKeyboardButton("✅ Permitir", callback_data=f"pev_acc_{event['id']}_{target_idol['id']}_{target_idx}_{uid}")],
                [InlineKeyboardButton("❌ Denegar", callback_data=f"idols_{idx}_{uid}")]
            ]
            await q.edit_message_text(event_text, reply_markup=InlineKeyboardMarkup(event_kb), parse_mode="Markdown")
            return

    # Store current idol index
    context.user_data["current_idol_id"] = idol["id"]
    context.user_data["current_idol_idx"] = idx

    card_text = format_idol_card(idol, None, idx + 1, len(all_idols))
    text = card_text

    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"idols_{idx - 1}_{uid}"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{len(all_idols)}", callback_data="noop"))
    if idx < len(all_idols) - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"idols_{idx + 1}_{uid}"))

    kb = [
        nav,
        [InlineKeyboardButton("💿 Comeback", callback_data=f"cb_{idol['id']}_{idx}_{uid}")],
        [InlineKeyboardButton("💪 Entrenar", callback_data=f"tr_{idol['id']}_{idx}_{uid}")],
        [InlineKeyboardButton("🔞 Stats NSFW", callback_data=f"nsfw_info_{idol['id']}_{idx}_{uid}")],
        [InlineKeyboardButton("📱 Interactuar", callback_data=f"int_menu_{idol['id']}_{idx}_{uid}")],
        [InlineKeyboardButton("😴 Descansar", callback_data=f"rs_{idol['id']}_{idx}_{uid}")],
        [InlineKeyboardButton("✈️ Tour", callback_data=f"tour_{idol['id']}_{idx}_{uid}")],
        [InlineKeyboardButton("🏷️ Vender", callback_data=f"sell_{idol['id']}_{idx}_{uid}")],
        [InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{uid}")],
    ]

    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


# ─── COMEBACK ───
async def comeback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])
    owner_id = int(parts[3]) if len(parts) > 3 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ No puedes ordenar acciones a idols de otros.", show_alert=True)
        return

    r = perform_comeback(q.from_user.id, iid)

    if r == "puntos_insuficientes":
        await q.answer("❌ Necesitas 500 pts.", show_alert=True); return
    if r == "sin_energia":
        await q.answer("😴 Sin energía. Descansa a tu idol.", show_alert=True); return
    if r == "ocupada":
        await q.answer("✈️ Idol en Tour. Espera a que regrese.", show_alert=True); return
    if r == "no_disponible":
        await q.answer("❌ Idol no disponible (hiatus o mercado).", show_alert=True); return
    if r == "error" or r == "not_owner":
        await q.answer("❌ Error.", show_alert=True); return

    await q.edit_message_text(
        f"💿 *COMEBACK de {r['idol_name']}*\n━━━━━━━━━━━━━━━━━━\n"
        f"Resultado: *{r['type']}*\n📈 Score: `{r['score']}`\n💰 Ganancia: `+{r['reward']} pts`",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]]) ,
        parse_mode="Markdown")


# ─── TRAIN ───
async def train_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])
    owner_id = int(parts[3]) if len(parts) > 3 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Este entrenamiento no es tuyo.", show_alert=True)
        return

    r = train_idol(q.from_user.id, iid)

    if r == "puntos_insuficientes":
        await q.answer("❌ Necesitas 200 pts.", show_alert=True); return
    if r == "sin_energia":
        await q.answer("😴 Sin energía.", show_alert=True); return
    if r == "ocupada":
        await q.answer("✈️ Idol en Tour. Espera a que regrese.", show_alert=True); return
    if r == "error" or r == "not_owner":
        await q.answer("❌ Error.", show_alert=True); return

    await q.edit_message_text(
        f"💪 *ENTRENAMIENTO de {r['idol_name']}*\n━━━━━━━━━━━━━━━━━━\n"
        f"{r['emoji']} {r['stat'].title()} subió `+{r['boost']}` → `{r['new_val']}`",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]]) ,
        parse_mode="Markdown")


# ─── INTERACT ───
async def interact_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra opciones de interacción (Live / Instagram)"""
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[2]), int(parts[3])
    owner_id = int(parts[4]) if len(parts) > 4 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ No es tu idol.", show_alert=True); return

    await q.answer()

    text = (
        "📱 *MENÚ DE INTERACCIÓN*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Elige cómo quieres que tu idol conecte con sus fans hoy. "
        "Esto subirá su moral pero consumirá energía.\n\n"
        "📸 *Instagram:* Menos energía, moral moderada.\n"
        "🎥 *Live:* Mucha energía, moral alta (¡puede ser viral!)."
    )

    kb = [
        [InlineKeyboardButton(INTERACT_OPTIONS["instagram"]["name"], callback_data=f"int_exe_instagram_{iid}_{idx}_{owner_id}")],
        [InlineKeyboardButton(INTERACT_OPTIONS["live"]["name"], callback_data=f"int_exe_live_{iid}_{idx}_{owner_id}")],
        [InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]
    ]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


async def interact_execute_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ejecuta la interacción elegida"""
    q = update.callback_query
    parts = q.data.split("_")
    # int_exe_{type}_{iid}_{idx}_{owner_id}
    itype = parts[2]
    iid, idx, owner_id = int(parts[3]), int(parts[4]), int(parts[5])

    if q.from_user.id != owner_id:
        await q.answer("❌ No es tu idol.", show_alert=True); return

    r = interact_idol(q.from_user.id, iid, itype)

    if r == "sin_energia":
        await q.answer("😴 Sin energía para esto.", show_alert=True); return
    if r == "ocupada":
        await q.answer("✈️ Idol ocupada.", show_alert=True); return
    if r == "error" or r == "not_owner":
        await q.answer("❌ Error.", show_alert=True); return

    await q.edit_message_text(
        f"📱 *INTERACCIÓN: {r['idol_name']}*\n━━━━━━━━━━━━━━━━━━\n"
        f"{r['text']}\n\n"
        f"❤️ Moral: `{r['new_morale']}/100`\n"
        f"⚡ Energía: `{r['new_energy']}/100`",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]]),
        parse_mode="Markdown"
    )


# ─── PERSONAL EVENTS ───
async def personal_event_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa la aceptación de un evento personal"""
    q = update.callback_query
    parts = q.data.split("_")
    # pev_acc_{ev_id}_{iid}_{idx}_{owner_id}
    # Como ev_id puede tener guiones bajos, contamos desde el final
    owner_id = int(parts[-1])
    idx = int(parts[-2])
    iid = int(parts[-3])
    ev_id = "_".join(parts[2:-3])

    if q.from_user.id != owner_id:
        await q.answer("❌ No es tu idol.", show_alert=True); return

    r = apply_personal_event(q.from_user.id, iid, ev_id)

    if r == "puntos_insuficientes":
        await q.answer("❌ No tienes suficientes puntos.", show_alert=True); return
    if r == "error":
        await q.answer("❌ Error al procesar evento.", show_alert=True); return

    result_text = (
        f"✅ *PERMISO CONCEDIDO: {r['title']}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Has permitido que *{r['idol_name']}* se tome un descanso personal.\n\n"
        f"💰 Pagaste: `-{r['cost']} pts` en gastos y logística.\n"
        f"📉 El descanso afectó su práctica: `-{r['stat_loss']}` Talentos.\n"
        f"💖 Pero su felicidad es máxima: `+{r['moral_gain']} Moral` y `+{r['energy_gain']} Energía`.\n"
        f"━━━━━━━━━━━━━━━━━━"
    )

    await q.edit_message_text(
        result_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]]),
        parse_mode="Markdown"
    )


# ─── REST ───
async def rest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])
    owner_id = int(parts[3]) if len(parts) > 3 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ No puedes dormir a idols de otros.", show_alert=True)
        return

    r = rest_idol(q.from_user.id, iid)

    if r == "ocupada":
        await q.answer("✈️ Idol ocupada (Tour o Descanso).", show_alert=True); return
    if r == "error" or r == "not_owner":
        await q.answer("❌ Error.", show_alert=True); return
        
    # Show wake up time
    until = r['until'].strftime("%H:%M")
    await q.edit_message_text(
        f"😴 *{r['idol_name']} se fue a dormir*\n⚡ Energía +{r['energy_gain']} → `{r['new_energy']}/100`\n"
        f"Regresará a las `{until} UTC`.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]]),
        parse_mode="Markdown")


# ─── TOUR ───
async def tour_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])
    owner_id = int(parts[3]) if len(parts) > 3 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Solo el dueño puede iniciar tours.", show_alert=True)
        return

    r = start_world_tour(q.from_user.id, iid)

    if isinstance(r, dict):
        # Show unlock time
        until = r['until'].strftime("%H:%M")
        t = f"✈️ *TOUR INICIADO*\n\nTu idol ha comenzado una gira mundial. Generará beneficios pasivos y regresará a las `{until} UTC`."
    elif r == "ya_en_tour":
        t = "✈️ Esta idol ya está en medio de un tour."
    else:
        t = "❌ No disponible para tour (debe estar activa y no en el mercado)."

    await q.edit_message_text(t,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]]) ,
        parse_mode="Markdown")


# ─── SELL (put on market) ───
async def sell_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])
    owner_id = int(parts[3]) if len(parts) > 3 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Este no es tu menú de venta.", show_alert=True)
        return

    kb = [
        [InlineKeyboardButton("500 pts", callback_data=f"listsell_{iid}_{idx}_500_{owner_id}"),
         InlineKeyboardButton("1000 pts", callback_data=f"listsell_{iid}_{idx}_1000_{owner_id}")],
        [InlineKeyboardButton("2000 pts", callback_data=f"listsell_{iid}_{idx}_2000_{owner_id}"),
         InlineKeyboardButton("5000 pts", callback_data=f"listsell_{iid}_{idx}_5000_{owner_id}")],
        [InlineKeyboardButton("🔙 Cancelar", callback_data=f"idols_{idx}_{owner_id}")],
    ]

    await q.edit_message_text("🏷️ *¿A qué precio quieres vender esta idol?*",
        reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


async def list_sell_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx, price = int(parts[1]), int(parts[2]), int(parts[3])
    owner_id = int(parts[4]) if len(parts) > 4 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Solo el dueño puede listar idols.", show_alert=True)
        return

    r = list_idol_for_sale(q.from_user.id, iid, price)

    if r == "listed":
        t = f"✅ Idol puesta en venta por `{price} pts`."
    else:
        t = "❌ No se pudo listar."

    await q.edit_message_text(t,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{q.from_user.id}")]]),
        parse_mode="Markdown")


# ─── MARKET ───
async def market_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    idx = int(parts[1]) if len(parts) > 1 else 0
    owner_id = int(parts[2]) if len(parts) > 2 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Abre el mercado tú mismo para navegar.", show_alert=True)
        return

    # Get all idols for sale
    all_idols = get_all_idols()
    listings = [idol for idol in all_idols.values() if idol.get("for_sale", False)]

    if not listings:
        await q.edit_message_text("🏪 *MERCADO*\nNo hay idols en venta.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{owner_id}")]]),
            parse_mode="Markdown")
        return

    idx = max(0, min(idx, len(listings) - 1))
    idol = listings[idx]

    text = f"🏪 *MERCADO* ({idx+1}/{len(listings)})\n━━━━━━━━━━━━━━━━━━\n"
    text += format_market_listing(idol, None, f"user_{idol['user_id']}")

    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"market_{idx-1}_{owner_id}"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{len(listings)}", callback_data="noop"))
    if idx < len(listings) - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"market_{idx + 1}_{owner_id}"))

    kb = [nav,
          [InlineKeyboardButton(f"💰 Comprar ({idol['sale_price']} pts)", callback_data=f"buy_{idol['id']}")],
          [InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{owner_id}")]]

    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


async def buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    iid = int(q.data.split("_")[1])

    r = buy_idol(q.from_user.id, iid)

    if r == "no_points":
        await q.answer("❌ Puntos insuficientes.", show_alert=True); return
    if r == "own_idol":
        await q.answer("❌ No puedes comprar tu propia idol.", show_alert=True); return
    if isinstance(r, str):
        await q.answer(f"❌ {r}", show_alert=True); return

    await q.edit_message_text(f"✅ *¡Compraste a {r['idol_name']}!*",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{q.from_user.id}")]]),
        parse_mode="Markdown")


# ─── SELECT IDOL FOR EVENT ───
async def select_idol_for_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra lista de idols para seleccionar en evento NSFW"""
    q = update.callback_query
    await q.answer()

    parts = q.data.split("_")
    eid = int(parts[2]) if len(parts) > 2 else 0
    idx = int(parts[3]) if len(parts) > 3 else 0
    owner_id = int(parts[4]) if len(parts) > 4 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Este menú de selección no es tuyo.", show_alert=True)
        return

    uid = q.from_user.id
    all_idols = get_user_idols(uid)

    if not all_idols:
        await q.edit_message_text(
            "📉 *NO Tienes idols*\n¡Usa el Gacha primero!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"back_main_{owner_id}")]]),
            parse_mode="Markdown"
        )
        return

    idx = max(0, min(idx, len(all_idols) - 1))
    idol = all_idols[idx]

    # Calcular stats totales para mostrar
    total_basic = idol.get("vocal", 0) + idol.get("dance", 0) + idol.get("rap", 0)
    total_nsfw = (idol.get("sensitivity", 50) + idol.get("coqueteo", 50) +
                  idol.get("firmeza_culo", 50) +
                  idol.get("habilidades_cama", 50) + idol.get("kinky", 50))

    card_text = (f"🔞 *SELECCIONA IDOL PARA EVENTO*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"✨ *{idol['name'].replace('_', ' ').upper()}* {idol.get('group_name', '')}\n"
                f"📊 Rareza: {'⭐' * (['C','B','A','S','SS','SSS'].index(idol['rarity']) + 1)} ({idol['rarity']})\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🎤 {idol.get('vocal', 0)} | 💃 {idol.get('dance', 0)} | 🎧 {idol.get('rap', 0)}\n"
                f"💪 Stats Básicos: `{total_basic}`\n\n"
                f"❤️ {idol.get('sensitivity', 50)} | 💕 {idol.get('coqueteo', 50)} | 🍑 {idol.get('firmeza_culo', 50)}\n"
                f"🔥 {idol.get('habilidades_cama', 50)} | 😈 {idol.get('kinky', 50)}\n"
                f"💪 Stats NSFW: `{total_nsfw}`\n\n"
                f"📈 Total Stats: `{total_basic + total_nsfw}`")

    # Botones para otras idols
    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"sel_event_{eid}_{idx - 1}_{owner_id}"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{len(all_idols)}", callback_data="noop"))
    if idx < len(all_idols) - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"sel_event_{eid}_{idx + 1}_{owner_id}"))

    kb = [
        nav,
        [InlineKeyboardButton(f"🔞 USAR ESTA IDOL", callback_data=f"use_idol_{eid}_{idol['id']}_{owner_id}")],
        [InlineKeyboardButton("🔙 Cancelar", callback_data=f"claim_{eid}")]
    ]

    await q.edit_message_text(
        card_text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )


# ─── USE IDOL FOR EVENT ───
async def use_idol_for_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ejecuta evento NSFW con la idol seleccionada"""
    q = update.callback_query
    parts = q.data.split("_")
    eid = int(parts[2])
    iid = int(parts[3])
    owner_id = int(parts[4]) if len(parts) > 4 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ No puedes usar idols ajenas en este evento.", show_alert=True)
        return

    # Calcular recompensa
    reward_data = calculate_event_reward(q.from_user.id, iid)

    if not reward_data:
        await q.answer("❌ Error al calcular recompensa.", show_alert=True)
        return

    # Variaciones de texto NSFW según stats
    nsfw_variants = [
        f"🔞 *{reward_data['idol_name']}* protagonizó una sesión de fotos picante para una revista exclusiva donde los camarógrafos no se pudieron resistir y uno a uno tomaron turnos follando cada uno de sus agujeros mientras el patrocinador esperaba su turno con ansias.",
        f"🔞 *{reward_data['idol_name']}* participó en un show privado de alta gama para fans VIP donde la ropa quedó tirada al suelo y fue penetrada por tres a la vez hasta que sus piernas temblaban de placer sucio.",
        f"🔞 *{reward_data['idol_name']}* fue la imagen principal de una campaña de lencería de lujo, pero terminó desnuda bajo las luces mientras le chupaban el clítoris para capturar su gemido más auténtico en cámara.",
        f"🔞 *{reward_data['idol_name']}* grabó un comercial provocativo que se volvió tendencia en redes, mostrando cómo lamió la lengua de su modelo mientras él le llenaba la boca con saliva y semen.",
        f"🔞 *{reward_data['idol_name']}* asistió como invitada especial a una fiesta privada de la élite de Gangnam donde fue atada al sofá y usada por los invitados hasta que amaneció sucia y exhausta.",
        f"🔞 *{reward_data['idol_name']}* aceptó un patrocinio arriesgado para una marca de bebidas para adultos, terminando con el líquido cayendo sobre su vientre mientras la lameran desde los pechos hasta el coño."
    ]

    # 1. Bloquear el evento para que nadie más lo use
    if not take_event(eid, q.from_user.id):
        await q.answer("❌ El evento ya no está disponible.", show_alert=True)
        return

    # 2. Añadir puntos al CEO
    add_points(q.from_user.id, reward_data['reward'])

    # 3. Penalizar moral y energía de la idol (Riesgo del evento NSFW)
    new_morale = max(0, reward_data.get('morale', 100) - 20)
    new_energy = max(0, reward_data.get('energy', 100) - 15)
    update_idol(iid, morale=new_morale, energy=new_energy)

    story = random.choice(nsfw_variants)

    result_text = (f"🔥 *¡CONTRATO FIRMADO!*\n{story}\n\n"
                  f"👤 CEO: *{q.from_user.username}*\n"
                  f"💰 Ganancia: `+{reward_data['reward']} pts` (Rareza {reward_data['rarity']} + {reward_data['stat_bonus']}x Bonus)\n"
                  f"📉 Efecto: `-20 Moral` | `-15 Energía`\n"
                  f"━━━━━━━━━━━━━━━━━━\n"
                  f"✨ _Tus stats NSFW han multiplicado la ganancia base significativamente._")

    await q.edit_message_text(
        result_text,
        parse_mode="Markdown"
    )


# ─── NSFW INFO HANDLER ───
async def nsfw_info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para el botón Stats NSFW en la tarjeta de idol"""
    q = update.callback_query
    parts = q.data.split("_")
    # nsfw_info_ID_IDX_OWNERID -> parts = ["nsfw", "info", "ID", "IDX", "OWNERID"]
    iid, idx = int(parts[2]), int(parts[3])
    owner_id = int(parts[4]) if len(parts) > 4 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ No puedes ver las stats privadas de otro CEO.", show_alert=True)
        return

    all_idols = get_all_idols()
    if str(iid) not in all_idols:
        await q.answer("❌ Idol no encontrada.", show_alert=True)
        return

    idol = all_idols[str(iid)]

    total_nsfw = (idol.get("sensitivity", 50) + idol.get("coqueteo", 50) +
                  idol.get("firmeza_culo", 50) +
                  idol.get("habilidades_cama", 50) + idol.get("kinky", 50))

    text = (f"🔞 *STATS NSFW de {idol['name'].replace('_', ' ').upper()}*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{NSFW_STAT_EMOJIS['sensitivity']} Sensibilidad: `{idol.get('sensitivity', 50)}/100`\n"
            f"{NSFW_STAT_EMOJIS['coqueteo']} Coqueteo: `{idol.get('coqueteo', 50)}/100`\n"
            f"{NSFW_STAT_EMOJIS['firmeza_culo']} Firmeza Culo: `{idol.get('firmeza_culo', 50)}/100`\n"
            f"{NSFW_STAT_EMOJIS['habilidades_cama']} Habilidades Cama: `{idol.get('habilidades_cama', 50)}/100`\n"
            f"{NSFW_STAT_EMOJIS['kinky']} Kinky: `{idol.get('kinky', 50)}/100`\n\n"
            f"💪 Total NSFW: `{total_nsfw}/500`")

    kb = [
        [InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")],
        [InlineKeyboardButton(f"🔞 Entrenar {NSFW_STAT_NAMES['sensitivity']}",
                              callback_data=f"nsfw_tr_sensitivity_{iid}_{idx}_{owner_id}")],
        [InlineKeyboardButton(f"🔞 Entrenar {NSFW_STAT_NAMES['coqueteo']}",
                              callback_data=f"nsfw_tr_coqueteo_{iid}_{idx}_{owner_id}")],
        [InlineKeyboardButton(f"🔞 Entrenar {NSFW_STAT_NAMES['firmeza_culo']}",
                              callback_data=f"nsfw_tr_firmeza_culo_{iid}_{idx}_{owner_id}")],
        [InlineKeyboardButton(f"🔞 Entrenar {NSFW_STAT_NAMES['habilidades_cama']}",
                              callback_data=f"nsfw_tr_habilidades_cama_{iid}_{idx}_{owner_id}")],
        [InlineKeyboardButton(f"🔞 Entrenar {NSFW_STAT_NAMES['kinky']}",
                              callback_data=f"nsfw_tr_kinky_{iid}_{idx}_{owner_id}")],
    ]

    await q.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )


# ─── NSFW TRAINING ───
async def nsfw_train_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entrena un stat NSFW específico"""
    q = update.callback_query
    parts = q.data.split("_")
    # nsfw_tr_{stat_name}_{iid}_{idx}_{owner_id}
    # Como el nombre del stat puede tener guiones bajos, contamos desde el final
    owner_id = int(parts[-1])
    idx = int(parts[-2])
    iid = int(parts[-3])
    stat_type = "_".join(parts[2:-3])

    if q.from_user.id != owner_id:
        await q.answer("❌ Este entrenamiento no es tuyo.", show_alert=True)
        return

    r = train_nsfw(q.from_user.id, iid, stat_type)

    if r == "puntos_insuficientes":
        await q.answer("❌ Necesitas 200 pts.", show_alert=True); return
    if r == "sin_energia":
        await q.answer("😴 Sin energía. Descansa a tu idol.", show_alert=True); return
    if r == "ocupada":
        await q.answer("✈️ Idol en Tour. Espera a que regrese.", show_alert=True); return
    if r == "error" or r == "not_owner":
        await q.answer("❌ Error.", show_alert=True); return

    await q.edit_message_text(
        f"🔞 *ENTRENAMIENTO NSFW de {r['idol_name']}*\n━━━━━━━━━━━━━━━━━━\n"
        f"{r['emoji']} {r['stat']} subió `+{r['boost']}` → `{r['new_val']}/100`",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}_{owner_id}")]]),
        parse_mode="Markdown"
    )


# ─── CLAIM GLOBAL EVENT ───
async def claim_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para reclamar evento global (primera fase: selección)"""
    q = update.callback_query
    parts = q.data.split("_")
    eid = int(parts[1]) if len(parts) > 1 else 0

    # Verificar si el evento ya fue tomado
    event = get_event(eid)
    if not event or event.get("is_taken"):
        await q.answer("❌ Este evento ya ha sido reclamado.", show_alert=True)
        try:
            await q.edit_message_text("⌛ *EVENTO FINALIZADO*\nEste contrato ya ha sido firmado.", parse_mode="Markdown")
        except: pass
        return

    uid = q.from_user.id
    all_idols = get_user_idols(uid)

    if not all_idols:
        await q.answer("❌ No tienes ninguna idol para participar.", show_alert=True)
        return

    # Mostrar primera idol para seleccionar
    idx = 0
    idol = all_idols[idx]
    
    total_basic = idol.get("vocal", 0) + idol.get("dance", 0) + idol.get("rap", 0)
    total_nsfw = (idol.get("sensitivity", 50) + idol.get("coqueteo", 50) +
                  idol.get("firmeza_culo", 50) +
                  idol.get("habilidades_cama", 50) + idol.get("kinky", 50))

    text = (f"🔞 *SELECCIONA IDOL PARA EVENTO*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✨ *{idol['name'].replace('_', ' ').upper()}* {idol.get('group_name', '')}\n"
            f"📊 Rareza: {'⭐' * (['C','B','A','S','SS','SSS'].index(idol['rarity']) + 1)} ({idol['rarity']})\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎤 {idol.get('vocal', 0)} | 💃 {idol.get('dance', 0)} | 🎧 {idol.get('rap', 0)}\n"
            f"💪 Stats Básicos: `{total_basic}`\n\n"
            f"❤️ {idol.get('sensitivity', 50)} | 💕 {idol.get('coqueteo', 50)} | 🍑 {idol.get('firmeza_culo', 50)}\n"
            f"🔥 {idol.get('habilidades_cama', 50)} | 😈 {idol.get('kinky', 50)}\n"
            f"💪 Stats NSFW: `{total_nsfw}`\n\n"
            f"📈 Total Stats: `{total_basic + total_nsfw}`")

    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"sel_event_{eid}_{idx - 1}_{uid}"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{len(all_idols)}", callback_data="noop"))
    if idx < len(all_idols) - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"sel_event_{eid}_{idx + 1}_{uid}"))

    kb = [
        nav,
        [InlineKeyboardButton(f"🔞 USAR ESTA IDOL", callback_data=f"use_idol_{eid}_{idol['id']}_{uid}")],
        [InlineKeyboardButton(" Anular", callback_data="noop")]
    ]

    await q.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )


# ─── HELP POINTS ───
async def help_points_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    owner_id = int(parts[2]) if len(parts) > 2 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ No puedes abrir menús ajenos.", show_alert=True)
        return

    await q.answer()

    text = (
        "💰 *¿CÓMO GANAR PUNTOS?*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📀 *Comebacks:* La forma principal. Envía a tu idol a lanzar un álbum. Si es un MEGA HIT, ¡ganarás muchísimos puntos!\n\n"
        "🔞 *Eventos Globales:* En los grupos aparecerán contratos. Si eres el primero en reclamarlos, ganarás puntos según la rareza de tu mejor idol.\n\n"
        "🏪 *Mercado:* Si tienes idols que no usas, ponlas en venta. Otros CEOs pueden comprarlas y tú recibirás el pago.\n\n"
        "✈️ *World Tours:* Envía a tu idol de gira por 12h. No podrá trabajar, pero a su regreso traerá una gran cantidad de puntos pasivos.\n"
        "━━━━━━━━━━━━━━━━━━"
    )

    kb = [[InlineKeyboardButton("🔙 Volver", callback_data=f"back_main_{q.from_user.id}")]]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


async def help_game_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la guía completa y detallada del juego"""
    q = update.callback_query
    parts = q.data.split("_")
    owner_id = int(parts[2]) if len(parts) > 2 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ No puedes abrir menús ajenos.", show_alert=True)
        return

    await q.answer()
    
    text = (
        "👑 *GUÍA DEFINITIVA DEL CEO DE IDOLS*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🎤 *HABILIDADES Y ÉXITO*\n"
        "• *Talento (V, D, R):* Vocal, Dance y Rap. Determinan el éxito de los *Comebacks*. Un MEGA HIT puede darte x2 de recompensa.\n"
        "• *Stats NSFW:* Sensibilidad, Coqueteo, Firmeza, Cama y Kinky. Son vitales para los *Eventos Globales*. A mayor nivel, ¡contratos más millonarios!\n\n"
        "💎 *RAREZAS Y MULTIPLICADORES*\n"
        "• `C` (40%): x1.0 | `B` (35%): x1.5\n"
        "• `A` (18%): x2.5 | `S` (6%): x5.0\n"
        "• `SS` (1%): x10.0 (¡Diosas Legendarias!)\n\n"
        "💸 *ECONOMÍA Y GASTOS*\n"
        "• *Mantenimiento:* Cada 24h pagas 50 pts por cada idol. Si no tienes puntos, tus idols entrarán en *Hiatus* (se pausan y no ganan nada).\n"
        "• *Energía (⚡):* Se gasta al trabajar. Si baja de 20, no podrán hacer Comebacks. Recupérala con 'Descansar'.\n"
        "• *Moral (❤️):* Afecta el Score. Si es baja, tus canciones serán un FLOP. Súbela con 'Saludar'.\n\n"
        "🏪 *MERCADO Y TOURS*\n"
        "• Puedes vender idols al precio que quieras. El mercado es global entre todos los jugadores.\n"
        "• Los *World Tours* duran 12h y son la mejor forma de ganar puntos mientras no estás conectado.\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    
    kb = [[InlineKeyboardButton("🔙 Volver", callback_data=f"back_main_{q.from_user.id}")]]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

# ─── FUSION HANDLERS ───

async def fusion_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, manual_owner_id=None):
    """Main fusion menu with 3 slots"""
    q = update.callback_query
    if manual_owner_id:
        owner_id = manual_owner_id
    else:
        parts = q.data.split("_")
        owner_id = int(parts[2]) if len(parts) > 2 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Este no es tu laboratorio.", show_alert=True)
        return

    # Initialize fusion slots in user_data if not present
    if "fusion_slots" not in context.user_data:
        context.user_data["fusion_slots"] = [None, None, None]

    slots = context.user_data["fusion_slots"]
    all_idols = get_all_idols()
    
    slot_texts = []
    for i, s_id in enumerate(slots):
        if s_id and str(s_id) in all_idols:
            idol = all_idols[str(s_id)]
            slot_texts.append(f"Slot {i+1}: *{idol['name']}* ({idol['rarity']})")
        else:
            slot_texts.append(f"Slot {i+1}: _[Vacío]_")

    text = (
        "🧪 *CÁMARA DE FUSIÓN*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Combina 3 idols para obtener una nueva con mejores probabilidades de rareza alta.\n\n"
        + "\n".join(slot_texts) +
        "\n━━━━━━━━━━━━━━━━━━"
    )

    kb = []
    for i in range(3):
        label = "✅ Cambiar" if slots[i] else "➕ Seleccionar"
        kb.append([InlineKeyboardButton(f"{label} Idol {i+1}", callback_data=f"fus_sel_{i}_{owner_id}")])

    if all(slots):
        kb.append([InlineKeyboardButton("⚡ FUSIONAR (Acción irreversible)", callback_data=f"fus_exe_{owner_id}")])
    
    kb.append([InlineKeyboardButton("🧹 Limpiar todo", callback_data=f"fus_clear_{owner_id}")])
    kb.append([InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{owner_id}")])

    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


async def fusion_select_slot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of idols to pick for a specific slot"""
    q = update.callback_query
    parts = q.data.split("_")
    slot_idx = int(parts[2])
    owner_id = int(parts[3])
    page = int(parts[4]) if len(parts) > 4 else 0

    if q.from_user.id != owner_id:
        await q.answer("❌ Error de acceso.", show_alert=True); return

    all_idols = get_user_idols(owner_id)
    # Filter out idols already in other slots
    selected_ids = [s for s in context.user_data.get("fusion_slots", []) if s is not None]
    available = [i for i in all_idols if i["id"] not in selected_ids or i["id"] == context.user_data["fusion_slots"][slot_idx]]

    if not available:
        await q.answer("❌ No tienes más idols disponibles.", show_alert=True); return

    # Pagination (5 per page)
    per_page = 5
    total_pages = (len(available) + per_page - 1) // per_page
    page = max(0, min(page, total_pages - 1))
    
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_idols = available[start_idx:end_idx]

    text = f"🧪 *SELECCIONAR PARA SLOT {slot_idx + 1}*\n(Página {page+1}/{total_pages})"
    
    kb = []
    for idol in page_idols:
        kb.append([InlineKeyboardButton(f"{idol['name']} ({idol['rarity']}) - {idol.get('era', 'Standard')}", 
                                         callback_data=f"fus_pick_{slot_idx}_{idol['id']}_{owner_id}")])

    # Navigation
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"fus_sel_{slot_idx}_{owner_id}_{page-1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"fus_sel_{slot_idx}_{owner_id}_{page+1}"))
    if nav: kb.append(nav)

    kb.append([InlineKeyboardButton("🔙 Volver", callback_data=f"fusion_main_{owner_id}")])

    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


async def fusion_pick_idol_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store picked idol and return to fusion menu"""
    q = update.callback_query
    parts = q.data.split("_")
    slot_idx = int(parts[2])
    idol_id = int(parts[3])
    owner_id = int(parts[4])

    if "fusion_slots" not in context.user_data:
        context.user_data["fusion_slots"] = [None, None, None]
    
    context.user_data["fusion_slots"][slot_idx] = idol_id
    await q.answer(f"✅ Slot {slot_idx+1} asignado.")
    
    # Redirect to menu
    await fusion_menu_handler(update, context, manual_owner_id=owner_id)


async def fusion_execute_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the fusion and show result"""
    q = update.callback_query
    parts = q.data.split("_")
    owner_id = int(parts[2])

    if q.from_user.id != owner_id:
        await q.answer("❌ Error.", show_alert=True); return

    slots = context.user_data.get("fusion_slots", [])
    if not all(slots):
        await q.answer("❌ Necesitas 3 idols.", show_alert=True); return

    # Feedback visual inmediato
    await q.edit_message_text("🧪 *PROCESANDO FUSIÓN...*\n━━━━━━━━━━━━━━━━━━\n🧬 Combinando secuencias de ADN...\n✨ Estabilizando núcleos de idols...\n⏳ Por favor espera un momento...", parse_mode="Markdown")
    
    try:
        result = perform_fusion(owner_id, slots)
    except Exception as e:
        import logging
        logging.error(f"Error en perform_fusion: {e}")
        await q.answer(f"❌ Error crítico: {e}", show_alert=True)
        # Restaurar el menú
        await fusion_menu_handler(update, context, manual_owner_id=owner_id)
        return
    
    if isinstance(result, str):
        if result.startswith("not_found"):
            msg = "Una de las idols seleccionadas ya no existe en tu inventario."
        elif result.startswith("not_owner"):
            name = result.replace("not_owner_", "")
            msg = f"No eres el dueño de {name}."
        elif result.startswith("in_market"):
            name = result.replace("in_market_", "")
            msg = f"La idol {name} está puesta en venta en el mercado. Quítala primero."
        elif result == "need_3_idols":
            msg = "Necesitas seleccionar 3 idols para la fusión."
        else:
            msg = f"Error: {result}"
            
        await q.answer(f"❌ {msg}", show_alert=True)
        # Restaurar el menú para que no se quede en "Procesando"
        await fusion_menu_handler(update, context, manual_owner_id=owner_id)
        return

    await q.answer("🧪 ¡Fusión completada!")

    # Clear slots
    context.user_data["fusion_slots"] = [None, None, None]
    
    new_idol = result["new_idol"]
    # Escapar nombres para evitar errores de Markdown
    fused_names = [n.replace("_", "\\_").replace("*", "\\*") for n in result["fused_names"]]
    names_str = ", ".join(fused_names)

    # Visuals based on result rarity
    rarity_themes = {
        "C":  {"emoji": "⭐",       "border": "⚪", "title": "FUSIÓN ÉXITO"},
        "B":  {"emoji": "⭐⭐",      "border": "🟢", "title": "FUSIÓN SUPERIOR"},
        "A":  {"emoji": "⭐⭐⭐",     "border": "🔵", "title": "FUSIÓN ELITE"},
        "S":  {"emoji": "🌟🌟🌟🌟",    "border": "🟣", "title": "FUSIÓN LEGENDARIA"},
        "SS": {"emoji": "💎💎💎💎💎", "border": "👑", "title": "Diosa Creada"},
        "SSS":{"emoji": "👑👑👑👑👑👑", "border": "✨", "title": "ENTIDAD SUPREMA"},
    }
    theme = rarity_themes.get(new_idol["rarity"], rarity_themes["C"])

    text = (
        f"🧪 *¡FUSIÓN COMPLETADA!*\n"
        f"Sacrificaste a: _{names_str}_\n\n"
        f"{theme['border']} *{theme['title']}* {theme['border']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✨ *{new_idol['name'].upper()}* ({new_idol.get('era', 'Standard')})\n"
        f"🏢 {new_idol['group_name']}\n"
        f"📊 Rareza: {theme['emoji']} ({new_idol['rarity']})\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎤 {new_idol['vocal']} | 💃 {new_idol['dance']} | 🎧 {new_idol['rap']}\n"
    )

    kb = [[InlineKeyboardButton("🔙 Menú", callback_data=f"back_main_{owner_id}")]]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


async def fusion_clear_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset the fusion slots"""
    q = update.callback_query
    owner_id = int(q.data.split("_")[2])
    context.user_data["fusion_slots"] = [None, None, None]
    await q.answer("🧹 Slots limpiados.")
    await fusion_menu_handler(update, context, manual_owner_id=owner_id)


# ─── NOOP (for page indicators) ───
async def noop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
