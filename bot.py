import os
import asyncio
from datetime import datetime, timedelta
from mcstatus import BedrockServer
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ====== НАСТРОЙКИ ======
TOKEN = "TOKEN"
CHAT_ID = int(os.getenv("CHAT_ID"))
# Онлайн для Анархии 1
ANARCHY1_IP = "92.38.222.133"
ANARCHY1_PORT = 19132

# InMine сервера
INMINE_SERVERS = {
    "1 Выживание inmine.ru:19132": ("inmine.ru", 19132),
    "2 Выживание inmine.ru:19133": ("inmine.ru", 19133),
    "3 Выживание inmine.ru:19134": ("inmine.ru", 19134),
    "4 Выживание inmine.ru:19135": ("inmine.ru", 19135),
}

# MineFun сервер
MINEFUN_IP = "minefun.ru"
MINEFUN_PORT = 19132

# ======================

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Состояние уведомлений ФанДропа
fd_notify = False

# ====== КНОПКИ ======
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎁 Время до ФанДропа")],
        [KeyboardButton(text="📊 Онлайн сервера")],
        [KeyboardButton(text="🌐 Выбрать проект")]
    ],
    resize_keyboard=True
)

online_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🟥 Анархия 1"), KeyboardButton(text="🟧 Анархия 2")],
        [KeyboardButton(text="🟨 Анархия 3"), KeyboardButton(text="🟩 Анархия 4")],
        [KeyboardButton(text="🟦 Анархия 5"), KeyboardButton(text="◀️ Назад")]
    ],
    resize_keyboard=True
)

projects_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="MineFun.ru"), KeyboardButton(text="InMine.ru")],
        [KeyboardButton(text="◀️ Назад")]
    ],
    resize_keyboard=True
)

inmine_servers_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1 Выживание inmine.ru:19132"), KeyboardButton(text="2 Выживание inmine.ru:19133")],
        [KeyboardButton(text="3 Выживание inmine.ru:19134"), KeyboardButton(text="4 Выживание inmine.ru:19135")],
        [KeyboardButton(text="◀️ Назад")]
    ],
    resize_keyboard=True
)

# ====== Функция ФанДропа ======
def get_next_fandrop():
    now = datetime.now()
    next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return next_hour

# ====== /start ======
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 Бот запущен!\nИспользуй кнопки ниже 👇",
        reply_markup=menu
    )

# ====== ФанДроп ======
@dp.message(lambda m: m.text == "🎁 Время до ФанДропа")
async def fd_time(message: types.Message):
    next_fd = get_next_fandrop()
    now = datetime.now()
    delta = next_fd - now
    minutes = delta.seconds // 60
    seconds = delta.seconds % 60
    await message.answer(
        f"🎁 Следующий ФанДроп:\n"
        f"🕒 {next_fd.strftime('%H:%M')}\n"
        f"⏳ Осталось: {minutes} мин {seconds} сек"
    )

@dp.message(Command("fd"))
async def fd_commands(message: types.Message):
    global fd_notify
    text = message.text.lower()
    if "uvedom on" in text:
        fd_notify = True
        await message.answer("🔔 Уведомления ФанДропа ВКЛЮЧЕНЫ")
    elif "uvedom off" in text:
        fd_notify = False
        await message.answer("🔕 Уведомления ФанДропа ВЫКЛЮЧЕНЫ")

async def fandrop_watcher():
    global fd_notify
    last_sent = None
    while True:
        now = datetime.now()
        next_fd = get_next_fandrop()
        if fd_notify and now >= next_fd:
            if last_sent != next_fd:
                await bot.send_message(
                    CHAT_ID,
                    "🎁 ФАНДРОП ЗАСПАВНИЛСЯ!\n🚀 Можете заходить на сервер!"
                )
                last_sent = next_fd
        await asyncio.sleep(5)

# ====== Онлайн сервера ======
@dp.message(lambda m: m.text == "📊 Онлайн сервера")
async def online_menu_msg(message: types.Message):
    await message.answer("Выберите анархию:", reply_markup=online_menu)

@dp.message(lambda m: m.text.startswith(("🟥","🟧","🟨","🟩","🟦","◀️")))
async def online_select(message: types.Message):
    if message.text == "◀️ Назад":
        await message.answer("Меню:", reply_markup=menu)
        return

    if message.text == "🟥 Анархия 1":
        try:
            server = BedrockServer(ANARCHY1_IP, ANARCHY1_PORT)
            status = server.status()
            await message.answer(f"🟥 Анархия 1\n🟢 Онлайн: {status.players.online}")
        except Exception as e:
            await message.answer(f"🟥 Анархия 1\n❌ Не удалось получить онлайн: {e}")
    else:
        await message.answer(f"{message.text}\n❓ Онлайн неизвестен")

# ====== Меню проекта ======
@dp.message(lambda m: m.text == "🌐 Выбрать проект")
async def select_project(message: types.Message):
    await message.answer("Выберите проект:", reply_markup=projects_menu)

@dp.message(lambda m: m.text in ["MineFun.ru", "InMine.ru"])
async def project_select(message: types.Message):
    if message.text == "InMine.ru":
        await message.answer("Выберите сервер:", reply_markup=inmine_servers_menu)
    else:  # MineFun
        await message.answer(
            "Сервера MineFun.ru\n⚠️ Если сервер уйдёт на тех. работы, уведомление придёт в чат\nПодробнее: https://t.me/minefun_ru"
        )

# ====== Проверка серверов InMine ======
@dp.message(lambda m: any(name in m.text for name in INMINE_SERVERS))
async def inmine_server_status(message: types.Message):
    server_info = INMINE_SERVERS.get(message.text)
    if server_info:
        ip, port = server_info
        try:
            server = BedrockServer(ip, port)
            status = server.status()
            await message.answer(
                f"✅ Сервер: {ip}:{port}\n"
                f"🟢 Онлайн: {status.players.online}\n"
                f"🏓 Пинг: {status.latency} ms"
            )
        except Exception as e:
            await message.answer(f"❌ Не удалось получить статус сервера {ip}:{port}:\n{e}")
    else:
        await message.answer("❌ Сервер не найден")

# ====== MineFun watcher ======
async def minefun_watcher():
    last_status = True
    while True:
        try:
            server = BedrockServer(MINEFUN_IP, MINEFUN_PORT)
            server.status()
            if not last_status:
                await bot.send_message(CHAT_ID, "✅ Сервер MineFun снова онлайн")
            last_status = True
        except:
            if last_status:
                await bot.send_message(CHAT_ID, "⚠️ Сервер MineFun ушёл на тех.работы\nПодробнее: https://t.me/minefun_ru")
            last_status = False
        await asyncio.sleep(30)

# ====== ЗАПУСК ======
async def main():
    asyncio.create_task(fandrop_watcher())
    asyncio.create_task(minefun_watcher())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
