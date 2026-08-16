import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import TELEGRAM_TOKEN
from api_football import FootballAPI
from analyzer import analyze_live_match, simple_value_hint

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
api = FootballAPI()

live_cache = {
    "data": [],
    "updated_at": 0
}
CACHE_TTL = 90


async def get_cached_live():
    import time
    now = time.time()
    if now - live_cache["updated_at"] > CACHE_TTL or not live_cache["data"]:
        logger.info("Updating live fixtures cache...")
        live_cache["data"] = await api.get_live_fixtures()
        live_cache["updated_at"] = now
    return live_cache["data"]


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "👋 Привет! Я бот для лайв-анализа футбольных матчей.\n\n"
        "Я использую данные API-Football по всем лигам мира.\n\n"
        "<b>Команды:</b>\n"
        "/live — текущие live-матчи\n"
        "/status — сколько запросов осталось сегодня\n"
        "/help — помощь\n\n"
        "Пока бот работает в режиме «по запросу» (чтобы экономить бесплатный лимит)."
    )
    await message.answer(text)


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "<b>Как пользоваться:</b>\n\n"
        "1. Нажми /live — получишь список текущих матчей\n"
        "2. Нажми на матч — получишь подробный анализ\n\n"
        "Бот показывает:\n"
        "• Текущий счёт и минуту\n"
        "• Базовый статистический анализ\n"
        "• Подсказки по тоталам и BTTS\n\n"
        "⚠️ Это не финансовые рекомендации. Используй на свой страх и риск.\n"
        "Бесплатный тариф API — 100 запросов в сутки. Используй осознанно."
    )
    await message.answer(text)


@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    try:
        status = await api.get_status()
        sub = status.get("subscription", {})
        req = status.get("requests", {})

        text = (
            f"📊 <b>Статус API-Football</b>\n\n"
            f"План: <b>{sub.get('plan', '—')}</b>\n"
            f"Активен: {'✅' if sub.get('active') else '❌'}\n"
            f"Запросов сегодня: <b>{req.get('current', 0)}</b> / {req.get('limit_day', 100)}\n"
            f"Осталось: <b>{req.get('limit_day', 100) - req.get('current', 0)}</b>"
        )
        await message.answer(text)
    except Exception as e:
        await message.answer(f"Ошибка при получении статуса: {e}")


@dp.message(Command("live"))
async def cmd_live(message: types.Message):
    await message.answer("🔄 Загружаю live-матчи...")

    try:
        fixtures = await get_cached_live()
    except Exception as e:
        await message.answer(f"❌ Ошибка API: {e}")
        return

    if not fixtures:
        await message.answer("Сейчас нет live-матчей 😴")
        return

    priority_leagues = {
        39: 1, 140: 2, 135: 3, 78: 4, 61: 5, 2: 6, 3: 7, 848: 8,
    }

    def sort_key(f):
        lid = f.get("league", {}).get("id", 9999)
        return priority_leagues.get(lid, 100)

    fixtures_sorted = sorted(fixtures, key=sort_key)[:25]

    builder = InlineKeyboardBuilder()
    for f in fixtures_sorted:
        home = f["teams"]["home"]["name"]
        away = f["teams"]["away"]["name"]
        score = f"{f['goals']['home'] or 0}:{f['goals']['away'] or 0}"
