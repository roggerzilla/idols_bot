"""
Formateadores usando almacenamiento JSON (dicts).
"""


def format_idol_card(idol, template, idx=None, total=None):
    """Compact idol card for the flat navigation UI - works with dicts"""

    # Status mapping
    status_map = {
        "active": ("✅", "Activa"),
        "hiatus": ("😴", "Hiatus"),
        "world_tour": ("✈️", "En Tour"),
    }

    status_emoji, status_text = status_map.get(idol.get("status", "active"), ("❓", "Desconocido"))

    # Morale bar
    morale_bars = "█" * (idol.get("morale", 100) // 10) + "░" * (10 - idol.get("morale", 100) // 10)
    energy_bars = "█" * (idol.get("energy", 100) // 10) + "░" * (10 - idol.get("energy", 100) // 10)

    header = ""
    if idx is not None and total is not None:
        header = f"Idol {idx}/{total}\n"

    sale_text = ""
    if idol.get("for_sale", False):
        sale_text = f"\n🏷 EN VENTA: {idol.get('sale_price', 0)} pts"

    name = idol.get("name", "Unknown").replace("_", " ")
    group = idol.get("group_name", "Unknown Group")

    return (
        f"{header}"
        f"🌟 *{name}* ({group}) [{idol.get('rarity', 'C')}]\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{status_emoji} Estado: {status_text}\n"
        f"🎤 {idol.get('vocal', 0)} | 💃 {idol.get('dance', 0)} | 🎧 {idol.get('rap', 0)}\n"
        f"❤️ Moral: {morale_bars} {idol.get('morale', 100)}/100\n"
        f"⚡ Energía: {energy_bars} {idol.get('energy', 100)}/100"
        f"{sale_text}"
    )


def format_user_profile(user, idols_count):
    """Format user profile - works with dict"""
    return (
        f"👤 *CEO: {user.get('username', 'Unknown')}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 Puntos: `{user.get('points', 0)}`\n"
        f"🏆 Victorias: `{user.get('wins', 0)}`\n"
        f"👯 Idols: `{idols_count}`\n"
        f"━━━━━━━━━━━━━━━━━━"
    )


def format_market_listing(idol, template, owner_name):
    """Format market listing - works with dicts"""
    name = idol.get("name", "Unknown").replace("_", " ")
    group = idol.get("group_name", "Unknown Group")

    return (
        f"🏷 *{name}* ({group}) [{idol.get('rarity', 'C')}]\n"
        f"🎤 {idol.get('vocal', 0)} | 💃 {idol.get('dance', 0)} | 🎧 {idol.get('rap', 0)}\n"
        f"💰 Precio: {idol.get('sale_price', 0)} pts\n"
        f"👤 Vendedor: {owner_name}"
    )
