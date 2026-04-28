"""
Script para migrar de SQLite a JSON.
Ejecutar una vez en PythonAnywhere: python3 migrate_to_json.py
"""

import sqlite3
from storage import (
    save_json, USERS_FILE, IDOLS_FILE, EVENTS_FILE, GROUPS_FILE,
    DATA_DIR
)
from datetime import datetime


def migrate():
    """Migra todos los datos de SQLite a JSON."""

    # Asegurar directorio existe
    DATA_DIR.mkdir(exist_ok=True)

    # Conectar a la DB SQLite existente
    db_path = "idols_bot.db"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print(f"✅ Conectado a {db_path}")
    except Exception as e:
        print(f"❌ Error conectando a {db_path}: {e}")
        return False

    try:
        # === MIGRAR USUARIOS ===
        cursor.execute("SELECT id, username, points, wins FROM users")
        rows = cursor.fetchall()
        users = {}
        for row in rows:
            user_id, username, points, wins = row
            users[user_id] = {
                "id": user_id,
                "username": username or f"user_{user_id}",
                "points": points or 1000,
                "wins": wins or 0,
                "last_maintenance_check": datetime.utcnow().isoformat(),
                "idols": []
            }

        save_json(USERS_FILE, users)
        print(f"✅ Migrados {len(users)} usuarios")

        # === MIGRAR IDOLS ===
        cursor.execute("""
            SELECT id, user_id, template_id, vocal, dance, rap, morale, energy,
                   status, busy_until, contract_expiry, for_sale, sale_price
            FROM user_idols
        """)
        rows = cursor.fetchall()
        idols = {}

        # Obtener templates para nombre y grupo
        cursor.execute("SELECT id, name, group_name, rarity, base_vocal, base_dance, base_rap FROM idol_templates")
        templates = {row[0]: row for row in cursor.fetchall()}

        for row in rows:
            idol_id, user_id, template_id, vocal, dance, rap, morale, energy, \
                status, busy_until, contract_expiry, for_sale, sale_price = row

            tmpl = templates.get(template_id)
            if tmpl:
                # tmpl tiene 7 valores: id, name, group_name, rarity, base_vocal, base_dance, base_rap
                _, name, group_name, rarity, base_vocal, base_dance, base_rap = tmpl
            else:
                name, group_name, rarity = "Unknown", "Unknown Group", "C"

            idols[idol_id] = {
                "id": idol_id,
                "user_id": user_id,
                "template_id": template_id or 0,
                "name": (name or "").replace("_", " "),
                "group_name": (group_name or "").replace("_", " "),
                "rarity": rarity or "C",
                "vocal": vocal or base_vocal or 10,
                "dance": dance or base_dance or 10,
                "rap": rap or base_rap or 10,
                "morale": morale or 100,
                "energy": energy or 100,
                # NSFW Stats con default 50
                "sensitivity": 50,
                "coqueteo": 50,
                "firmeza_culo": 50,
                "habilidades_cama": 50,
                "kinky": 50,
                "status": status or "active",
                "busy_until": busy_until,
                "contract_expiry": contract_expiry,
                "for_sale": bool(for_sale) if for_sale is not None else False,
                "sale_price": sale_price or 0
            }

        save_json(IDOLS_FILE, idols)
        print(f"✅ Migrados {len(idols)} idols")

        # Actualizar lista de idols en usuarios
        updated_users = {}
        for user_id in users:
            user = users[user_id].copy()
            user["idols"] = [iid for iid, idol in idols.items() if idol["user_id"] == user_id]
            updated_users[user_id] = user
        save_json(USERS_FILE, updated_users)

        # === MIGRAR EVENTOS GLOBALES ===
        cursor.execute("""
            SELECT id, event_type, description, points, is_taken, taken_by_user_id,
                   chat_id, message_id, created_at FROM global_events
        """)
        rows = cursor.fetchall()
        events = {}
        for row in rows:
            event_id, event_type, description, points, is_taken, taken_by_user_id, \
                chat_id, message_id, created_at = row

            events[event_id] = {
                "id": event_id,
                "event_type": event_type or "NSFW_SPONSOR",
                "description": description or "",
                "points": points or 0,
                "is_taken": bool(is_taken) if is_taken is not None else False,
                "taken_by_user_id": taken_by_user_id,
                "chat_id": chat_id,
                "message_id": message_id,
                "created_at": created_at or datetime.utcnow().isoformat()
            }

        save_json(EVENTS_FILE, events)
        print(f"✅ Migrados {len(events)} eventos")

        # === MIGRAR GRUPOS ===
        cursor.execute("SELECT chat_id, title, added_at FROM bot_groups")
        rows = cursor.fetchall()
        groups = {}
        for row in rows:
            chat_id, title, added_at = row
            groups[chat_id] = {
                "chat_id": chat_id,
                "title": (title or "").replace("_", " "),
                "added_at": added_at or datetime.utcnow().isoformat()
            }

        save_json(GROUPS_FILE, groups)
        print(f"✅ Migrados {len(groups)} grupos")

        conn.close()
        print("\n" + "="*50)
        print("🎉 ¡MIGRACIÓN COMPLETADA!")
        print("="*50)
        print("\nSiguientes pasos:")
        print("1. Elimina el archivo idols_bot.db (opcional)")
        print("2. Reinicia el bot con: python3 main.py")
        print("3. Los datos ahora se guardan en data/*.json")

        return True

    except Exception as e:
        print(f"❌ Error durante migración: {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        return False


if __name__ == "__main__":
    migrate()
