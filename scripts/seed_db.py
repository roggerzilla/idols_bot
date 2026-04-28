import asyncio
import os
import sys

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import init_db, AsyncSessionLocal
from models import IdolTemplate

async def seed():
    await init_db()
    async with AsyncSessionLocal() as session:
        idols = [
            # --- RAREZA SS (Nivel Diosa / Viralidad Global NSFW) ---
            IdolTemplate(name="Karina", group_name="aespa", rarity="SS", base_vocal=65, base_dance=92, base_rap=70),
            IdolTemplate(name="Wonyoung", group_name="IVE", rarity="SS", base_vocal=55, base_dance=85, base_rap=30),
            IdolTemplate(name="Yuna", group_name="ITZY", rarity="SS", base_vocal=60, base_dance=94, base_rap=75),
            IdolTemplate(name="Chaewon", group_name="LE SSERAFIM", rarity="SS", base_vocal=82, base_dance=88, base_rap=70),
            IdolTemplate(name="Lisa", group_name="BLACKPINK", rarity="SS", base_vocal=65, base_dance=98, base_rap=94),
            IdolTemplate(name="Jennie", group_name="BLACKPINK", rarity="SS", base_vocal=78, base_dance=82, base_rap=90),
            IdolTemplate(name="Momo", group_name="TWICE", rarity="SS", base_vocal=45, base_dance=99, base_rap=65),

            # --- RAREZA S (Muy Populares / Top Tier) ---
            
            IdolTemplate(name="Hanni", group_name="NewJeans", rarity="S", base_vocal=80, base_dance=82, base_rap=75),
            IdolTemplate(name="Winter", group_name="aespa", rarity="S", base_vocal=94, base_dance=75, base_rap=35),
            IdolTemplate(name="Sakura", group_name="LE SSERAFIM", rarity="S", base_vocal=60, base_dance=82, base_rap=50),
            IdolTemplate(name="Yujin", group_name="IVE", rarity="S", base_vocal=78, base_dance=88, base_rap=60),
            IdolTemplate(name="Kazuha", group_name="LE SSERAFIM", rarity="S", base_vocal=55, base_dance=96, base_rap=40),
            IdolTemplate(name="Mina", group_name="TWICE", rarity="S", base_vocal=72, base_dance=88, base_rap=30),
            IdolTemplate(name="Jihyo", group_name="TWICE", rarity="S", base_vocal=98, base_dance=82, base_rap=40),

            # --- RAREZA A (Reconocidas / Talentosas) ---
            IdolTemplate(name="Ryujin", group_name="ITZY", rarity="A", base_vocal=55, base_dance=92, base_rap=88),
            IdolTemplate(name="Rei", group_name="IVE", rarity="A", base_vocal=58, base_dance=74, base_rap=82),
            IdolTemplate(name="Yeji", group_name="ITZY", rarity="A", base_vocal=75, base_dance=96, base_rap=60),
            IdolTemplate(name="Nayeon", group_name="TWICE", rarity="A", base_vocal=85, base_dance=78, base_rap=30),
            IdolTemplate(name="Sana", group_name="TWICE", rarity="A", base_vocal=62, base_dance=84, base_rap=45),
            IdolTemplate(name="Haerin", group_name="NewJeans", rarity="A", base_vocal=70, base_dance=90, base_rap=75),

            # --- RAREZA B (Promesas / Mid Tier) ---
            IdolTemplate(name="Minji", group_name="NewJeans", rarity="B", base_vocal=68, base_dance=82, base_rap=70),
            IdolTemplate(name="Danielle", group_name="NewJeans", rarity="B", base_vocal=85, base_dance=75, base_rap=40),
            IdolTemplate(name="Liz", group_name="IVE", rarity="B", base_vocal=92, base_dance=60, base_rap=30),
            IdolTemplate(name="Yunjin", group_name="LE SSERAFIM", rarity="B", base_vocal=60, base_dance=85, base_rap=60),
            IdolTemplate(name="Eunchae", group_name="LE SSERAFIM", rarity="B", base_vocal=60, base_dance=85, base_rap=60),

            # --- RAREZA C (Rookies / Soporte) ---
            IdolTemplate(name="Minji", group_name="NewJeans", rarity="C", base_vocal=60, base_dance=75, base_rap=65),
        ]

        session.add_all(idols)
        await session.commit()
        print(f"✅ Database seeded with {len(idols)} idols!")

if __name__ == "__main__":
    asyncio.run(seed())
