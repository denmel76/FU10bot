import aiosqlite

DB_NAME = "vk_salon.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                service TEXT,
                master TEXT,
                appointment_time TEXT,
                status TEXT DEFAULT 'new'
            )
        """)
        await db.commit()

async def save_appointment(user_id, name, service, master, appointment_time):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO appointments (user_id, name, service, master, appointment_time) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, service, master, appointment_time)
        )
        await db.commit()
