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

            # --- BETA TEST ONLY (No Gacha) ---
            IdolTemplate(name="Wendy", group_name="Red Velvet", rarity="SS", era="GOT THE BEAT", base_vocal=98, base_dance=75, base_rap=62, can_gacha=False),
            IdolTemplate(name="Taeyeon", group_name="Girls' Generation", rarity="SS", era="GOT THE BEAT", base_vocal=99, base_dance=80, base_rap=56, can_gacha=False),

            # =========================================================
# POWER SYSTEM:
# SS = 235 TOTAL
# S  = 215 TOTAL
# A  = 195 TOTAL
# B  = 175 TOTAL
# C  = 155 TOTAL
# =========================================================

# 🍭 TWICE
# =========================================================
# TT
            IdolTemplate(name="Jeongyeon", group_name="TWICE", rarity="SS", era="TT", base_vocal=98, base_dance=90, base_rap=47),
            IdolTemplate(name="Sana", group_name="TWICE", rarity="S", era="TT", base_vocal=84, base_dance=92, base_rap=39),
            IdolTemplate(name="Dahyun", group_name="TWICE", rarity="S", era="TT", base_vocal=78, base_dance=80, base_rap=57),
            IdolTemplate(name="Mina", group_name="TWICE", rarity="A", era="TT", base_vocal=88, base_dance=82, base_rap=25),
            IdolTemplate(name="Chaeyoung", group_name="TWICE", rarity="A", era="TT", base_vocal=72, base_dance=75, base_rap=48),
            IdolTemplate(name="Nayeon", group_name="TWICE", rarity="B", era="TT", base_vocal=88, base_dance=70, base_rap=17),
            IdolTemplate(name="Jihyo", group_name="TWICE", rarity="B", era="TT", base_vocal=92, base_dance=67, base_rap=16),
            IdolTemplate(name="Tzuyu", group_name="TWICE", rarity="C", era="TT", base_vocal=72, base_dance=64, base_rap=19),
            IdolTemplate(name="Momo", group_name="TWICE", rarity="C", era="TT", base_vocal=40, base_dance=91, base_rap=24),

# Knock Knock
            IdolTemplate(name="Momo", group_name="TWICE", rarity="SS", era="Knock Knock", base_vocal=58, base_dance=99, base_rap=78),
            IdolTemplate(name="Chaeyoung", group_name="TWICE", rarity="S", era="Knock Knock", base_vocal=74, base_dance=78, base_rap=63),
            IdolTemplate(name="Jihyo", group_name="TWICE", rarity="S", era="Knock Knock", base_vocal=97, base_dance=86, base_rap=32),
            IdolTemplate(name="Sana", group_name="TWICE", rarity="A", era="Knock Knock", base_vocal=83, base_dance=88, base_rap=24),
            IdolTemplate(name="Dahyun", group_name="TWICE", rarity="A", era="Knock Knock", base_vocal=76, base_dance=76, base_rap=43),
            IdolTemplate(name="Mina", group_name="TWICE", rarity="B", era="Knock Knock", base_vocal=86, base_dance=73, base_rap=16),
            IdolTemplate(name="Tzuyu", group_name="TWICE", rarity="B", era="Knock Knock", base_vocal=78, base_dance=80, base_rap=17),
            IdolTemplate(name="Nayeon", group_name="TWICE", rarity="C", era="Knock Knock", base_vocal=79, base_dance=61, base_rap=15),
            IdolTemplate(name="Jeongyeon", group_name="TWICE", rarity="C", era="Knock Knock", base_vocal=84, base_dance=56, base_rap=15),

            # Signal
            IdolTemplate(name="Dahyun", group_name="TWICE", rarity="SS", era="Signal", base_vocal=82, base_dance=85, base_rap=68),
            IdolTemplate(name="Mina", group_name="TWICE", rarity="S", era="Signal", base_vocal=92, base_dance=91, base_rap=32),
            IdolTemplate(name="Sana", group_name="TWICE", rarity="S", era="Signal", base_vocal=85, base_dance=94, base_rap=36),
            IdolTemplate(name="Tzuyu", group_name="TWICE", rarity="A", era="Signal", base_vocal=79, base_dance=91, base_rap=25),
            IdolTemplate(name="Nayeon", group_name="TWICE", rarity="A", era="Signal", base_vocal=94, base_dance=78, base_rap=23),
            IdolTemplate(name="Jihyo", group_name="TWICE", rarity="B", era="Signal", base_vocal=91, base_dance=66, base_rap=18),
            IdolTemplate(name="Momo", group_name="TWICE", rarity="B", era="Signal", base_vocal=48, base_dance=95, base_rap=32),
            IdolTemplate(name="Chaeyoung", group_name="TWICE", rarity="C", era="Signal", base_vocal=60, base_dance=58, base_rap=37),
            IdolTemplate(name="Jeongyeon", group_name="TWICE", rarity="C", era="Signal", base_vocal=83, base_dance=55, base_rap=17),

            # Heart Shaker
            IdolTemplate(name="Jeongyeon", group_name="TWICE", rarity="SS", era="Heart Shaker", base_vocal=99, base_dance=91, base_rap=45),
            IdolTemplate(name="Sana", group_name="TWICE", rarity="S", era="Heart Shaker", base_vocal=86, base_dance=95, base_rap=34),
            IdolTemplate(name="Mina", group_name="TWICE", rarity="S", era="Heart Shaker", base_vocal=93, base_dance=90, base_rap=32),
            IdolTemplate(name="Dahyun", group_name="TWICE", rarity="A", era="Heart Shaker", base_vocal=78, base_dance=79, base_rap=38),
            IdolTemplate(name="Chaeyoung", group_name="TWICE", rarity="A", era="Heart Shaker", base_vocal=73, base_dance=76, base_rap=46),
            IdolTemplate(name="Nayeon", group_name="TWICE", rarity="B", era="Heart Shaker", base_vocal=89, base_dance=68, base_rap=18),
            IdolTemplate(name="Jihyo", group_name="TWICE", rarity="B", era="Heart Shaker", base_vocal=92, base_dance=65, base_rap=18),
            IdolTemplate(name="Tzuyu", group_name="TWICE", rarity="C", era="Heart Shaker", base_vocal=73, base_dance=65, base_rap=17),
            IdolTemplate(name="Momo", group_name="TWICE", rarity="C", era="Heart Shaker", base_vocal=42, base_dance=89, base_rap=24),

            # What Is Love?
            IdolTemplate(name="Mina", group_name="TWICE", rarity="SS", era="What Is Love?", base_vocal=96, base_dance=96, base_rap=43),
            IdolTemplate(name="Nayeon", group_name="TWICE", rarity="S", era="What Is Love?", base_vocal=96, base_dance=87, base_rap=32),
            IdolTemplate(name="Tzuyu", group_name="TWICE", rarity="S", era="What Is Love?", base_vocal=83, base_dance=97, base_rap=35),
            IdolTemplate(name="Sana", group_name="TWICE", rarity="A", era="What Is Love?", base_vocal=84, base_dance=88, base_rap=23),
            IdolTemplate(name="Dahyun", group_name="TWICE", rarity="A", era="What Is Love?", base_vocal=78, base_dance=76, base_rap=41),
            IdolTemplate(name="Jihyo", group_name="TWICE", rarity="B", era="What Is Love?", base_vocal=91, base_dance=67, base_rap=17),
            IdolTemplate(name="Chaeyoung", group_name="TWICE", rarity="B", era="What Is Love?", base_vocal=67, base_dance=66, base_rap=42),
            IdolTemplate(name="Momo", group_name="TWICE", rarity="C", era="What Is Love?", base_vocal=43, base_dance=89, base_rap=23),
            IdolTemplate(name="Jeongyeon", group_name="TWICE", rarity="C", era="What Is Love?", base_vocal=82, base_dance=56, base_rap=17),

            # Fancy
            IdolTemplate(name="Tzuyu", group_name="TWICE", rarity="SS", era="Fancy", base_vocal=88, base_dance=99, base_rap=48),
            IdolTemplate(name="Mina", group_name="TWICE", rarity="S", era="Fancy", base_vocal=94, base_dance=90, base_rap=31),
            IdolTemplate(name="Sana", group_name="TWICE", rarity="S", era="Fancy", base_vocal=86, base_dance=95, base_rap=34),
            IdolTemplate(name="Jihyo", group_name="TWICE", rarity="A", era="Fancy", base_vocal=95, base_dance=80, base_rap=20),
            IdolTemplate(name="Chaeyoung", group_name="TWICE", rarity="A", era="Fancy", base_vocal=72, base_dance=74, base_rap=49),
            IdolTemplate(name="Nayeon", group_name="TWICE", rarity="B", era="Fancy", base_vocal=88, base_dance=69, base_rap=18),
            IdolTemplate(name="Dahyun", group_name="TWICE", rarity="B", era="Fancy", base_vocal=70, base_dance=69, base_rap=36),
            IdolTemplate(name="Momo", group_name="TWICE", rarity="C", era="Fancy", base_vocal=40, base_dance=91, base_rap=24),
            IdolTemplate(name="Jeongyeon", group_name="TWICE", rarity="C", era="Fancy", base_vocal=82, base_dance=57, base_rap=16),

# IZ*ONE (primer bloque)
# Debut
            IdolTemplate(name="Hyewon", group_name="IZ*ONE", rarity="SS", era="Debut", base_vocal=78, base_dance=82, base_rap=75),
            IdolTemplate(name="Nako", group_name="IZ*ONE", rarity="S", era="Debut", base_vocal=95, base_dance=88, base_rap=32),
            IdolTemplate(name="Hitomi", group_name="IZ*ONE", rarity="S", era="Debut", base_vocal=82, base_dance=97, base_rap=36),
            IdolTemplate(name="Eunbi", group_name="IZ*ONE", rarity="S", era="Debut", base_vocal=88, base_dance=94, base_rap=33),
            IdolTemplate(name="Minju", group_name="IZ*ONE", rarity="A", era="Debut", base_vocal=90, base_dance=82, base_rap=23),
            IdolTemplate(name="Yena", group_name="IZ*ONE", rarity="A", era="Debut", base_vocal=76, base_dance=82, base_rap=37),
            IdolTemplate(name="Yuri", group_name="IZ*ONE", rarity="A", era="Debut", base_vocal=97, base_dance=76, base_rap=22),
            IdolTemplate(name="Sakura", group_name="IZ*ONE", rarity="B", era="Debut", base_vocal=76, base_dance=82, base_rap=17),
            IdolTemplate(name="Wonyoung", group_name="IZ*ONE", rarity="B", era="Debut", base_vocal=82, base_dance=76, base_rap=17),
            IdolTemplate(name="Chaewon", group_name="IZ*ONE", rarity="B", era="Debut", base_vocal=88, base_dance=70, base_rap=17),
            # HEARTIZ
            IdolTemplate(name="Nako", group_name="IZ*ONE", rarity="SS", era="HEARTIZ", base_vocal=98, base_dance=94, base_rap=43),
            IdolTemplate(name="Hyewon", group_name="IZ*ONE", rarity="S", era="HEARTIZ", base_vocal=80, base_dance=83, base_rap=52),
            IdolTemplate(name="Hitomi", group_name="IZ*ONE", rarity="S", era="HEARTIZ", base_vocal=83, base_dance=98, base_rap=34),
            IdolTemplate(name="Eunbi", group_name="IZ*ONE", rarity="S", era="HEARTIZ", base_vocal=89, base_dance=94, base_rap=32),
            IdolTemplate(name="Sakura", group_name="IZ*ONE", rarity="A", era="HEARTIZ", base_vocal=78, base_dance=88, base_rap=29),
            IdolTemplate(name="Minju", group_name="IZ*ONE", rarity="A", era="HEARTIZ", base_vocal=91, base_dance=81, base_rap=23),
            IdolTemplate(name="Chaeyeon", group_name="IZ*ONE", rarity="A", era="HEARTIZ", base_vocal=72, base_dance=98, base_rap=25),
            IdolTemplate(name="Yena", group_name="IZ*ONE", rarity="B", era="HEARTIZ", base_vocal=77, base_dance=80, base_rap=18),
            IdolTemplate(name="Yuri", group_name="IZ*ONE", rarity="B", era="HEARTIZ", base_vocal=95, base_dance=63, base_rap=17),
            IdolTemplate(name="Wonyoung", group_name="IZ*ONE", rarity="B", era="HEARTIZ", base_vocal=83, base_dance=75, base_rap=17),
            IdolTemplate(name="Chaewon", group_name="IZ*ONE", rarity="B", era="HEARTIZ", base_vocal=89, base_dance=69, base_rap=17),

            # BLOOMIZ
            IdolTemplate(name="Minju", group_name="IZ*ONE", rarity="SS", era="BLOOMIZ", base_vocal=96, base_dance=94, base_rap=45),
            IdolTemplate(name="Nako", group_name="IZ*ONE", rarity="S", era="BLOOMIZ", base_vocal=97, base_dance=88, base_rap=30),
            IdolTemplate(name="Hitomi", group_name="IZ*ONE", rarity="S", era="BLOOMIZ", base_vocal=82, base_dance=99, base_rap=34),
            IdolTemplate(name="Eunbi", group_name="IZ*ONE", rarity="S", era="BLOOMIZ", base_vocal=90, base_dance=93, base_rap=32),
            IdolTemplate(name="Sakura", group_name="IZ*ONE", rarity="A", era="BLOOMIZ", base_vocal=80, base_dance=87, base_rap=28),
            IdolTemplate(name="Hyewon", group_name="IZ*ONE", rarity="A", era="BLOOMIZ", base_vocal=79, base_dance=81, base_rap=35),
            IdolTemplate(name="Yuri", group_name="IZ*ONE", rarity="A", era="BLOOMIZ", base_vocal=98, base_dance=75, base_rap=22),
            IdolTemplate(name="Yena", group_name="IZ*ONE", rarity="B", era="BLOOMIZ", base_vocal=78, base_dance=79, base_rap=18),
            IdolTemplate(name="Wonyoung", group_name="IZ*ONE", rarity="B", era="BLOOMIZ", base_vocal=84, base_dance=74, base_rap=17),
            IdolTemplate(name="Chaewon", group_name="IZ*ONE", rarity="B", era="BLOOMIZ", base_vocal=90, base_dance=68, base_rap=17),
            IdolTemplate(name="Chaeyeon", group_name="IZ*ONE", rarity="B", era="BLOOMIZ", base_vocal=68, base_dance=90, base_rap=17),

            # Oneiric Diary
            IdolTemplate(name="Hitomi", group_name="IZ*ONE", rarity="SS", era="Oneiric Diary", base_vocal=86, base_dance=99, base_rap=50),
            IdolTemplate(name="Minju", group_name="IZ*ONE", rarity="S", era="Oneiric Diary", base_vocal=94, base_dance=89, base_rap=32),
            IdolTemplate(name="Nako", group_name="IZ*ONE", rarity="S", era="Oneiric Diary", base_vocal=96, base_dance=88, base_rap=31),
            IdolTemplate(name="Eunbi", group_name="IZ*ONE", rarity="S", era="Oneiric Diary", base_vocal=91, base_dance=92, base_rap=32),
            IdolTemplate(name="Hyewon", group_name="IZ*ONE", rarity="A", era="Oneiric Diary", base_vocal=80, base_dance=80, base_rap=35),
            IdolTemplate(name="Sakura", group_name="IZ*ONE", rarity="A", era="Oneiric Diary", base_vocal=81, base_dance=87, base_rap=27),
            IdolTemplate(name="Chaeyeon", group_name="IZ*ONE", rarity="A", era="Oneiric Diary", base_vocal=74, base_dance=96, base_rap=25),
            IdolTemplate(name="Yuri", group_name="IZ*ONE", rarity="B", era="Oneiric Diary", base_vocal=96, base_dance=62, base_rap=17),
            IdolTemplate(name="Yena", group_name="IZ*ONE", rarity="B", era="Oneiric Diary", base_vocal=78, base_dance=79, base_rap=18),
            IdolTemplate(name="Wonyoung", group_name="IZ*ONE", rarity="B", era="Oneiric Diary", base_vocal=84, base_dance=74, base_rap=17),
            IdolTemplate(name="Chaewon", group_name="IZ*ONE", rarity="B", era="Oneiric Diary", base_vocal=90, base_dance=68, base_rap=17),

# Era Final
            IdolTemplate(name="Sakura", group_name="IZ*ONE", rarity="SS", era="Oneiric Theater", base_vocal=88, base_dance=97, base_rap=50),
            IdolTemplate(name="Minju", group_name="IZ*ONE", rarity="S", era="Oneiric Theater", base_vocal=95, base_dance=88, base_rap=32),
            IdolTemplate(name="Eunbi", group_name="IZ*ONE", rarity="S", era="Oneiric Theater", base_vocal=92, base_dance=91, base_rap=32),
            IdolTemplate(name="Nako", group_name="IZ*ONE", rarity="S", era="Oneiric Theater", base_vocal=97, base_dance=87, base_rap=31),
            IdolTemplate(name="Hitomi", group_name="IZ*ONE", rarity="A", era="Oneiric Theater", base_vocal=84, base_dance=88, base_rap=23),
            IdolTemplate(name="Hyewon", group_name="IZ*ONE", rarity="A", era="Oneiric Theater", base_vocal=81, base_dance=79, base_rap=35),
            IdolTemplate(name="Chaewon", group_name="IZ*ONE", rarity="A", era="Oneiric Theater", base_vocal=93, base_dance=79, base_rap=23),
            IdolTemplate(name="Yuri", group_name="IZ*ONE", rarity="B", era="Oneiric Theater", base_vocal=97, base_dance=61, base_rap=17),
            IdolTemplate(name="Yena", group_name="IZ*ONE", rarity="B", era="Oneiric Theater", base_vocal=79, base_dance=78, base_rap=18),
            IdolTemplate(name="Wonyoung", group_name="IZ*ONE", rarity="B", era="Oneiric Theater", base_vocal=85, base_dance=73, base_rap=17),
            IdolTemplate(name="Chaeyeon", group_name="IZ*ONE", rarity="B", era="Oneiric Theater", base_vocal=69, base_dance=89, base_rap=17),

            #aespa
            # debut
            IdolTemplate(name="Giselle", group_name="aespa", rarity="SS", era="Debut", base_vocal=82, base_dance=75, base_rap=78),
            IdolTemplate(name="Ningning", group_name="aespa", rarity="S", era="Debut", base_vocal=98, base_dance=87, base_rap=30),
            IdolTemplate(name="Karina", group_name="aespa", rarity="A", era="Debut", base_vocal=78, base_dance=92, base_rap=25),
            IdolTemplate(name="Winter", group_name="aespa", rarity="C", era="Debut", base_vocal=84, base_dance=56, base_rap=15),

            # Next Level
            IdolTemplate(name="Ningning", group_name="aespa", rarity="SS", era="Next Level", base_vocal=99, base_dance=92, base_rap=44),
            IdolTemplate(name="Giselle", group_name="aespa", rarity="S", era="Next Level", base_vocal=84, base_dance=78, base_rap=53),
            IdolTemplate(name="Winter", group_name="aespa", rarity="A", era="Next Level", base_vocal=94, base_dance=81, base_rap=20),
            IdolTemplate(name="Karina", group_name="aespa", rarity="C", era="Next Level", base_vocal=55, base_dance=84, base_rap=16),

            # Savage
            IdolTemplate(name="Winter", group_name="aespa", rarity="SS", era="Savage", base_vocal=97, base_dance=95, base_rap=43),
            IdolTemplate(name="Karina", group_name="aespa", rarity="S", era="Savage", base_vocal=80, base_dance=98, base_rap=37),
            IdolTemplate(name="Ningning", group_name="aespa", rarity="A", era="Savage", base_vocal=98, base_dance=75, base_rap=22),
            IdolTemplate(name="Giselle", group_name="aespa", rarity="C", era="Savage", base_vocal=72, base_dance=58, base_rap=25),

            # Girls
            IdolTemplate(name="Karina", group_name="aespa", rarity="SS", era="Girls", base_vocal=78, base_dance=99, base_rap=58),
            IdolTemplate(name="Winter", group_name="aespa", rarity="S", era="Girls", base_vocal=95, base_dance=90, base_rap=30),
            IdolTemplate(name="Giselle", group_name="aespa", rarity="A", era="Girls", base_vocal=79, base_dance=72, base_rap=44),
            IdolTemplate(name="Ningning", group_name="aespa", rarity="C", era="Girls", base_vocal=88, base_dance=52, base_rap=15),

            # Spicy
            IdolTemplate(name="Giselle", group_name="aespa", rarity="SS", era="Spicy", base_vocal=84, base_dance=78, base_rap=73),
            IdolTemplate(name="Karina", group_name="aespa", rarity="S", era="Spicy", base_vocal=79, base_dance=97, base_rap=39),
            IdolTemplate(name="Winter", group_name="aespa", rarity="A", era="Spicy", base_vocal=95, base_dance=80, base_rap=20),
            IdolTemplate(name="Ningning", group_name="aespa", rarity="C", era="Spicy", base_vocal=88, base_dance=52, base_rap=15),

            # Supernova / Armageddon
            IdolTemplate(name="Ningning", group_name="aespa", rarity="SS", era="Supernova / Armageddon", base_vocal=99, base_dance=93, base_rap=43),
            IdolTemplate(name="Winter", group_name="aespa", rarity="S", era="Supernova / Armageddon", base_vocal=96, base_dance=89, base_rap=30),
            IdolTemplate(name="Giselle", group_name="aespa", rarity="A", era="Supernova / Armageddon", base_vocal=81, base_dance=72, base_rap=42),
            IdolTemplate(name="Karina", group_name="aespa", rarity="C", era="Supernova / Armageddon", base_vocal=56, base_dance=83, base_rap=16),

            # Rich Man
            IdolTemplate(name="Winter", group_name="aespa", rarity="SS", era="Rich Man", base_vocal=98, base_dance=94, base_rap=43),
            IdolTemplate(name="Karina", group_name="aespa", rarity="S", era="Rich Man", base_vocal=80, base_dance=97, base_rap=38),
            IdolTemplate(name="Ningning", group_name="aespa", rarity="A", era="Rich Man", base_vocal=98, base_dance=75, base_rap=22),
            IdolTemplate(name="Giselle", group_name="aespa", rarity="C", era="Rich Man", base_vocal=72, base_dance=58, base_rap=25),


            # =========================================================
            # 💎 LE SSERAFIM (BALANCEADO REAL)
            # Todas mínimo 1 SS + 1 S
            # =========================================================

            # Fearless
            IdolTemplate(name="Eunchae", group_name="LE SSERAFIM", rarity="SS", era="Fearless", base_vocal=72, base_dance=98, base_rap=65),
            IdolTemplate(name="Kazuha", group_name="LE SSERAFIM", rarity="S", era="Fearless", base_vocal=74, base_dance=97, base_rap=44),
            IdolTemplate(name="Yunjin", group_name="LE SSERAFIM", rarity="A", era="Fearless", base_vocal=97, base_dance=78, base_rap=20),
            IdolTemplate(name="Sakura", group_name="LE SSERAFIM", rarity="B", era="Fearless", base_vocal=76, base_dance=82, base_rap=17),
            IdolTemplate(name="Chaewon", group_name="LE SSERAFIM", rarity="C", era="Fearless", base_vocal=84, base_dance=56, base_rap=15),

            # Antifragile
            IdolTemplate(name="Kazuha", group_name="LE SSERAFIM", rarity="SS", era="Antifragile", base_vocal=76, base_dance=99, base_rap=60),
            IdolTemplate(name="Chaewon", group_name="LE SSERAFIM", rarity="S", era="Antifragile", base_vocal=96, base_dance=88, base_rap=31),
            IdolTemplate(name="Sakura", group_name="LE SSERAFIM", rarity="A", era="Antifragile", base_vocal=78, base_dance=92, base_rap=25),
            IdolTemplate(name="Eunchae", group_name="LE SSERAFIM", rarity="B", era="Antifragile", base_vocal=70, base_dance=88, base_rap=17),
            IdolTemplate(name="Yunjin", group_name="LE SSERAFIM", rarity="C", era="Antifragile", base_vocal=89, base_dance=51, base_rap=15),

            # Unforgiven
            IdolTemplate(name="Yunjin", group_name="LE SSERAFIM", rarity="SS", era="Unforgiven", base_vocal=99, base_dance=91, base_rap=45),
            IdolTemplate(name="Sakura", group_name="LE SSERAFIM", rarity="S", era="Unforgiven", base_vocal=81, base_dance=96, base_rap=38),
            IdolTemplate(name="Eunchae", group_name="LE SSERAFIM", rarity="A", era="Unforgiven", base_vocal=72, base_dance=95, base_rap=28),
            IdolTemplate(name="Kazuha", group_name="LE SSERAFIM", rarity="B", era="Unforgiven", base_vocal=74, base_dance=84, base_rap=17),
            IdolTemplate(name="Chaewon", group_name="LE SSERAFIM", rarity="C", era="Unforgiven", base_vocal=86, base_dance=54, base_rap=15),

            # Easy / Crazy
            IdolTemplate(name="Sakura", group_name="LE SSERAFIM", rarity="SS", era="Easy / Crazy", base_vocal=82, base_dance=97, base_rap=56),
            IdolTemplate(name="Chaewon", group_name="LE SSERAFIM", rarity="S", era="Easy / Crazy", base_vocal=97, base_dance=87, base_rap=31),
            IdolTemplate(name="Kazuha", group_name="LE SSERAFIM", rarity="A", era="Easy / Crazy", base_vocal=74, base_dance=97, base_rap=24),
            IdolTemplate(name="Yunjin", group_name="LE SSERAFIM", rarity="B", era="Easy / Crazy", base_vocal=95, base_dance=61, base_rap=19),
            IdolTemplate(name="Eunchae", group_name="LE SSERAFIM", rarity="C", era="Easy / Crazy", base_vocal=68, base_dance=72, base_rap=15),



        ]

        session.add_all(idols)
        await session.commit()
        print(f"Database seeded with {len(idols)} idols!")

if __name__ == "__main__":
    asyncio.run(seed())
