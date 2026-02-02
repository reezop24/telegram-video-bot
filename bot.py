from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import json

TOKEN = "8571888421:AAH8WDtaarglaEIlEwjlvg87mAKnfCMNKwM"
VIDEO_CHANNEL_ID = -1003809328917  # tukar ikut channel kau

VIDEO_MAP = {
    "basic_001": 5,
    "basic_002": 6,
    "basic_003": 7,
    "basic_004": 8,
    "basic_005": 9,
    "basic_006": 10,
    "basic_007": 11,
    "basic_008": 12,
    "basic_009": 13,
    "basic_010": 14,
    "basic_011": 15,
    "basic_012": 16,
    "basic_013": 17,
    "medium_001": 18,
    "medium_002": 19,
    "medium_003": 20,
    "advance_001": 21,
    "advance_002": 22
}

FREE_BASIC_LIMIT = 13  # topik 1–13 free

VIDEO_LIST = {
    "basic": list(range(1, 30)),     # basic_001 → basic_029 (contoh)
    "medium": list(range(1, 20)),
    "advance": list(range(1, 15))
}

USER_STATE = {}



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🎓 Premium Education Videos"],
        ["📝 Request"],
        ["💳 Langganan"]
    ]

    await update.message.reply_text(
        "Selamat datang 👋\nSila pilih menu:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


async def premium_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🎓 Premium Education Videos":
        keyboard = [
            ["Basic"],
            ["Medium"],
            ["Advance"],
            ["⬅ Back"]
        ]
        await update.message.reply_text(
            "Pilih tahap pembelajaran:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    elif text in ["Basic", "Medium", "Advance"]:
        level = text.lower()  # basic / medium / advance

        keyboard = [[
            KeyboardButton(
                text=f"📂 Buka Galeri {text}",
                web_app=WebAppInfo(
                    url=f"https://telegram-miniapp-v45s.vercel.app?level={level}"
                )
            )
        ], ["⬅ Back"]]

        await update.message.reply_text(
            f"Galeri {text} dibuka:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    elif text == "⬅ Back":
        await start(update, context)


def can_access(level, index, is_subscriber=False):
    if is_subscriber:
        return True

    if level == "basic":
        return index < FREE_BASIC_LIMIT  # index 0–12 = topik 1–13

    # medium & advance
    return False


async def webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    data = json.loads(update.message.web_app_data.data)

    level = data["level"]          # basic / medium / advance
    video_id = data["video_id"]    # contoh basic_001
    index = int(video_id.split("_")[-1]) - 1  # basic_014 -> index 13

    is_subscriber = False  # nanti kita upgrade

    # 🔒 ACCESS CHECK
    if not can_access(level, index, is_subscriber):
        await update.message.reply_text(
            "❌ Sila buat langganan untuk menonton topik ini."
        )
        return

    # check video wujud
    if video_id not in VIDEO_MAP:
        await update.message.reply_text("❌ Video belum tersedia.")
        return

    USER_STATE[user_id] = {
        "level": level,
        "index": index
    }

    await send_video(context, chat_id, user_id)



from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def send_video(context, chat_id, user_id):
    state = USER_STATE[user_id]
    level = state["level"]
    index = state["index"]

    video_key = f"{level}_{str(index+1).zfill(3)}"

    # safety check
    if video_key not in VIDEO_MAP:
        await context.bot.send_message(chat_id, "❌ Video belum tersedia.")
        return

    keyboard = []

    nav_row = []
    if index > 0:
        nav_row.append(InlineKeyboardButton("◀️ Previous", callback_data="prev"))
    if index < len(VIDEO_LIST[level]) - 1:
        nav_row.append(InlineKeyboardButton("▶️ Next", callback_data="next"))

    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([
        InlineKeyboardButton("🎓 Level Selection", callback_data="level"),
        InlineKeyboardButton("🏠 Home", callback_data="home")
    ])

    sent = await context.bot.copy_message(
    chat_id=chat_id,
    from_chat_id=VIDEO_CHANNEL_ID,
    message_id=VIDEO_MAP[video_key],
    reply_markup=InlineKeyboardMarkup(keyboard),
    protect_content=True
)


    # delete old video
    if "message_id" in state:
        try:
            await context.bot.delete_message(chat_id, state["message_id"])
        except:
            pass

    state["message_id"] = sent.message_id

from telegram.ext import CallbackQueryHandler

async def navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    chat_id = query.message.chat_id

    if user_id not in USER_STATE:
        return

    state = USER_STATE[user_id]

    if query.data == "next":
        state["index"] += 1
        await send_video(context, chat_id, user_id)

    elif query.data == "prev":
        state["index"] -= 1
        await send_video(context, chat_id, user_id)

    elif query.data == "level":
        try:
            await context.bot.delete_message(chat_id, state["message_id"])
        except:
            pass

        del USER_STATE[user_id]

        keyboard = [
            ["Basic"],
            ["Medium"],
            ["Advance"],
            ["⬅ Back"]
        ]

        await context.bot.send_message(
            chat_id=chat_id,
            text="Pilih tahap pembelajaran:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    elif query.data == "home":
        try:
            await context.bot.delete_message(chat_id, state["message_id"])
        except:
            pass

        del USER_STATE[user_id]

        keyboard = [
            ["🎓 Premium Education Videos"],
            ["📝 Request"],
            ["💳 Langganan"]
        ]

        await context.bot.send_message(
            chat_id=chat_id,
            text="Selamat datang 👋\nSila pilih menu:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )


app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, premium_menu))
app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data))
app.add_handler(CallbackQueryHandler(navigation))


app.run_polling()
