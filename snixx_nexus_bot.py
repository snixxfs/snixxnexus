import logging
import json
import asyncio
import pytz  # Fix timezone error in APScheduler
from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import openai

# ✅ Set OpenAI API key globally
openai.api_key = "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"

# ✅ Your bot token (Don't lose this)
API_TOKEN = "7550325074:AAEsVPjH5tJleAxj9D_Cph9XLhEG1NXkgjc"
YOUR_TELEGRAM_ID = 1848440092  # Replace with your Telegram ID

# ✅ Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()  # ✅ Use Router() for Aiogram 3

# ✅ Fix Event Loop issue for APScheduler
scheduler = AsyncIOScheduler(timezone=pytz.UTC)  # ✅ Use pytz.UTC instead of "UTC"

# ✅ XP System
XP_POINTS = {"workout": 10, "study": 15, "skincare": 5, "money_tracking": 5}

# ✅ Load user data
DATA_FILE = "user_data.json"
try:
    with open(DATA_FILE, "r") as f:
        user_data = json.load(f)
except FileNotFoundError:
    user_data = {"xp": 0, "streak": 0, "tasks": {}}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(user_data, f, indent=4)

# ✅ Fix Keyboard Markup
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 My Stats"), KeyboardButton(text="✅ Log Task")],
        [KeyboardButton(text="🔄 Reset Streak"), KeyboardButton(text="💡 Get Advice")],
    ],
    resize_keyboard=True
)

# ✅ /start Command
@router.message(Command("start"))
async def start_cmd(message: types.Message):
    if message.from_user.id != YOUR_TELEGRAM_ID:
        return await message.answer("🚫 This bot is private!")
    await message.answer("🔥 Snixx Nexus Bot Activated!", reply_markup=main_keyboard)

# ✅ My Stats
@router.message(lambda message: message.text == "📊 My Stats")
async def stats_cmd(message: types.Message):
    stats_text = (
        f"📈 **Your Stats**\n"
        f"🔥 XP: {user_data['xp']}\n"
        f"🔥 Streak: {user_data['streak']} days\n"
        f"💪 Workouts: {user_data['tasks'].get('workout', 0)}\n"
        f"📖 Study Sessions: {user_data['tasks'].get('study', 0)}\n"
        f"💸 Money Tracked: {user_data['tasks'].get('money_tracking', 0)}\n"
        f"🧴 Skincare Days: {user_data['tasks'].get('skincare', 0)}"
    )
    await message.answer(stats_text)

# ✅ Log Task Menu
@router.message(lambda message: message.text == "✅ Log Task")
async def log_task_menu(message: types.Message):
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💪 Workout"), KeyboardButton(text="📖 Study")],
            [KeyboardButton(text="💸 Money Tracking"), KeyboardButton(text="🧴 Skincare")],
        ],
        resize_keyboard=True
    )
    await message.answer("Select the task you completed:", reply_markup=markup)

# ✅ Log Selected Task
@router.message(lambda message: message.text in ["💪 Workout", "📖 Study", "💸 Money Tracking", "🧴 Skincare"])
async def log_selected_task(message: types.Message):
    task_map = {
        "💪 Workout": "workout",
        "📖 Study": "study",
        "💸 Money Tracking": "money_tracking",
        "🧴 Skincare": "skincare",
    }
    user_data["xp"] += XP_POINTS[task_map[message.text]]
    user_data["streak"] += 1
    user_data["tasks"][task_map[message.text]] = user_data["tasks"].get(task_map[message.text], 0) + 1
    save_data()
    await message.answer(f"✅ Logged {message.text}! Keep up the streak!")

# ✅ Reset Streak
@router.message(lambda message: message.text == "🔄 Reset Streak")
async def reset_streak(message: types.Message):
    user_data["streak"] = 0
    save_data()
    await message.answer("🚨 Streak reset! Time to grind again.")

# ✅ AI-Based Advice (Fixed API Call)
@router.message(lambda message: message.text == "💡 Get Advice")
async def get_advice(message: types.Message):
    prompt = f"My XP: {user_data['xp']}, Streak: {user_data['streak']}. Give me a motivational tip."
    
    response = await asyncio.to_thread(openai.ChatCompletion.create,
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    advice = response['choices'][0]['message']['content']
    await message.answer(f"💡 **Your Personalized Advice:**\n{advice}")

# ✅ Voice Input Logging
@router.message(lambda message: message.voice)
async def handle_voice(message: types.Message):
    user_data["xp"] += 5
    save_data()
    await message.answer("🎙️ Voice logged! Keep tracking your progress.")

# ✅ Auto Reminders
async def send_reminders():
    await bot.send_message(YOUR_TELEGRAM_ID, "🔥 Reminder: Workout Time! 💪")
    await bot.send_message(YOUR_TELEGRAM_ID, "📖 Reminder: Study Session! 🚀")
    await bot.send_message(YOUR_TELEGRAM_ID, "🧴 Reminder: Skincare & Sleep Mode 🛏")

# ✅ Schedule reminders
scheduler.add_job(send_reminders, "cron", hour=6, minute=30)  # Morning
scheduler.add_job(send_reminders, "cron", hour=17, minute=30)  # Workout
scheduler.add_job(send_reminders, "cron", hour=21, minute=0)  # Study
scheduler.add_job(send_reminders, "cron", hour=22, minute=30)  # Night routine

# ✅ Run Bot (Fixed Aiogram 3)
async def main():
    dp.include_router(router)  # ✅ Use router instead of dp
    await dp.start_polling(bot, skip_updates=True)
    
    # ✅ Now Start APScheduler inside the running event loop!
    scheduler.start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())  
