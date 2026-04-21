import requests
import sqlite3
from datetime import date

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7907298890

API_URL = "https://anon-num-info.vercel.app/num"
API_KEY = "Yrnamw2104"
# ==========================================


# ================= DATABASE =================
db = sqlite3.connect("database.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
credits INTEGER,
premium INTEGER,
banned INTEGER,
last_reset TEXT
)
""")
db.commit()


# ================= USER SYSTEM =================
def get_user(user_id):

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        today = str(date.today())
        cursor.execute(
            "INSERT INTO users VALUES(?,?,?,?,?)",
            (user_id, 10, 0, 0, today),
        )
        db.commit()
        return (user_id,10,0,0,today)

    return user


def reset_daily(user_id):
    user = get_user(user_id)
    today = str(date.today())

    if user[3] != today:
        cursor.execute(
            "UPDATE users SET credits=?, last_reset=? WHERE user_id=?",
            (10, today, user_id),
        )
        db.commit()


def add_credit(user_id, amount):
    cursor.execute(
        "UPDATE users SET credits = credits + ? WHERE user_id=?",
        (amount, user_id),
    )
    db.commit()


def unlimited(user_id):
    cursor.execute(
        "UPDATE users SET premium=1 WHERE user_id=?",
        (user_id,),
    )
    db.commit()


def ban_user(user_id):
    cursor.execute(
        "UPDATE users SET banned=1 WHERE user_id=?",
        (user_id,),
    )
    db.commit()


def unban_user(user_id):
    cursor.execute(
        "UPDATE users SET banned=0 WHERE user_id=?",
        (user_id,),
    )
    db.commit()


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    get_user(update.effective_user.id)

    keyboard = [
        [InlineKeyboardButton("🔎 Search", callback_data="search")],
        [InlineKeyboardButton("💳 Balance", callback_data="balance")],
    ]

    await update.message.reply_text(
        "🤖 Number Info Bot",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ================= USER BUTTONS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "search":
        await query.message.reply_text("📱 Send Number")

    elif query.data == "balance":
        reset_daily(user_id)
        user = get_user(user_id)

        if user[2] == 1:
            msg = "👑 Unlimited User"
        else:
            msg = f"💳 Credits Left: {user[1]}"

        await query.message.reply_text(msg)


# ================= SEARCH =================
async def check_number(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # 🔥 ADMIN ACTION MODE FIRST
    if update.effective_user.id == ADMIN_ID and "admin_action" in context.user_data:
        await admin_action(update, context)
        return

    user_id = update.effective_user.id

    reset_daily(user_id)
    user = get_user(user_id)

    if user[3] == 1:
        await update.message.reply_text("❌ You are banned")
        return

    if user[2] == 0 and user[1] <= 0:
        await update.message.reply_text("❌ Daily limit finished")
        return

    number = update.message.text.strip()

    params = {"key": API_KEY, "num": number}

    try:
        r = requests.get(API_URL, params=params, timeout=10)
        data = r.json()

        info = data["response"]["data"][0]

        msg = f"""
📱 Number : {info.get('num','N/A')}
👤 Name   : {info.get('name','N/A')}
 father's name :{info.get ('fname', 'N/A')}
📍 Circle : {info.get('circle','N/A')}
📧 Email  : {info.get('email','N/A')}
🏠 Address: {info.get('address','N/A')}
aadhar : {info.get ('aadhar', 'N/A')}
Email :  {info.get ('email', 'N/A')}
Alternate no. :  {info.get ('alt', 'N/A')}


━━━━━━━━━━
🤖 Developed by Somesh 
"""

        await update.message.reply_text(msg)

        if user[2] == 0:
            cursor.execute(
                "UPDATE users SET credits = credits - 1 WHERE user_id=?",
                (user_id,),
            )
            db.commit()

    except:
        await update.message.reply_text("❌ Number not found")


# ================= ADMIN PANEL =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("👑 Unlimited User", callback_data="unlimited")],
        [InlineKeyboardButton("➕ Add Credits", callback_data="credit")],
        [InlineKeyboardButton("🚫 Ban User", callback_data="ban")],
        [InlineKeyboardButton("✅ Unban User", callback_data="unban")],
        [InlineKeyboardButton("📊 Total Users", callback_data="users")],
    ]

    await update.message.reply_text(
        "👑 ADMIN PANEL",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ================= ADMIN BUTTONS =================
async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    if query.data == "users":
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        await query.message.reply_text(f"👥 Total Users: {total}")
        return

    context.user_data["admin_action"] = query.data
    await query.message.reply_text("Send USER ID")


# ================= ADMIN ACTION =================
async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = int(update.message.text)
    action = context.user_data["admin_action"]

    if action == "unlimited":
        unlimited(uid)
        await update.message.reply_text("✅ Unlimited Added")

    elif action == "credit":
        add_credit(uid, 50)
        await update.message.reply_text("✅ Credits Added")

    elif action == "ban":
        ban_user(uid)
        await update.message.reply_text("✅ User Banned")

    elif action == "unban":
        unban_user(uid)
        await update.message.reply_text("✅ User Unbanned")

    del context.user_data["admin_action"]


# ================= MAIN =================
def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))

    app.add_handler(
        CallbackQueryHandler(buttons, pattern="^(search|balance)$")
    )

    app.add_handler(
        CallbackQueryHandler(
            admin_buttons,
            pattern="^(unlimited|credit|ban|unban|users)$"
        )
    )

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, check_number)
    )

    print("✅ ADMIN BOT RUNNING...")
    app.run_polling()


if __name__ == "__main__":
    main()