import os
import requests

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    MenuButtonWebApp,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)


# =========================
# SETTINGS
# =========================

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    "https://oejaiweclbxbwqikaznn.supabase.co",
)

SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

WEB_URL = "https://aliali2011kalf-alt.github.io/telegram-bot/"


# =========================
# SUPABASE
# =========================

def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def supabase_rpc(function_name, telegram_id):
    url = (
        f"{SUPABASE_URL}/rest/v1/rpc/"
        f"{function_name}"
    )

    response = requests.post(
        url,
        headers=supabase_headers(),
        json={
            "p_telegram_id": int(telegram_id)
        },
        timeout=20,
    )

    if not response.ok:
        raise RuntimeError(
            f"Supabase error "
            f"{response.status_code}: "
            f"{response.text}"
        )

    if not response.text:
        return None

    return response.json()


# =========================
# PROFILE
# =========================

def get_profile(telegram_id):
    url = (
        f"{SUPABASE_URL}/rest/v1/profiles"
        f"?telegram_id=eq.{int(telegram_id)}"
        f"&select=*"
    )

    response = requests.get(
        url,
        headers=supabase_headers(),
        timeout=20,
    )

    if not response.ok:
        raise RuntimeError(
            f"Profile error "
            f"{response.status_code}: "
            f"{response.text}"
        )

    data = response.json()

    if not data:
        return None

    return data[0]


# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if user is None:
        return

    telegram_id = user.id

    # Check profile
    try:
        profile = get_profile(telegram_id)

        if profile is None:
            await update.message.reply_text(
                "⚠️ لم يتم إنشاء حسابك في النظام بعد.\n\n"
                "افتح التطبيق من الزر بالأسفل ليتم إنشاء حسابك تلقائيًا."
            )

    except Exception as e:
        print("Profile check error:", e)

    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 فتح تطبيق ANF",
                web_app=WebAppInfo(
                    url=WEB_URL
                ),
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    await update.message.reply_text(
        "👋 أهلاً بك في منصة ANF\n\n"
        "🪙 عملة ANF\n"
        "⛓️ شبكة TON\n\n"
        "⛏️ التعدين:\n"
        "0.01 ANF كل ثانية\n\n"
        "⏱️ مدة دورة التعدين:\n"
        "24 ساعة\n\n"
        "🎁 ابدأ التعدين واجمع عملات ANF.\n\n"
        "👇 اضغط الزر لفتح التطبيق:",
        reply_markup=reply_markup,
    )


# =========================
# HELP
# =========================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.message.reply_text(
        "🚀 استخدم /start لفتح تطبيق ANF."
    )


# =========================
# MINING TEST COMMAND
# =========================

async def mining_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if user is None:
        return

    try:

        result = supabase_rpc(
            "anf_get_mining_status_by_telegram",
            user.id,
        )

        if isinstance(result, list) and result:
            result = result[0]

        if not isinstance(result, dict):
            result = {}

        balance = result.get(
            "balance",
            0,
        )

        claimable = result.get(
            "claimable",
            0,
        )

        active = result.get(
            "active",
            False,
        )

        rate = result.get(
            "rate_per_second",
            0.01,
        )

        if active:
            status = "🟢 التعدين يعمل"
        else:
            status = "🔴 التعدين متوقف"

        await update.message.reply_text(
            "⛏️ حالة التعدين\n\n"
            f"{status}\n\n"
            f"💰 الرصيد: {balance} ANF\n"
            f"🎁 القابل للمطالبة: {claimable} ANF\n"
            f"⚡ السرعة: {rate} ANF/ثانية"
        )

    except Exception as e:

        print("Mining status error:", e)

        await update.message.reply_text(
            "⚠️ حدث خطأ أثناء جلب حالة التعدين."
        )


# =========================
# MAIN
# =========================

def main():

    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN غير موجود في GitHub Secrets"
        )

    if not SUPABASE_KEY:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY غير موجود في GitHub Secrets"
        )

    print("==============================")
    print("ANF BOT STARTING")
    print("==============================")
    print("Mining rate: 0.01 ANF / second")
    print("Mining cycle: 24 hours")
    print("==============================")

    application = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "mining",
            mining_command,
        )
    )

    application.run_polling(
        drop_pending_updates=True
    )


# =========================
# RUN
# =========================

if __name__ == "__main__":
    main()
