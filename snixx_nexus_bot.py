import logging
import json
import asyncio
import os
import pytz  # Fixes timezone error in APScheduler

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import openai

# Load environment variables (for local development)
load_dotenv()

# Get API keys from environment variables
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
YOUR_TELEGRAM_ID = int(os.getenv("YOUR_TELEGRAM_ID", "0"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()  
scheduler = AsyncIOScheduler(timezone=pytz.utc)  

# XP System
XP_POINTS = {"workout": 10, "study": 15, "skincare": 5, "money_tracking": 5}

# User data storage (Stored in a local JSON file)
DATA_FILE = "user_data.json"

# Load existing data or create a new one
try:
    with open(DATA_FILE, "r") as f:
        user_data = json.load(f)
except FileNotFoundError:
    user_data = {"xp": 0, "streak": 0, "tasks": {}}

# Function to save data
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(user_data, f, indent=4)

# Keyboard Markup
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 My Stats"), KeyboardButton(text="✅ Log Task")],
        [KeyboardButton(text="🔄 Reset Streak"), KeyboardButton(text="💡 Get Advice")],
    ],
    resize_keyboard=True
)

# Function to log task completion
async def log_task(task):
    user_data["xp"] += XP_POINTS[task]
    user_data["streak"] += 1
    user_data["tasks"][task] = user_data["tasks"].get(task, 0) + 1
    save_data()

# /start Command
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    if message.from_user.id != YOUR_TELEGRAM_ID:
        return await message.answer("🚫 This bot is private!")
    await message.answer("🔥 Snixx Nexus Bot Activated! Track habits, level up & stay disciplined.", reply_markup=main_keyboard)

# 📊 My Stats
@dp.message(lambda message: message.text == "📊 My Stats")
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

# ✅ Log Task
@dp.message(lambda message: message.text == "✅ Log Task")
async def log_task_menu(message: types.Message):
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💪 Workout"), KeyboardButton(text="📖 Study")],
            [KeyboardButton(text="💸 Money Tracking"), KeyboardButton(text="🧴 Skincare")],
        ],
        resize_keyboard=True
    )
    await message.answer("Select the task you completed:", reply_markup=markup)

# Task Selection Handler
@dp.message(lambda message: message.text in ["💪 Workout", "📖 Study", "💸 Money Tracking", "🧴 Skincare"])
async def log_selected_task(message: types.Message):
    task_map = {
        "💪 Workout": "workout",
        "📖 Study": "study",
        "💸 Money Tracking": "money_tracking",
        "🧴 Skincare": "skincare",
    }
    await log_task(task_map[message.text])
    await message.answer(f"✅ Logged {message.text}! Keep up the streak!")

# 🔄 Reset Streak
@dp.message(lambda message: message.text == "🔄 Reset Streak")
async def reset_streak(message: types.Message):
    user_data["streak"] = 0
    save_data()
    await message.answer("🚨 Streak reset! Time to grind again.")

# 💡 AI-Based Advice
@dp.message(lambda message: message.text == "💡 Get Advice")
async def get_advice(message: types.Message):
    prompt = f"My XP: {user_data['xp']}, Streak: {user_data['streak']}. Give me a motivational tip."

    response = await asyncio.to_thread(openai.ChatCompletion.create,
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        api_key=OPENAI_API_KEY
    )

    advice = response['choices'][0]['message']['content']
    await message.answer(f"💡 **Your Personalized Advice:**\n{advice}")

# 🔔 Auto Reminders
async def send_reminders():
    await bot.send_message(YOUR_TELEGRAM_ID, "🔥 Reminder: Workout Time! 💪")
    await bot.send_message(YOUR_TELEGRAM_ID, "📖 Reminder: Study Session! 🚀")
    await bot.send_message(YOUR_TELEGRAM_ID, "🧴 Reminder: Skincare & Sleep Mode 🛏")

# 📅 Schedule reminders
scheduler.add_job(send_reminders, "cron", hour=6, minute=30)  # Morning
scheduler.add_job(send_reminders, "cron", hour=17, minute=30)  # Workout
scheduler.add_job(send_reminders, "cron", hour=21, minute=0)   # Study
scheduler.add_job(send_reminders, "cron", hour=22, minute=30)  # Night routine

# 🚀 Run Bot with proper event loop
async def main():
    scheduler.start()
    dp.include_router(dp)
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
