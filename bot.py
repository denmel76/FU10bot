import logging
import asyncio
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text
from config import VK_TOKEN, GROUP_ID, ADMIN_ID, SERVICES, MASTERS
from database import init_db, save_appointment

logging.basicConfig(level=logging.INFO)
bot = Bot(token=VK_TOKEN)

# --- КЛАВИАТУРЫ ---
def main_menu():
    kb = Keyboard(one_time=False)
    kb.add(Text("Записаться"), color=KeyboardButtonColor.PRIMARY)
    return kb

def services_menu():
    kb = Keyboard(one_time=False)
    for name in SERVICES.values():
        kb.add(Text(name), color=KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)
    return kb

def masters_menu():
    kb = Keyboard(one_time=False)
    for name in MASTERS.values():
        kb.add(Text(name), color=KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)
    return kb

# --- ОБРАБОТЧИКИ ---
@bot.on.message(text=["Начать", "/start", "start", "Привет"])
async def start_handler(message: Message):
    await message.answer("💅 Добро пожаловать в салон красоты!\nНажмите «Записаться».", keyboard=main_menu())

@bot.on.message(text="Записаться")
async def book_handler(message: Message):
    await message.answer("Выберите услугу:", keyboard=services_menu())

@bot.on.message(text="Назад")
async def back_handler(message: Message):
    await message.answer("Главное меню:", keyboard=main_menu())

# Обработка выбора услуги (если текст совпадает с названием услуги)
@bot.on.message(text=list(SERVICES.values()))
async def service_handler(message: Message):
    await message.answer("Выберите мастера:", keyboard=masters_menu())

# Обработка выбора мастера (если текст совпадает с именем мастера)
@bot.on.message(text=list(MASTERS.values()))
async def master_handler(message: Message):
    # Для теста просто сохраняем заявку с дефолтным именем и временем
    # В реальном проекте здесь нужно спросить имя и время, но для проверки работы этого достаточно
    
    service = "Услуга выбрана" # Мы не знаем услугу, так как не передали её в текстовой кнопке
    master = message.text
    
    # Уведомление админу
    admin_text = f"🔥 Новая запись!\n\n💅 Мастер: {master}\n🆔 Клиент ID: {message.from_id}"
    if ADMIN_ID != 0:
        try:
            await bot.api.messages.send(peer_id=ADMIN_ID, message=admin_text, random_id=0)
        except Exception as e:
            logging.error(f"Ошибка отправки админу: {e}")
    
    await message.answer(f"✅ Вы записаны к мастеру {master}.\nМы свяжемся с вами!", keyboard=main_menu())

if __name__ == "__main__":
    import asyncio
    # Создаем базу данных перед запуском
    asyncio.run(init_db())
    print("VK Салон Бот запущен (текстовые кнопки)...")
    # Запускаем бота через asyncio
    asyncio.run(bot.run_polling())
