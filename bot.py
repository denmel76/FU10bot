import asyncio
import aiohttp
import logging
from config import VK_TOKEN, GROUP_ID, ADMIN_ID, SERVICES, MASTERS
from database import init_db, save_appointment

logging.basicConfig(level=logging.INFO)

# --- БАЗОВЫЕ ФУНКЦИИ VK API ---
async def vk_api_request(method, params):
    url = f"https://api.vk.com/method/{method}"
    params["access_token"] = VK_TOKEN
    params["v"] = "5.199"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=params) as resp:
            return await resp.json()

async def send_message(peer_id, text, keyboard=None):
    params = {
        "peer_id": peer_id,
        "message": text,
        "random_id": 0
    }
    if keyboard:
        params["keyboard"] = keyboard
    await vk_api_request("messages.send", params)

# --- КЛАВИАТУРЫ (JSON формат) ---
def get_main_keyboard():
    return '{"one_time":false,"buttons":[[{"action":{"type":"text","label":"Записаться"},"color":"primary"}]]}'

def get_services_keyboard():
    buttons = []
    for name in SERVICES.values():
        buttons.append([{"action": {"type": "text", "label": name}, "color": "secondary"}])
    buttons.append([{"action": {"type": "text", "label": "Назад"}, "color": "negative"}])
    return '{"one_time":false,"buttons":' + str(buttons).replace("'", '"') + '}'

def get_masters_keyboard():
    buttons = []
    for name in MASTERS.values():
        buttons.append([{"action": {"type": "text", "label": name}, "color": "secondary"}])
    buttons.append([{"action": {"type": "text", "label": "Назад"}, "color": "negative"}])
    return '{"one_time":false,"buttons":' + str(buttons).replace("'", '"') + '}'

# --- ОСНОВНОЙ ЦИКЛ (LongPoll) ---
async def main():
    await init_db()
    print("VK Салон Бот (на чистом API) запущен...")
    
    # Получаем сервер для LongPoll
    server_data = await vk_api_request("groups.getLongPollServer", {"group_id": GROUP_ID})
    if "response" not in server_data:
        print(f"Ошибка получения сервера: {server_data}")
        return
    
    server = server_data["response"]["server"]
    key = server_data["response"]["key"]
    ts = server_data["response"]["ts"]

    while True:
        url = f"{server}?act=a_check&key={key}&ts={ts}&wait=25"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.json()
                    
                    if "failed" in data:
                        print(f"Ошибка LongPoll: {data}")
                        # Перезапрашиваем сервер при ошибке
                        server_data = await vk_api_request("groups.getLongPollServer", {"group_id": GROUP_ID})
                        server = server_data["response"]["server"]
                        key = server_data["response"]["key"]
                        ts = server_data["response"]["ts"]
                        continue

                    ts = data["ts"]
                    
                    for update in data.get("updates", []):
                        if update["type"] == "message_new":
                            msg = update["object"]["message"]
                            peer_id = msg["peer_id"]
                            text = msg.get("text", "").strip()

                            # ЛОГИКА ОТВЕТОВ
                            if text in ["Начать", "/start", "start", "Привет"]:
                                await send_message(peer_id, "💅 Добро пожаловать в салон красоты!\nНажмите «Записаться».", get_main_keyboard())
                            
                            elif text == "Записаться":
                                await send_message(peer_id, "Выберите услугу:", get_services_keyboard())
                            
                            elif text == "Назад":
                                await send_message(peer_id, "Главное меню:", get_main_keyboard())
                            
                            elif text in SERVICES.values():
                                await send_message(peer_id, "Выберите мастера:", get_masters_keyboard())
                            
                            elif text in MASTERS.values():
                                # Сохраняем заявку (упрощенно)
                                await save_appointment(msg["from_id"], "Клиент", "Услуга", text, "Время не указано")
                                await send_message(peer_id, f"✅ Вы записаны к мастеру {text}.\nМы свяжемся с вами!", get_main_keyboard())
                                
                                # Уведомление админу
                                if ADMIN_ID != 0:
                                    await send_message(ADMIN_ID, f"🔥 Новая запись!\nМастер: {text}\nКлиент ID: {msg['from_id']}")
                            
                            else:
                                await send_message(peer_id, "Я вас не понял. Нажмите «Начать».", get_main_keyboard())
        except Exception as e:
            print(f"Ошибка в цикле: {e}")
            await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())
