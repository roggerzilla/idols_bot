from sqlalchemy import select
from models import User
from services.economy import process_maintenance
from database import AsyncSessionLocal

async def process_all_maintenances():
    """Background task to process maintenance for ALL users"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        for user in users:
            # This function already handles point deduction and hiatus
            await process_maintenance(session, user.id)
        
        print(f"✅ Mantenimiento procesado para {len(users)} usuarios.")
