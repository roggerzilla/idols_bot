"""
Handlers usando almacenamiento JSON.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import random
import asyncio
from storage import (
    get_user, update_user, add_points, deduct_points,
    get_all_idols, get_user_idols, get_idol, update_idol, create_idol, delete_idol,
    get_event, take_event, get_all_events, get_all_groups, add_group
)
from services.economy import (
    gacha_pull, perform_comeback, start_world_tour,
    train_idol, greet_idol, rest_idol, buy_idol, cancel_sale, list_idol_for_sale,
    train_nsfw, calculate_event_reward
)
from utils.formatter import format_idol_card, format_market_listing
from config import RARITY_CONFIG

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

    # Animation sequence
    frames = ["🎰 ✨", "🎰 🌟", "🎰 💎", "🎰 🌈"]
    for frame in frames:
        try:
            await q.edit_message_text(f"GIRANDO RULETA...\n\n{frame}")
        except:
            pass
        await asyncio.sleep(0.3)

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
            [InlineKeyboardButton("🎰 Otro Gacha (500 pts)", callback_data="gacha")],
            [InlineKeyboardButton("🔙 Menú", callback_data="back_main")]
        ]), parse_mode="Markdown")


# ─── IDOL NAVIGATION (flat, with prev/next) ───
async def idols_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    parts = q.data.split("_")
    idx = int(parts[1]) if len(parts) > 1 else 0
    uid = q.from_user.id

    all_idols = get_user_idols(uid)

    if not all_idols:
        await q.edit_message_text("📉 No tienes idols. ¡Usa el Gacha!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data="back_main")]]))
        return

    idx = max(0, min(idx, len(all_idols) - 1))
    idol = all_idols[idx]

    # Store current idol index
    context.user_data["current_idol_id"] = idol["id"]
    context.user_data["current_idol_idx"] = idx

    card_text = format_idol_card(idol, None, idx + 1, len(all_idols))
    text = card_text

    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"idols_{idx - 1}"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{len(all_idols)}", callback_data="noop"))
    if idx < len(all_idols) - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"idols_{idx + 1}"))

    kb = [
        nav,
        [InlineKeyboardButton("💿 Comeback", callback_data=f"cb_{idol['id']}_{idx}")],
        [InlineKeyboardButton("💪 Entrenar", callback_data=f"tr_{idol['id']}_{idx}")],
        [InlineKeyboardButton("🔞 Stats NSFW", callback_data=f"nsfw_info_{idol['id']}_{idx}")],
        [InlineKeyboardButton("💬 Saludar", callback_data=f"gr_{idol['id']}_{idx}")],
        [InlineKeyboardButton("😴 Descansar", callback_data=f"rs_{idol['id']}_{idx}")],
        [InlineKeyboardButton("✈️ Tour", callback_data=f"tour_{idol['id']}_{idx}")],
        [InlineKeyboardButton("🏷️ Vender", callback_data=f"sell_{idol['id']}_{idx}")],
        [InlineKeyboardButton("🔙 Menú", callback_data="back_main")],
    ]

    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


# ─── COMEBACK ───
async def comeback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])

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
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}")]]),
        parse_mode="Markdown")


# ─── TRAIN ───
async def train_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])

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
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}")]]),
        parse_mode="Markdown")


# ─── GREET ───
async def greet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])

    r = greet_idol(q.from_user.id, iid)

    if r == "ocupada":
        await q.answer("✈️ Idol en Tour. Espera a que regrese.", show_alert=True); return
    if r == "error" or r == "not_owner":
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

    r = rest_idol(q.from_user.id, iid)

    if r == "ocupada":
        await q.answer("✈️ Idol en Tour. Espera a que regrese.", show_alert=True); return
    if r == "error" or r == "not_owner":
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
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}")]]),
        parse_mode="Markdown")


# ─── SELL (put on market) ───
async def sell_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split("_")
    iid, idx = int(parts[1]), int(parts[2])

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

    r = list_idol_for_sale(q.from_user.id, iid, price)

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

    idx = int(q.data.split("_")[1]) if "_" in q.data else 0

    # Get all idols for sale
    all_idols = get_all_idols()
    listings = [idol for idol in all_idols.values() if idol.get("for_sale", False)]

    if not listings:
        await q.edit_message_text("🏪 *MERCADO*\nNo hay idols en venta.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data="back_main")]]),
            parse_mode="Markdown")
        return

    idx = max(0, min(idx, len(listings) - 1))
    idol = listings[idx]

    text = f"🏪 *MERCADO* ({idx+1}/{len(listings)})\n━━━━━━━━━━━━━━━━━━\n"
    text += format_market_listing(idol, None, f"user_{idol['user_id']}")

    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"market_{idx-1}"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{len(listings)}", callback_data="noop"))
    if idx < len(listings) - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"market_{idx + 1}"))

    kb = [nav,
          [InlineKeyboardButton(f"💰 Comprar ({idol['sale_price']} pts)", callback_data=f"buy_{idol['id']}")],
          [InlineKeyboardButton("🔙 Menú", callback_data="back_main")]]

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
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menú", callback_data="back_main")]]),
        parse_mode="Markdown")


# ─── SELECT IDOL FOR EVENT ───
async def select_idol_for_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra lista de idols para seleccionar en evento NSFW"""
    q = update.callback_query
    await q.answer()

    parts = q.data.split("_")
    eid = int(parts[1]) if len(parts) > 1 else 0
    idx = int(parts[2]) if len(parts) > 2 else 0
    uid = q.from_user.id

    all_idols = get_user_idols(uid)

    if not all_idols:
        await q.edit_message_text(
            "📉 *NO Tienes idols*\n¡Usa el Gacha primero!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data="back_main")]]),
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
                f"📊 Rareza: {'⭐' * ['C','B','A','S','SS'].index(idol['rarity']) + 1} ({idol['rarity']})\n"
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
        nav.append(InlineKeyboardButton("◀️", callback_data=f"sel_event_{eid}_{idx - 1}"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{len(all_idols)}", callback_data="noop"))
    if idx < len(all_idols) - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"sel_event_{eid}_{idx + 1}"))

    kb = [
        nav,
        [InlineKeyboardButton(f"🔞 USAR ESTA IDOL", callback_data=f"use_idol_{eid}_{idol['id']}")],
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
    eid = int(parts[1])
    iid = int(parts[2])

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

    story = random.choice(nsfw_variants)

    result_text = (f"🔥 *¡CONTRATO FIRMADO!*\n{story}\n\n"
                  f"👤 CEO: *{q.from_user.username}*\n"
                  f"💰 Ganancia: `+{reward_data['reward']} pts`\n"
                  f"📊 Base: `{reward_data['base_points']}` × Rareza ({reward_data['rarity']})\n"
                  f"📈 Bonus Stats: `{reward_data['stat_bonus']}x` (Total: `{reward_data['total_stats']}`)")

    await q.edit_message_text(
        result_text,
        parse_mode="Markdown"
    )


# ─── NSFW INFO HANDLER ───
async def nsfw_info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para el botón Stats NSFW en la tarjeta de idol"""
    q = update.callback_query
    parts = q.data.split("_")
    # nsfw_info_ID_IDX -> parts = ["nsfw", "info", "ID", "IDX"]
    iid, idx = int(parts[2]), int(parts[3])

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
        [InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}")],
        [InlineKeyboardButton(f"🔞 Entrenar {NSFW_STAT_NAMES['sensitivity']}",
                              callback_data=f"nsfw_tr_sensitivity_{iid}_{idx}")],
        [InlineKeyboardButton(f"🔞 Entrenar {NSFW_STAT_NAMES['coqueteo']}",
                              callback_data=f"nsfw_tr_coqueteo_{iid}_{idx}")],
        [InlineKeyboardButton(f"🔞 Entrenar {NSFW_STAT_NAMES['firmeza_culo']}",
                              callback_data=f"nsfw_tr_firmeza_culo_{iid}_{idx}")],
        [InlineKeyboardButton(f"🔞 Entrenar {NSFW_STAT_NAMES['habilidades_cama']}",
                              callback_data=f"nsfw_tr_habilidades_cama_{iid}_{idx}")],
        [InlineKeyboardButton(f"🔞 Entrenar {NSFW_STAT_NAMES['kinky']}",
                              callback_data=f"nsfw_tr_kinky_{iid}_{idx}")],
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
    # nsfw_tr_{stat_name}_{iid}_{idx}
    # Como el nombre del stat puede tener guiones bajos, contamos desde el final
    idx = int(parts[-1])
    iid = int(parts[-2])
    stat_type = "_".join(parts[2:-2])

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
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Volver", callback_data=f"idols_{idx}")]]),
        parse_mode="Markdown"
    )


# ─── CLAIM GLOBAL EVENT ───
async def claim_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para reclamar evento global"""
    q = update.callback_query

    parts = q.data.split("_")
    eid = int(parts[1]) if len(parts) > 1 else 0

    # Check if this is the first click (show selection) or second click (use idol)
    if "_" in q.data and len(parts) == 3:
        # Already showing selection, just use the selected idol
        iid = int(parts[2])
        await use_idol_for_event(update, context)
        return

    uid = q.from_user.id

    # Get all idols for this user
    all_idols = get_user_idols(uid)

    if not all_idols:
        await q.answer("❌ Necesitas una idol.", show_alert=True); return

    # Show selection screen with first idol highlighted
    idx = 0
    idol = all_idols[idx]

    total_basic = idol.get("vocal", 0) + idol.get("dance", 0) + idol.get("rap", 0)
    total_nsfw = (idol.get("sensitivity", 50) + idol.get("coqueteo", 50) +
                  idol.get("firmeza_culo", 50) +
                  idol.get("habilidades_cama", 50) + idol.get("kinky", 50))

    text = (f"🔞 *SELECCIONA IDOL PARA EVENTO*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✨ *{idol['name'].replace('_', ' ').upper()}* {idol.get('group_name', '')}\n"
            f"📊 Rareza: {'⭐' * ['C','B','A','S','SS'].index(idol['rarity']) + 1} ({idol['rarity']})\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎤 {idol.get('vocal', 0)} | 💃 {idol.get('dance', 0)} | 🎧 {idol.get('rap', 0)}\n"
            f"💪 Stats Básicos: `{total_basic}`\n\n"
            f"❤️ {idol.get('sensitivity', 50)} | 💕 {idol.get('coqueteo', 50)} | 🍑 {idol.get('firmeza_culo', 50)}\n"
            f"🔥 {idol.get('habilidades_cama', 50)} | 😈 {idol.get('kinky', 50)}\n"
            f"💪 Stats NSFW: `{total_nsfw}`\n\n"
            f"📈 Total Stats: `{total_basic + total_nsfw}`")

    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"sel_event_{eid}_{idx - 1}"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{len(all_idols)}", callback_data="noop"))
    if idx < len(all_idols) - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"sel_event_{eid}_{idx + 1}"))

    kb = [
        nav,
        [InlineKeyboardButton(f"🔞 USAR ESTA IDOL", callback_data=f"use_idol_{eid}_{idol['id']}")],
        [InlineKeyboardButton("🔙 Cancelar", callback_data=f"claim_{eid}")]
    ]

    await q.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )


# ─── HELP POINTS ───
async def help_points_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
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

    kb = [[InlineKeyboardButton("🔙 Volver", callback_data="back_main")]]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")


async def help_game_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la guía completa y detallada del juego"""
    q = update.callback_query
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
    
    kb = [[InlineKeyboardButton("🔙 Volver", callback_data="back_main")]]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

# ─── NOOP (for page indicators) ───
async def noop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
