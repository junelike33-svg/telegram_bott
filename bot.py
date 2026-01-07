from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from datetime import time
import pytz
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = None

TEXT = "любимая ты меня любишь? 🥹"
REMINDER_HOUR = 13
REMINDER_MINUTE = 50

love_counter = 0
pending_message_id = None

tz = pytz.timezone("Europe/Moscow")


async def send_message(context: ContextTypes.DEFAULT_TYPE):
    global pending_message_id

    keyboard = [[InlineKeyboardButton("люблю 🤍", callback_data="love")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    msg = await context.bot.send_message(
        chat_id=CHAT_ID,
        text=TEXT,
        reply_markup=reply_markup
    )

    pending_message_id = msg.message_id
    context.job_queue.run_once(remind_again, 600)


async def remind_again(context: ContextTypes.DEFAULT_TYPE):
    global pending_message_id
    if pending_message_id is not None:
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text="ты так и не ответила… 🥺 напишешь мне, что любишь?.. 💗"
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    CHAT_ID = update.effective_chat.id

    await update.message.reply_text(
        "Теперь я буду спрашивать тебя каждый день 🤍\n"
        "Если хочешь изменить время — напиши его так: 13:50"
    )


async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global REMINDER_HOUR, REMINDER_MINUTE

    try:
        t = update.message.text.strip()
        h, m = map(int, t.split(":"))
        REMINDER_HOUR = h
        REMINDER_MINUTE = m

        for job in context.job_queue.jobs():
            job.schedule_removal()

        context.job_queue.run_daily(
            send_message,
            time=time(hour=h, minute=m, tzinfo=tz)
        )

        await update.message.reply_text(f"Теперь я буду писать каждый день в {t} ❤️")
    except:
        await update.message.reply_text("Напиши время в формате ЧЧ:ММ 😊")


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global love_counter, pending_message_id

    query = update.callback_query
    await query.answer()

    love_counter += 1
    pending_message_id = None

    await query.edit_message_text(
        f"я тоже тебя люблю 🤍\n"
        f"ты сказала это уже {love_counter} раз(а) 🥹"
    )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_time))

    app.job_queue.run_daily(
        send_message,
        time=time(hour=REMINDER_HOUR, minute=REMINDER_MINUTE, tzinfo=tz)
    )

    app.run_polling()


if __name__ == "__main__":
    main()
