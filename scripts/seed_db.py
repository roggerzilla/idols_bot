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
        # Clear existing templates to avoid duplicates
        from sqlalchemy import delete
        await session.execute(delete(IdolTemplate))
        
        idols = [
            # --- RAREZA SSS ---
            IdolTemplate(name="Karina", group_name="aespa", rarity="SSS", era="Waterbomb", base_vocal=98, base_dance=99, base_rap=95),
            IdolTemplate(name="Eunbi", group_name="Soloist", rarity="SSS", era="Waterbomb", base_vocal=96, base_dance=98, base_rap=80),

            # --- RAREZA SS---
            IdolTemplate(name="Karina", group_name="aespa", rarity="SS", era="Standard", base_vocal=65, base_dance=92, base_rap=70),
            IdolTemplate(name="Wonyoung", group_name="IVE", rarity="SS", era="Standard", base_vocal=55, base_dance=85, base_rap=30),
            IdolTemplate(name="Yuna", group_name="ITZY", rarity="SS", era="Standard", base_vocal=60, base_dance=94, base_rap=75),
            IdolTemplate(name="Chaewon", group_name="LE SSERAFIM", rarity="SS", era="Standard", base_vocal=82, base_dance=88, base_rap=70),
            IdolTemplate(name="Lisa", group_name="BLACKPINK", rarity="SS", era="Standard", base_vocal=65, base_dance=98, base_rap=94),
            IdolTemplate(name="Jennie", group_name="BLACKPINK", rarity="SS", era="Standard", base_vocal=78, base_dance=82, base_rap=90),
            IdolTemplate(name="Momo", group_name="TWICE", rarity="SS", era="Standard", base_vocal=45, base_dance=99, base_rap=65),
            IdolTemplate(name="Sullyoon", group_name="NMIXX", rarity="SS", era="Standard", base_vocal=85, base_dance=82, base_rap=30),

            # --- RAREZA S ---
            IdolTemplate(name="Hanni", group_name="NewJeans", rarity="S", era="Standard", base_vocal=80, base_dance=82, base_rap=75),
            IdolTemplate(name="Winter", group_name="aespa", rarity="S", era="Standard", base_vocal=94, base_dance=75, base_rap=35),
            IdolTemplate(name="Sakura", group_name="LE SSERAFIM", rarity="S", era="Standard", base_vocal=60, base_dance=82, base_rap=50),
            IdolTemplate(name="Yujin", group_name="IVE", rarity="S", era="Standard", base_vocal=78, base_dance=88, base_rap=60),
            IdolTemplate(name="Kazuha", group_name="LE SSERAFIM", rarity="S", era="Standard", base_vocal=55, base_dance=96, base_rap=40),
            IdolTemplate(name="Mina", group_name="TWICE", rarity="S", era="Standard", base_vocal=72, base_dance=88, base_rap=30),
            IdolTemplate(name="Jihyo", group_name="TWICE", rarity="S", era="Standard", base_vocal=98, base_dance=82, base_rap=40),
            IdolTemplate(name="Haerin", group_name="NewJeans", rarity="S", era="Standard", base_vocal=70, base_dance=90, base_rap=75),

            # --- RAREZA A ---
            IdolTemplate(name="Ryujin", group_name="ITZY", rarity="A", era="Standard", base_vocal=55, base_dance=92, base_rap=88),
            IdolTemplate(name="Rei", group_name="IVE", rarity="A", era="Standard", base_vocal=58, base_dance=74, base_rap=82),
            IdolTemplate(name="Yeji", group_name="ITZY", rarity="A", era="Standard", base_vocal=75, base_dance=96, base_rap=60),
            IdolTemplate(name="Nayeon", group_name="TWICE", rarity="A", era="Standard", base_vocal=85, base_dance=78, base_rap=30),
            IdolTemplate(name="Sana", group_name="TWICE", rarity="A", era="Standard", base_vocal=62, base_dance=84, base_rap=45),
            IdolTemplate(name="Natty", group_name="Kiss of Life", rarity="A", era="Standard", base_vocal=70, base_dance=92, base_rap=60),
            IdolTemplate(name="Yunjin", group_name="LE SSERAFIM", rarity="A", era="Standard", base_vocal=88, base_dance=78, base_rap=50),

            # --- RAREZA B ---
            IdolTemplate(name="Minji", group_name="NewJeans", rarity="B", era="Standard", base_vocal=68, base_dance=82, base_rap=70),
            IdolTemplate(name="Danielle", group_name="NewJeans", rarity="B", era="Standard", base_vocal=85, base_dance=75, base_rap=40),
            IdolTemplate(name="Liz", group_name="IVE", rarity="B", era="Standard", base_vocal=92, base_dance=60, base_rap=30),
            IdolTemplate(name="Eunchae", group_name="LE SSERAFIM", rarity="B", era="Standard", base_vocal=60, base_dance=85, base_rap=60),
            IdolTemplate(name="Xiaoting", group_name="Kep1er", rarity="B", era="Standard", base_vocal=50, base_dance=92, base_rap=40),
            IdolTemplate(name="Hyein", group_name="NewJeans", rarity="B", era="Standard", base_vocal=75, base_dance=80, base_rap=60),
            IdolTemplate(name="Lily", group_name="NMIXX", rarity="B", era="Standard", base_vocal=96, base_dance=70, base_rap=40),
            IdolTemplate(name="Sieun", group_name="STAYC", rarity="B", era="Standard", base_vocal=85, base_dance=75, base_rap=30),
            IdolTemplate(name="Yoon", group_name="STAYC", rarity="B", era="Standard", base_vocal=82, base_dance=70, base_rap=40),

            # --- RAREZA C ---
            IdolTemplate(name="Karina", group_name="aespa", rarity="C", era="Debut", base_vocal=40, base_dance=60, base_rap=30),
            IdolTemplate(name="Eunbi", group_name="IZ*ONE", rarity="C", era="Produce 48", base_vocal=45, base_dance=50, base_rap=20),
            IdolTemplate(name="Haewon", group_name="NMIXX", rarity="C", era="Standard", base_vocal=90, base_dance=75, base_rap=40),
            IdolTemplate(name="Bae", group_name="NMIXX", rarity="C", era="Standard", base_vocal=75, base_dance=75, base_rap=50),
            IdolTemplate(name="Jiwoo", group_name="NMIXX", rarity="C", era="Standard", base_vocal=65, base_dance=88, base_rap=82),
            IdolTemplate(name="Kyujin", group_name="NMIXX", rarity="C", era="Standard", base_vocal=75, base_dance=90, base_rap=75),
            IdolTemplate(name="Mashiro", group_name="Kep1er", rarity="C", era="Standard", base_vocal=72, base_dance=78, base_rap=40),
            IdolTemplate(name="Chaehyun", group_name="Kep1er", rarity="C", era="Standard", base_vocal=88, base_dance=70, base_rap=30),
            IdolTemplate(name="Hikaru", group_name="Kep1er", rarity="C", era="Standard", base_vocal=50, base_dance=92, base_rap=88),
            IdolTemplate(name="Huening Bahiyyih", group_name="Kep1er", rarity="C", era="Standard", base_vocal=65, base_dance=75, base_rap=40),
            IdolTemplate(name="Isa", group_name="STAYC", rarity="C", era="Standard", base_vocal=78, base_dance=78, base_rap=30),
            IdolTemplate(name="Seeun", group_name="STAYC", rarity="C", era="Standard", base_vocal=70, base_dance=70, base_rap=30),
            IdolTemplate(name="Sumin", group_name="STAYC", rarity="C", era="Standard", base_vocal=72, base_dance=75, base_rap=40),
            IdolTemplate(name="J", group_name="STAYC", rarity="C", era="Standard", base_vocal=65, base_dance=70, base_rap=85),
            IdolTemplate(name="Belle", group_name="Kiss of Life", rarity="C", era="Standard", base_vocal=92, base_dance=70, base_rap=30),
            IdolTemplate(name="Julie", group_name="Kiss of Life", rarity="C", era="Standard", base_vocal=55, base_dance=80, base_rap=90),
            IdolTemplate(name="Haneul", group_name="Kiss of Life", rarity="C", era="Standard", base_vocal=75, base_dance=75, base_rap=40),
            IdolTemplate(name="Iroha", group_name="ILLIT", rarity="C", era="Standard", base_vocal=60, base_dance=85, base_rap=50),
            IdolTemplate(name="Wonhee", group_name="ILLIT", rarity="C", era="Standard", base_vocal=75, base_dance=65, base_rap=30),
            IdolTemplate(name="Minju", group_name="ILLIT", rarity="C", era="Standard", base_vocal=82, base_dance=70, base_rap=40),
            IdolTemplate(name="Moka", group_name="ILLIT", rarity="C", era="Standard", base_vocal=70, base_dance=75, base_rap=30),
            IdolTemplate(name="Yunah", group_name="ILLIT", rarity="C", era="Standard", base_vocal=75, base_dance=82, base_rap=65),
        ]

        session.add_all(idols)
        await session.commit()
        print(f"Database seeded with {len(idols)} idols!")

if __name__ == "__main__":
    asyncio.run(seed())
