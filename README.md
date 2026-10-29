# Appointment Booking Bot

A Telegram bot for booking appointments, built with aiogram 3 and SQLite.

## Features
- Choose a service, day and time with inline buttons
- Double-booking is prevented at database level
- Users can view and cancel their bookings (/my)
- Admin gets a notification for every new booking

## Setup
```bash
git clone https://github.com/meyrlankzh/appointment-booking-bot.git
cd appointment-booking-bot
pip install -r requirements.txt
cp .env.example .env   # then fill in BOT_TOKEN and ADMIN_ID
python bot.py
```

## Commands
- `/start`, `/book` - start a new booking
- `/my` - list and cancel your bookings

## Tech
Python, aiogram 3, SQLite
