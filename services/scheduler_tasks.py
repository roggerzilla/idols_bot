"""
Tareas de background usando almacenamiento JSON.
"""

from storage import get_all_users, process_maintenance


async def process_all_maintenances():
    """Background task to process maintenance for ALL users"""
    users = get_all_users()

    for user_id, user in users.items():
        # This function already handles point deduction and hiatus
        result = process_maintenance(user_id)
        print(f"✅ Mantenimiento procesado para usuario {user_id}: {result}")

    print(f"✅ Mantenimiento procesado para {len(users)} usuarios.")
