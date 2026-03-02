import os
import random
import asyncio
import json
import time
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update

TOKEN = os.getenv("8781591629:AAG9A1Eh1ufOlSLPDfcg68M8TgxSKI8u3qs")
CHAT_ID = int(os.getenv("-1002553476177"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
MEMORY_FILE = "skuf_memory.json"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
app = Flask(name)

# ================= STATE =================

state = {
    "drunk_level": 0,
    "location": "dacha",
    "binge": False,
    "last_messages": [],
    "spam_counter": 0,
    "last_mushroom_post": 0,
    "users": {}
}

# ================= LOAD/SAVE MEMORY =================

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            state["users"] = json.load(f)
    else:
        state["users"] = {}

def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(state["users"], f, ensure_ascii=False, indent=2)

# ================= DATA =================

FISH = ["карася", "щуку", "окуня", "судака", "леща"]
MUSHROOMS = ["подосиновики", "лисички", "опята", "маслята"]

START = ["Да", "Ну", "Эх", "Блин", "Слушай"]
MOOD = ["живём", "нормально всё", "крутимся", "держимся"]
DETAIL = ["рыба не клюёт", "грибы растут", "баня топится", "машина троит"]
ENDING = ["как можем", "и ладно", "переживём"]
INSERTIONS = ["эх...", "вот раньше было лучше...", "я ж говорил", "ты понимаешь о чём я"]

JOKES = [
    "Пошёл как-то карась в бар... не пустили.",
    "Гриб спрашивает гриб: ты чего такой красный? — Да мухомор я!",
    "Баня без веника — деньги на ветер."
]

# ================= MEMORY SYSTEM =================

def update_user(user_id, text):
    if str(user_id) not in state["users"]:
        state["users"][str(user_id)] = {"messages": 0, "last_topic": None, "annoyed": 0}

    user = state["users"][str(user_id)]
    user["messages"] += 1
    if "рыба" in text:
        user["last_topic"] = "fish"
    if "гриб" in text:
        user["last_topic"] = "mushroom"

def user_memory_response(user_id):
    user = state["users"].get(str(user_id))
    if not user:
        return None

    if user["messages"] > 15 and random.random() < 0.1:
        return "Ты что-то сегодня разговорился..."
    if user["last_topic"] == "fish" and random.random() < 0.2:
        return "Ты опять про рыбу... люблю я это дело."
    if user["annoyed"] > 3:
        return "Ты меня уже подбешиваешь немного..."
    return None

# ================= RESPONSE GENERATOR =================

def generate_response():
    parts = [
        random.choice(START),
        random.choice(MOOD),
        random.choice(DETAIL),
        random.choice(ENDING)
    ]
    sentence = " ".join(parts)
    if random.random() < 0.3:
        sentence += " " + random.choice(INSERTIONS)
    return sentence

def drunkify(text):
    if state["drunk_level"] >= 2:
        text = text.replace("о", "оо")
    if state["drunk_level"] >= 4:
        text += " бл..."
    if state["drunk_level"] >= 6:
        text = text.upper()
    return text

# ================= MUSHROOM AUTO =================

async def mushroom_scheduler():
    while True:
        await asyncio.sleep(random.randint(7200, 14400))  # 2–4 часа
        if state["location"] == "dacha":
            mush = random.choice(MUSHROOMS)
            try:
                await bot.send_message(CHAT_ID, f"Парни, гляньте какие {mush} нашёл 🍄")
            except:
                pass

# ================= MESSAGE HANDLER =================

@dp.message_handler()
async def handle_message(message: types.Message):
    text = message.text
    if not text:
        return

    user_id = message.from_user.id
    lower = text.lower()

    if state["binge"]:
        return

    update_user(user_id, lower)

    # CAPS
    if text.isupper() and len(text) > 5:
        state["users"][str(user_id)]["annoyed"] += 1
        await message.answer("Ты чего орёшь-то? Я не глухой...")
        save_memory()
        return# SPAM
    if state["last_messages"] and lower == state["last_messages"][-1]:
        state["spam_counter"] += 1
        state["users"][str(user_id)]["annoyed"] += 1
    else:
        state["spam_counter"] = 0

    if state["spam_counter"] >= 3:
        await message.answer("Да понял я, не долби одно и то же...")
        save_memory()
        return

    state["last_messages"].append(lower)
    if len(state["last_messages"]) > 5:
        state["last_messages"].pop(0)

    # MEMORY RESPONSE
    mem = user_memory_response(user_id)
    if mem:
        await message.answer(mem)
        save_memory()
        return

    # DRINK
    if "хлебни пивка" in lower:
        state["drunk_level"] += 1
        await message.answer("Хлебнул...")
        if state["drunk_level"] >= 9:
            await message.answer("Всё... хватит писать...")
        if state["drunk_level"] >= 10:
            state["binge"] = True
            await message.answer("Ухожу в запой...")
            await asyncio.sleep(3600)
            state["binge"] = False
            state["drunk_level"] = 0
            await message.answer("Фух, вот это я перебрал")
        save_memory()
        return

    # LOCATION SWITCH
    if "езжай на рыбалку" in lower:
        state["location"] = "fishing"
        await message.answer("Поехал на рыбалку...")
        save_memory()
        return

    if "езжай на дачу" in lower:
        state["location"] = "dacha"
        await message.answer("Вернулся на дачу.")
        save_memory()
        return

    # FISH
    if "рыбу поймай" in lower:
        if state["location"] != "fishing":
            await message.answer("Я сейчас не на рыбалке.")
            save_memory()
            return
        await message.answer("Щас...")
        await asyncio.sleep(random.randint(30, 60))
        await message.answer(f"Поймал {random.choice(FISH)}!")
        save_memory()
        return

    # SHOW MUSHROOMS
    if "покажи грибы" in lower:
        if state["location"] != "dacha":
            await message.answer("Я сейчас на рыбалке, не могу.")
            save_memory()
            return
        await message.answer(f"Смотри какие {random.choice(MUSHROOMS)} нашёл!")
        save_memory()
        return

    # RANDOM FUN
    if random.random() < 0.05:
        await message.answer("Эх, вот помню в школе кружками кидались...")
        save_memory()
        return

    # DEFAULT RESPONSE
    response = generate_response()
    response = drunkify(response)
    await message.answer(response)
    save_memory()

# ================= WEBHOOK =================

@app.route('/webhook', methods=['POST'])
async def webhook():
    update = Update(**request.json)
    await dp.process_update(update)
    return '', 200

@app.route('/')
def index():
    return "Skuf bot is alive"

# ================= STARTUP =================

if name == "main":
    load_memory()
    loop = asyncio.get_event_loop()
    loop.create_task(mushroom_scheduler())
    bot.set_webhook(WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))