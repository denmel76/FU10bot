import logging
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text
from vkbottle import BaseStateGroup, StateDispenser
from config import VK_TOKEN, GROUP_ID, ADMIN_ID, SERVICES, MASTERS
from database import init_db, save_appointment

logging.basicConfig(level=logging.INFO)
bot = Bot(token=VK_TOKEN)
state_dispenser = StateDispenser()

# --- СОСТОЯНИЯ (Чтобы бот помнил, на каком шаге пользователь) ---
class BookingState(BaseStateGroup):
    WAITING_SERVICE = "waiting_service"
    WAITING_MASTER = "waiting_master"
    WAITING_NAME = "waiting_name"
    WAITING_TIME = "waiting_time"

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
    await state_dispenser.delete(message.peer_id)
    await message.answer("💅 Добро пожаловать в салон красоты!\nНажмите «Записаться», чтобы выбрать услугу.", keyboard=main_menu())

@bot.on.message(text="Записаться")
async def book_handler(message: Message):
    await state_dispenser.set(message.peer_id, BookingState.WAITING_SERVICE)
    await message.answer("Выберите услугу:", keyboard=services_menu())

@bot.on.message(state=BookingState.WAITING_SERVICE)
async def service_handler(message: Message):
    if message.text == "Назад":
        await state_dispenser.delete(message.peer_id)
        return await message.answer("Главное меню:", keyboard=main_menu())
    
    if message.text not in SERVICES.values():
        return await message.answer("Пожалуйста, выберите услугу из списка ниже.", keyboard=services_menu())
    
    await state_dispenser.set(message.peer_id, BookingState.WAITING_MASTER, service=message.text)
    await message.answer("Выберите мастера:", keyboard=masters_menu())

@bot.on.message(state=BookingState.WAITING_MASTER)
async def master_handler(message: Message):
    if message.text == "Назад":
        await state_dispenser.set(message.peer_id, BookingState.WAITING_SERVICE)
        return await message.answer("Выберите услугу:", keyboard=services_menu())
    
    if message.text not in MASTERS.values():
        return await message.answer("Пожалуйста, выберите мастера из списка.", keyboard=masters_menu())
    
    await state_dispenser.set(message.peer_id, BookingState.WAITING_NAME, master=message.text)
    await message.answer("Введите ваше имя:")

@bot.on.message(state=BookingState.WAITING_NAME)
async def name_handler(message: Message):
    if len(message.text) < 2:
        return await message.answer("Имя слишком короткое. Введите имя еще раз:")
    
    await state_dispenser.set(message.peer_id, BookingState.WAITING_TIME, name=message.text)
    await message.answer("Введите желаемую дату и время (например: 25.10 в 15:00):")

@bot.on.message(state=BookingState.WAITING_TIME)
async def time_handler(message: Message):
    # Получаем данные, которые сохранили на прошлых шагах
    state_peer = await state_dispenser.get(message.peer_id)
    payload = state_peer.payload
    
    service = payload.get("service")
    master = payload.get("master")
    name = payload.get("name")
    time = message.text
    
    # Сохраняем в базу
    await save_appointment(message.from_id, name, service, master, time)
    
    # Уведомление админу
    admin_text = f"🔥 Новая запись!\n\n👤 Имя: {name}\n✂️ Услуга: {service}\n💅 Мастер: {master}\n⏰ Время: {time}\n🆔 Клиент ID: {message.from_id}"
    if ADMIN_ID != 0:
        try:
            await bot.api.messages.send(peer_id=ADMIN_ID, message=admin_text, random_id=0)
        except Exception as e:
            logging.error(f"Ошибка отправки админу: {e}")
    
    await state_dispenser.delete(message.peer_id)
    await message.answer(f"✅ Спасибо, {name}! Вы записаны на {service} к мастеру {master} на {time}.\nМы свяжемся с вами.", keyboard=main_menu())

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
    print("VK Салон Бот запущен...")
    bot.run_forever()
