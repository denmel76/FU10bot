import os

# Данные из ВК
VK_TOKEN = os.environ.get("VK_TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID", 0))
# Ваш личный ID ВК (чтобы присылать уведомления). Узнать можно в настройках профиля.
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0)) 

SERVICES = {
    "haircut": "Стрижка (2000 ₽)",
    "color": "Окрашивание (5000 ₽)",
    "manicure": "Маникюр (1500 ₽)"
}

MASTERS = {
    "anna": "Анна",
    "elena": "Елена",
    "maria": "Мария"
}
