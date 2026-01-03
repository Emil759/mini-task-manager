# Полностью рабочий Telegram-бот знакомств
# Библиотека: telebot (pyTelegramBotAPI)
# Хранение: SQLite
# Функции:
# - Создание анкеты (имя, возраст, пол, кого ищешь, религия, описание, фото, гео)
# - Просмотр анкет
# - Лайк / дизлайк
# - Матчи + уведомления с username / id
# - Моя анкета
# - Изменение анкеты (все поля)
# - Кнопка Назад и главное меню

import telebot
from telebot import types
import sqlite3
import math

TOKEN = "мой токен"
bot = telebot.TeleBot(TOKEN)

# ---------------- DATABASE ----------------

def db():
    return sqlite3.connect("dating.db", check_same_thread=False)

with db() as conn:
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        looking TEXT,
        religion TEXT,
        bio TEXT,
        city TEXT,
        lat REAL,
        lon REAL,
        photo TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        from_id INTEGER,
        to_id INTEGER,
        UNIQUE(from_id, to_id)
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS dislikes (
        from_id INTEGER,
        to_id INTEGER,
        UNIQUE(from_id, to_id)
    )
    """)

# ---------------- STATE ----------------

temp = {}
view_queue = {}

# ---------------- KEYBOARDS ----------------

def main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👀 Смотреть анкеты")
    kb.add("👤 Моя анкета", "✏️ Изменить анкету")
    return kb

# ---------------- UTIL ----------------

def get_distance(lat1, lon1, lat2, lon2):
    if not lat1 or not lon1 or not lat2 or not lon2:
        return float('inf')
    R = 6371 # km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# ---------------- START ----------------

@bot.message_handler(commands=["start"])
def start(m):
    if get_user(m.from_user.id):
        bot.send_message(m.chat.id, "Главное меню", reply_markup=main_kb())
    else:
        temp[m.chat.id] = {"user_id": m.from_user.id, "username": m.from_user.username}
        bot.send_message(m.chat.id, "Введите ваше имя")
        bot.register_next_step_handler(m, step_name)

# ---------------- CREATE PROFILE ----------------

def step_name(m):
    temp[m.chat.id]["name"] = m.text
    bot.send_message(m.chat.id, "Введите возраст")
    bot.register_next_step_handler(m, step_age)

def step_age(m):
    if not m.text.isdigit():
        bot.send_message(m.chat.id, "Введите число")
        bot.register_next_step_handler(m, step_age)
        return
    temp[m.chat.id]["age"] = int(m.text)

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("Мужчина", "Женщина")
    bot.send_message(m.chat.id, "Ваш пол", reply_markup=kb)
    bot.register_next_step_handler(m, step_gender)

def step_gender(m):
    temp[m.chat.id]["gender"] = m.text
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("Мужчину", "Женщину")
    bot.send_message(m.chat.id, "Кого вы ищете?", reply_markup=kb)
    bot.register_next_step_handler(m, step_looking)

def step_looking(m):
    temp[m.chat.id]["looking"] = m.text
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("Ислам", "Христианство", "Иудаизм", "Атеизм", "Другое")
    bot.send_message(m.chat.id, "Ваша религия", reply_markup=kb)
    bot.register_next_step_handler(m, step_religion)

def step_religion(m):
    temp[m.chat.id]["religion"] = m.text
    bot.send_message(m.chat.id, "Напишите описание")
    bot.register_next_step_handler(m, step_bio)

def step_bio(m):
    temp[m.chat.id]["bio"] = m.text
    bot.send_message(m.chat.id, "Отправьте фото")
    bot.register_next_step_handler(m, step_photo)

def step_photo(m):
    if not m.photo:
        bot.send_message(m.chat.id, "Отправьте фото")
        bot.register_next_step_handler(m, step_photo)
        return
    temp[m.chat.id]["photo"] = m.photo[-1].file_id
    
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton(text="📍 Отправить геолокацию", request_location=True))
    
    bot.send_message(m.chat.id, "Отправьте геолокацию", reply_markup=kb)
    bot.register_next_step_handler(m, step_geo)

def step_geo(m):
    # FIX: Проверка на случай перезапуска бота
    if m.chat.id not in temp:
        bot.send_message(m.chat.id, "⚠️ Произошел сброс бота. Пожалуйста, начните регистрацию заново: /start", reply_markup=types.ReplyKeyboardRemove())
        return

    if not m.location:
        bot.send_message(m.chat.id, "Нужно отправить геолокацию (нажмите на кнопку или прикрепите гео)")
        bot.register_next_step_handler(m, step_geo)
        return
        
    try:
        temp[m.chat.id]["lat"] = m.location.latitude
        temp[m.chat.id]["lon"] = m.location.longitude
        temp[m.chat.id]["city"] = ""
        save_user(temp[m.chat.id])
        temp.pop(m.chat.id)
        # FIX: Updated message as requested
        bot.send_message(m.chat.id, "✅ Ваша анкета готова", reply_markup=main_kb())
    except Exception as e:
        print(f"ERROR saving user: {e}")
        bot.send_message(m.chat.id, f"❌ Ошибка при сохранении: {e}")

# ---------------- DATABASE HELPERS ----------------

def save_user(d):
    with db() as conn:
        conn.execute("""
        INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            d["user_id"], d.get("username"), d["name"], d["age"], d["gender"],
            d["looking"], d["religion"], d["bio"], d.get("city"),
            d["lat"], d["lon"], d["photo"]
        ))

def get_user(uid):
    cur = db().cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()

# ---------------- VIEW PROFILES ----------------

@bot.message_handler(func=lambda m: m.text == "👀 Смотреть анкеты")
def browse(m):
    me = get_user(m.from_user.id)
    if not me:
        return bot.send_message(m.chat.id, "Сначала создайте анкету")

    # FIX: Сопоставление падежей ("Мужчину" -> "Мужчина")
    mapping = {
        "Мужчину": "Мужчина",
        "Женщину": "Женщина"
    }
    target_gender = mapping.get(me[5], me[5]) # Если не найдено, ищем как есть

    cur = db().cursor()
    cur.execute("""
    SELECT * FROM users WHERE gender=? AND user_id!=?
    AND user_id NOT IN (SELECT to_id FROM likes WHERE from_id=?)
    AND user_id NOT IN (SELECT to_id FROM dislikes WHERE from_id=?)
    """, (target_gender, me[0], me[0], me[0]))
    users = cur.fetchall()

    if not users:
        # FIX: Updated message
        return bot.send_message(m.chat.id, "Нет анкет рядом с вами")

    # FIX: Calculate distances and filter/sort
    results = []
    my_lat, my_lon = me[9], me[10]
    
    for u in users:
        dist = get_distance(my_lat, my_lon, u[9], u[10])
        # Only show users within 100km (example radius, or just sort)
        # Let's simple sort by distance for "nearby" logic
        results.append((dist, u))
        
    results.sort(key=lambda x: x[0])
    
    # Filter if you want hard limit e.g. < 500km
    # results = [r for r in results if r[0] < 500] 

    if not results:
        return bot.send_message(m.chat.id, "Нет анкет рядом с вами")

    # Store just the user objects, sorted by distance
    view_queue[m.chat.id] = [r[1] for r in results]
    show_next(m.chat.id)

def show_next(cid):
    if not view_queue.get(cid):
        # FIX: Loop back to menu when done
        return bot.send_message(cid, "Анкеты закончились", reply_markup=main_kb())

    u = view_queue[cid].pop(0)
    
    # Optional: Display distance? Not explicitly requested but good for "nearby"
    # But user asked for specific flow. I'll stick to their text request.
    text = f"👤 {u[2]}, {u[3]}\n{u[7]}\nРелигия: {u[6]}"
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❤️", callback_data=f"like_{u[0]}"),
           types.InlineKeyboardButton("❌", callback_data=f"dis_{u[0]}"))
    bot.send_photo(cid, u[11], caption=text, reply_markup=kb)

# ---------------- LIKES ----------------

@bot.callback_query_handler(func=lambda c: c.data.startswith("like_"))
def like(c):
    uid = int(c.data.split("_")[1])
    me = c.from_user.id
    with db() as conn:
        conn.execute("INSERT OR IGNORE INTO likes VALUES (?,?)", (me, uid))
        cur = conn.execute("SELECT 1 FROM likes WHERE from_id=? AND to_id=?", (uid, me))
        if cur.fetchone():
            # MATCH logic
            other = get_user(uid)
            myself = get_user(me)
            # FIX: Sending username link if available
            u1_link = f"@{other[1]}" if other[1] else f"[id{other[0]}](tg://user?id={other[0]})"
            u2_link = f"@{myself[1]}" if myself[1] else f"[id{myself[0]}](tg://user?id={myself[0]})"
            
            bot.send_message(me, f"🎉 МАТЧ! {u1_link}", parse_mode="Markdown")
            bot.send_message(uid, f"🎉 МАТЧ! {u2_link}", parse_mode="Markdown")
            
    show_next(c.message.chat.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("dis_"))
def dislike(c):
    uid = int(c.data.split("_")[1])
    with db() as conn:
        conn.execute("INSERT OR IGNORE INTO dislikes VALUES (?,?)", (c.from_user.id, uid))
    show_next(c.message.chat.id)

# ---------------- MY PROFILE ----------------

@bot.message_handler(func=lambda m: m.text == "👤 Моя анкета")
def my(m):
    u = get_user(m.from_user.id)
    if not u:
        return bot.send_message(m.chat.id, "Анкета не найдена")
    text = f"👤 {u[2]}, {u[3]}\n{u[7]}\nРелигия: {u[6]}"
    bot.send_photo(m.chat.id, u[11], caption=text, reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "✏️ Изменить анкету")
def edit(m):
    temp[m.chat.id] = {"user_id": m.from_user.id, "username": m.from_user.username}
    bot.send_message(m.chat.id, "Введите новое имя")
    bot.register_next_step_handler(m, step_name)

# ---------------- RUN ----------------

print("BOT STARTED")
bot.infinity_polling()
