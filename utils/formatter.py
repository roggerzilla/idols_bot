import datetime

def format_idol_card(idol, template):
    status_emoji = {
        "ACTIVE": "✨",
        "HIATUS": "😴",
        "WORLD_TOUR": "✈️"
    }.get(idol.status.name, "❓")
    
    return (
        f"🌟 *{template.name}* ({template.group_name})\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📊 Rarity: `{template.rarity}` | {status_emoji} {idol.status.value.title()}\n"
        f"🎤 Vocal: `{idol.vocal}` | 💃 Dance: `{idol.dance}` | 🎧 Rap: `{idol.rap}`\n"
        f"❤️ Morale: `{idol.morale}/100` (Influye en el éxito del Comeback)\n"
        f"⚡ Energy: `{idol.energy}/100` (Se agota al trabajar/entrenar)\n"
        f"📜 Contract: `{idol.contract_expiry.strftime('%Y-%m-%d')}`\n"
        f"━━━━━━━━━━━━━━━"
    )

def format_user_profile(user, idols_count):
    return (
        f"👤 *Agencia de {user.username}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 Balance: `{user.points} pts`\n"
        f"🏆 Wins: `{user.wins}`\n"
        f"👯 Idols en Staff: `{idols_count}`\n"
        f"🚩 Fandom: `{user.fandom.name if user.fandom else 'Ninguno'}`\n"
        f"━━━━━━━━━━━━━━━"
    )
