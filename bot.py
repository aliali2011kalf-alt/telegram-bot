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
# إعدادات ANF
# =========================

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    "https://oejaiweclbxbwqikaznn.supabase.co",
)

SUPABASE_KEY = (
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    or os.environ.get("SUPABASE_SECRET_KEY")
)

WEB_URL = "https://aliali2011kalf-alt.github.io/telegram-bot/"

BOT_USERNAME = "ANF_AIRDROP_bot"

REFERRAL_REWARD = 100
MINING_RATE = 0.0001


# =========================
# Supabase
# =========================

def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def supabase_rpc(function_name, payload):
    url = f"{SUPABASE_URL}/rest/v1/rpc/{function_name}"

    response = requests.post(
        url,
        headers=supabase_headers(),
        json=payload,
        timeout=20,
    )

    if not response.ok:
        raise RuntimeError(
            f"Supabase RPC error {response.status_code}: {response.text}"
        )

    if not response.text:
        return None

    return response.json()


def get_profile(telegram_id):
    url = (
        f"{SUPABASE_URL}/rest/v1/profiles"
        f"?telegram_id=eq.{int(telegram_id)}"
        f"&select=*"
        f"&limit=1"
    )

    response = requests.get(
        url,
        headers=supabase_headers(),
        timeout=20,
    )

    if not response.ok:
        raise RuntimeError(
            f"Profile error {response.status_code}: {response.text}"
        )

    data = response.json()

    if not data:
        return None

    return data[0]


# =========================
# إنشاء حساب المستخدم
# =========================

def create_profile(user):
    existing = get_profile(user.id)

    if existing:
        return existing

    # إنشاء مستخدم في Supabase Auth
    auth_url = f"{SUPABASE_URL}/auth/v1/admin/users"

    auth_payload = {
        "email": f"telegram_{user.id}@anf.local",
        "password": os.urandom(24).hex(),
        "email_confirm": True,
        "user_metadata": {
            "telegram_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
    }

    response = requests.post(
        auth_url,
        headers=supabase_headers(),
        json=auth_payload,
        timeout=20,
    )

    if not response.ok:
        # ربما تم إنشاء Auth user مسبقًا
        print("Auth create:", response.status_code, response.text)

    auth_data = {}

    try:
        auth_data = response.json()
    except Exception:
        pass

    auth_id = auth_data.get("id")

    if not auth_id:
        # إعادة البحث عن الحساب
        search_url = (
            f"{SUPABASE_URL}/auth/v1/admin/users"
            f"?page=1&per_page=1000"
        )

        search_response = requests.get(
            search_url,
            headers=supabase_headers(),
            timeout=20,
        )

        if search_response.ok:
            users = search_response.json().get("users", [])

            for auth_user in users:
                metadata = auth_user.get("user_metadata") or {}

                if str(metadata.get("telegram_id")) == str(user.id):
                    auth_id = auth_user.get("id")
                    break

    if not auth_id:
        raise RuntimeError("تعذر إنشاء حساب Supabase للمستخدم.")

    referral_code = str(user.id)

    profile_payload = {
        "id": auth_id,
        "telegram_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "referral_code": referral_code,
        "balance": 0,
        "is_active": True,
    }

    profile_url = f"{SUPABASE_URL}/rest/v1/profiles"

    profile_response = requests.post(
        profile_url,
        headers={
            **supabase_headers(),
            "Prefer": "return=representation",
        },
        json=profile_payload,
        timeout=20,
    )

    if not profile_response.ok:
        raise RuntimeError(
            f"Profile create error {profile_response.status_code}: "
            f"{profile_response.text}"
        )

    data = profile_response.json()

    if not data:
        raise RuntimeError("لم يتم إنشاء الملف الشخصي.")

    return data[0]


# =========================
# معالجة الإحالة
# =========================

def process_referral(profile, referral_code):
    if not referral_code:
        return None

    try:
        result = supabase_rpc(
            "claim_referral_reward",
            {
                "p_referred_id": profile["id"],
                "p_referral_code": str(referral_code),
            },
        )

        print("Referral result:", result)

        return result

    except Exception as e:
        print("Referral error:", e)
        return None


# =========================
# /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if user is None:
        return

    try:
        # إنشاء حساب المستخدم
        profile = create_profile(user)

        # قراءة كود الإحالة من:
        # /start REFERRAL_CODE
        referral_code = None

        if context.args:
            referral_code = context.args[0]

        # معالجة الإحالة
        if referral_code:
            process_referral(
                profile,
                referral_code,
            )

    except Exception as e:
        print("Start error:", e)

    keyboard = [[
        InlineKeyboardButton(
            "🚀 فتح تطبيق ANF",
            web_app=WebAppInfo(url=WEB_URL),
        )
    ]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 أهلاً بك في منصة ANF\n\n"
        "🪙 عملة ANF\n"
        "⛓️ شبكة TON\n\n"

        "⛏️ التعدين:\n"
        "0.0001 ANF كل ثانية\n\n"

        "⏱️ مدة دورة التعدين:\n"
        "24 ساعة\n\n"

        "🎁 مكافأة الإحالة:\n"
        "100 ANF لكل إحالة ناجحة\n\n"

        "👇 اضغط الزر لفتح التطبيق:",
        reply_markup=reply_markup,
    )


# =========================
# /help
# =========================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 أوامر منصة ANF\n\n"
        "/start - فتح منصة ANF\n"
        "/help - المساعدة\n"
        "/mining - معلومات التعدين\n\n"
        "🪙 ANF على شبكة TON"
    )


# =========================
# /mining
# =========================

async def mining(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "⛏️ تعدين ANF\n\n"
        "معدل التعدين:\n"
        "0.0001 ANF كل ثانية\n\n"
        "⏱️ مدة دورة التعدين:\n"
        "24 ساعة\n\n"
        "بعد انتهاء الدورة يمكنك بدء دورة جديدة من التطبيق."
    )


# =========================
# زر القائمة داخل Telegram
# =========================

async def setup_menu(application):

    await application.bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="🚀 ANF",
            web_app=WebAppInfo(url=WEB_URL),
        )
    )


# =========================
# تشغيل البوت
# =========================

def main():

    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN غير موجود في متغيرات البيئة."
        )

    if not SUPABASE_KEY:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY أو SUPABASE_SECRET_KEY غير موجود."
        )

    application = (
        Application.builder()
        .token(TOKEN)
        .post_init(setup_menu)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        CommandHandler("mining", mining)
    )

    print("ANF Bot is running...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
