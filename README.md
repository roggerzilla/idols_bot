# 🌟 Bot Idols - Telegram Management Bot

Un bot de gestión de idols K-Pop con economía, contratos, eventos NSFW y mecánicas de riesgo/recompensa.

## 🚀 Instalación

1.  Clonar el repositorio.
2.  Instalar dependencias:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configurar el token en `.env`:
    ```env
    TELEGRAM_TOKEN=tu_token_aqui
    ```
4.  Sembrar la base de datos con idols iniciales:
    ```bash
    python scripts/seed_db.py
    ```
5.  Ejecutar el bot:
    ```bash
    python main.py
    ```

## 🎮 Características

### 1. Gestión de Idols
- **Gacha:** Recluta idols de rarezas C, B, A, S y SS.
- **Contratos:** Las idols tienen contratos de 7 días y requieren mantenimiento diario.
- **Stats:** Mejora Vocal, Dance y Rap para dominar los charts.

### 2. Economía y Comebacks
- **Lanzamiento de Álbum:** Gasta puntos para lanzar un comeback. El éxito depende de los stats, la rareza y la suerte (Charts).
- **Maintenance:** Si no tienes puntos para el staff, tus idols entran en **Hiatus**.

### 3. Interactividad
- **World Tour:** Envía a tus idols a giras mundiales para ganar recompensas masivas (bloqueo temporal).
- **Eventos NSFW:** "Sponsors" que ofrecen grandes sumas de puntos a cambio de la moral de tus idols. Escándalos aleatorios que afectan la reputación.

### 4. Próximamente
- **Music Bank Battles:** Duelos PVP entre agencias.
- **Trading Market:** Venta y subasta de idols entre usuarios.
- **Fandoms:** Compite por la gloria de tu fandom favorito (ONCE, FEARNOT, etc.).

## 🛠️ Tecnologías
- Python 3.10+
- python-telegram-bot (Async)
- SQLAlchemy (Async SQLite)
- APScheduler (Mantenimiento)
