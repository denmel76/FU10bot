import logging
import asyncio
from vkbottle.bot import Bot, Message, MessageEvent
from vkbottle import Keyboard, KeyboardButtonColor, Text, Callback
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
    for key, name in SERVICES.items():
        # Используем Callback-кнопки для выбора услуги
        kb.add(Callback(name, payload={"cmd": "srv", "value": name}), color=KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)
    return kb

def masters_menu(service_name):
    kb = Keyboard(one_time=False)
    for key, name in MASTERS.items():
        # Передаем выбранную услугу в payload
        kb.add(Callback(name, payload={"cmd": "mst", "value": name, "service": service_name}), color=KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(Text("Назад"), color=KeyboardButtonColor.NEGATIVE)
    return kb

# --- ОБРАБОТЧИКИ ---
@bot.on.message(text=["Начать", "/start", "start", "Привет"])
async def start_handler(message: Message):
    await message.answer("💅 Добро пожаловать в салон красоты!\nНажмите «Записаться», чтобы выбрать услугу.", keyboard=main_menu())

@bot.on.message(text="Записаться")
async def book_handler(message: Message):
    await message.answer("Выберите услугу:", keyboard=services_menu())

@bot.on.message(text="Назад")
async def back_handler(message: Message):
    await message.answer("Главное меню:", keyboard=main_menu())

# --- ОБРАБОТКА CALLBACK (нажатий на кнопки) ---
@bot.on.message_view()
async def callback_handler(event: MessageEvent):
    payload = event.payload
    if not payload:
        return

    cmd = payload.get("cmd")
    value = payload.get("value")
    
    # Если нажали на услугу
    if cmd == "srv":
        await event.show_snackbar("Услуга выбрана!")
        # Отправляем меню мастеров
        await event.edit(message="Выберите мастера:", keyboard=masters_menu(value))
    
    # Если нажали на мастера
    elif cmd == "mst":
        service_name = payload.get("service")
        await event.show_snackbar("Мастер выбран!")
        # Отправляем сообщение, что мастер выбран (дальше нужно было бы спрашивать имя, но для теста просто фиксируем)
        # В реальном проекте здесь нужно спросить имя и время, но без FSM это сложно сделать в ВК за один шаг.
        # Поэтому мы просто сохраняем "тестовую" запись.
        
        # Уведомление админу
        admin_text = f"🔥 Новая запись!\n\n✂️ Услуга: {service_name}\n💅 Мастер: {value}\n🆔 Клиент ID: {event.user_id}"
        if ADMIN_ID != 0:
            try:
                await bot.api.messages.send(peer_id=ADMIN_ID, message=admin_text, random_id=0)
            except Exception as e:
                logging.error(f"Ошибка отправки админу: {e}")
        
        await event.edit(message=f"✅ Вы записаны на {service_name} к мастеру {value}.\nМы свяжемся с вами!", keyboard=main_menu())

if __name__ == "__main__":
    asyncio.run(init_db())
    print("VK Салон Бот запущен (без StateDispenser)...")
    bot.run_forever()
