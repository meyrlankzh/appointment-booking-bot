import asyncio
import os
import sqlite3
from datetime import date, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DB = "bookings.db"
SERVICES = ["Haircut", "Consultation", "Checkup"]
SLOTS = ["10:00", "11:00", "12:00", "14:00", "15:00", "16:00"]

dp = Dispatcher()


def db():
    con = sqlite3.connect(DB)
    con.execute(
        """CREATE TABLE IF NOT EXISTS bookings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, service TEXT, day TEXT, slot TEXT,
            UNIQUE(day, slot))"""
    )
    return con


def kb(rows):
    return InlineKeyboardMarkup(inline_keyboard=rows)


@dp.message(CommandStart())
@dp.message(Command("book"))
async def book(m: Message):
    rows = [[InlineKeyboardButton(text=s, callback_data=f"s|{i}")]
            for i, s in enumerate(SERVICES)]
    await m.answer("Welcome! Choose a service:", reply_markup=kb(rows))


@dp.callback_query(F.data.startswith("s|"))
async def pick_service(c: CallbackQuery):
    si = c.data.split("|")[1]
    days = [date.today() + timedelta(days=i) for i in range(1, 6)]
    rows = [[InlineKeyboardButton(text=d.strftime("%a %d %b"),
                                  callback_data=f"d|{si}|{d.isoformat()}")]
            for d in days]
    await c.message.edit_text("Choose a day:", reply_markup=kb(rows))
    await c.answer()


@dp.callback_query(F.data.startswith("d|"))
async def pick_day(c: CallbackQuery):
    _, si, day = c.data.split("|")
    with db() as con:
        taken = {r[0] for r in con.execute(
            "SELECT slot FROM bookings WHERE day=?", (day,))}
    free = [s for s in SLOTS if s not in taken]
    if not free:
        await c.answer("No free slots on this day.", show_alert=True)
        return
    rows = [[InlineKeyboardButton(text=s, callback_data=f"t|{si}|{day}|{s}")]
            for s in free]
    await c.message.edit_text(f"Free slots for {day}:", reply_markup=kb(rows))
    await c.answer()


@dp.callback_query(F.data.startswith("t|"))
async def confirm(c: CallbackQuery):
    _, si, day, slot = c.data.split("|")
    service = SERVICES[int(si)]
    try:
        with db() as con:
            con.execute(
                "INSERT INTO bookings(user_id, service, day, slot) VALUES (?,?,?,?)",
                (c.from_user.id, service, day, slot))
    except sqlite3.IntegrityError:
        await c.answer("Sorry, this slot was just taken.", show_alert=True)
        return
    await c.message.edit_text(f"Booked: {service}, {day} at {slot}")
    if ADMIN_ID:
        await c.bot.send_message(
            ADMIN_ID, f"New booking: {service}, {day} {slot} (user {c.from_user.id})")
    await c.answer()


@dp.message(Command("my"))
async def my_bookings(m: Message):
    with db() as con:
        rows = con.execute(
            "SELECT id, service, day, slot FROM bookings "
            "WHERE user_id=? ORDER BY day, slot", (m.from_user.id,)).fetchall()
    if not rows:
        await m.answer("You have no bookings.")
        return
    for bid, service, day, slot in rows:
        await m.answer(f"{service} - {day} {slot}", reply_markup=kb(
            [[InlineKeyboardButton(text="Cancel", callback_data=f"c|{bid}")]]))


@dp.callback_query(F.data.startswith("c|"))
async def cancel(c: CallbackQuery):
    bid = int(c.data.split("|")[1])
    with db() as con:
        con.execute("DELETE FROM bookings WHERE id=? AND user_id=?",
                    (bid, c.from_user.id))
    await c.message.edit_text("Booking cancelled.")
    await c.answer()


async def main():
    bot = Bot(TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
