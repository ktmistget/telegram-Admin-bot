import os
import json
import gspread
import pytz
from datetime import datetime
from collections import Counter
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# ================= CONFIG =================

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = -5105711109  # กลุ่มธุรการ

THAI_TZ = pytz.timezone("Asia/Bangkok")

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

def thai_now():
    return datetime.now(THAI_TZ)

def generate_ticket():
    records = sheet.get_all_records()
    count = len(records) + 1
    year = thai_now().year
    return f"MT-{year}-{str(count).zfill(4)}"

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "แจ้งงานแบบนี้:\n\n"
        "แจ้ง\n"
        "แผนก/ฝ่าย: ...\n"
        "แจ้งเรื่อง: ...\n"
        "ความเร่งด่วน: ด่วน/ปกติ"
    )

# ================= CREATE TICKET =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text.startswith("แจ้ง"):
        return

    try:
        lines = text.split("\n")

        department = lines[1].replace("แผนก/ฝ่าย:", "").strip()
        subject = lines[2].replace("แจ้งเรื่อง:", "").strip()
        priority = lines[3].replace("ความเร่งด่วน:", "").strip()

        ticket_id = generate_ticket()
        now = thai_now()

        sheet.append_row([
            ticket_id,
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M"),
            department,
            subject,
            priority,
            "รอดำเนินการ",
            update.message.from_user.full_name,
            ""  # เวลาปิด
        ])

        await update.message.reply_text(
            f"✅ บันทึกเรียบร้อย\n📌 Ticket: {ticket_id}"
        )

        alert_text = (
            f"🚨 งานใหม่\n\n"
            f"📌 {ticket_id}\n"
            f"🏢 แผนก/ฝ่าย: {department}\n"
            f"📝 เรื่อง: {subject}\n"
            f"⚠️ ความเร่งด่วน: {priority}\n"
            f"🕒 เวลา: {now.strftime('%H:%M')}"
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
            "แจ้ง\n"
            "แผนก/ฝ่าย: ...\n"
            "แจ้งเรื่อง: ...\n"
            "ความเร่งด่วน: ด่วน/ปกติ"
        )

# ================= CLOSE TICKET =================

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ticket_id = context.args[0]
        records = sheet.get_all_records()

        for i, row in enumerate(records):
            if row["Ticket"] == ticket_id:
                sheet.update_cell(i + 2, 7, "เสร็จแล้ว")  # สถานะ
                sheet.update_cell(i + 2, 9, thai_now().strftime("%Y-%m-%d %H:%M"))
                break
        else:
            await update.message.reply_text("❌ ไม่พบ Ticket")
            return

        await update.message.reply_text(f"✅ ปิดงาน {ticket_id} แล้ว")

        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"🔒 {ticket_id} ถูกปิดโดย {update.message.from_user.full_name}"
        )

    except:
        await update.message.reply_text("ใช้คำสั่งแบบนี้:\n/done MT-2026-0001")

# ================= DASHBOARD =================

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    records = sheet.get_all_records()

    total = len(records)
    pending = len([r for r in records if r["สถานะ"] == "รอดำเนินการ"])
    done_count = len([r for r in records if r["สถานะ"] == "เสร็จแล้ว"])
    urgent = len([r for r in records if r["ความเร่งด่วน"] == "ด่วน"])

    department_counter = Counter([r["แผนก/ฝ่าย"] for r in records])

    dept_text = ""
    for dept, count in department_counter.items():
        dept_text += f"{dept}: {count} งาน\n"

    message = (
        f"📊 Dashboard ผู้บริหาร\n\n"
        f"งานทั้งหมด: {total}\n"
        f"รอดำเนินการ: {pending}\n"
        f"เสร็จแล้ว: {done_count}\n"
        f"งานด่วน: {urgent}\n\n"
        f"📌 แยกตามแผนก/ฝ่าย\n{dept_text}"
    )

    await update.message.reply_text(message)

# ================= RUN =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("done", done))
app.add_handler(CommandHandler("dashboard", dashboard))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
