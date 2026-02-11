import os
import json
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# ================= CONFIG =================

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = -5105711109  # ใส่เลขกลุ่มธุรการของคุณ

# ================= GOOGLE SHEET =================

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

sheet = client.open("ระบบแจ้งซ่อมสำนักงาน").sheet1

# ================= HELPER =================

def generate_ticket():
    records = sheet.get_all_records()
    count = len(records) + 1
    year = datetime.now().year
    return f"MT-{year}-{str(count).zfill(4)}"

# ================= COMMAND START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "วิธีแจ้งซ่อม:\n\n"
        "พิมพ์แบบนี้ครั้งเดียวจบ\n\n"
        "แจ้ง\n"
        "แผนก: ...\n"
        "ทรัพย์สิน: ...\n"
        "อาการ: ...\n"
        "ความเร่งด่วน: ด่วน/ปกติ"
    )

# ================= MAIN HANDLER =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text.startswith("แจ้ง"):
        return

    try:
        lines = text.split("\n")

        location = lines[1].replace("แผนก:", "").strip()
        asset = lines[2].replace("ทรัพย์สิน:", "").strip()
        issue = lines[3].replace("อาการ:", "").strip()
        priority = lines[4].replace("ความเร่งด่วน:", "").strip()

        ticket_id = generate_ticket()
        now = datetime.now()

        # ===== บันทึกลง Sheet =====
        sheet.append_row([
            ticket_id,
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M"),
            location,
            asset,
            issue,
            priority,
            "รอดำเนินการ",
            update.message.from_user.full_name
        ])

        # ===== ตอบกลับผู้แจ้ง =====
        await update.message.reply_text(
            f"✅ บันทึกเรียบร้อย\n📌 Ticket: {ticket_id}"
        )

        # ===== แจ้งเตือนเข้ากลุ่ม =====
        alert_text = (
            f"🚨 มีงานแจ้งซ่อมใหม่\n\n"
            f"📌 Ticket: {ticket_id}\n"
            f"🏢 แผนก: {location}\n"
            f"🛠 อุปกรณ์: {asset}\n"
            f"📝 อาการ: {issue}\n"
            f"⚠️ ความเร่งด่วน: {priority}\n"
            f"👤 ผู้แจ้ง: {update.message.from_user.full_name}"
        )

        if priority == "ด่วน":
            alert_text = "❗❗ งานด่วน ❗❗\n\n" + alert_text

        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=alert_text
        )

    except:
        await update.message.reply_text(
            "❌ รูปแบบไม่ถูกต้อง\n\n"
            "กรุณาพิมพ์แบบนี้:\n\n"
            "แจ้ง\n"
            "แผนก: ...\n"
            "ทรัพย์สิน: ...\n"
            "อาการ: ...\n"
            "ความเร่งด่วน: ด่วน/ปกติ"
        )

# ================= RUN APP =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
