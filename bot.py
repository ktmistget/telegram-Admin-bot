import os
import json
import gspread
from datetime import datetime, time
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================== GOOGLE SHEET SETUP ==================

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

sheet = client.open("ระบบแจ้งซ่อมสำนักงาน").sheet1

# ================== TELEGRAM SETUP ==================

TOKEN = os.environ.get("BOT_TOKEN")

# ================== HANDLERS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "สวัสดีค่ะ 😊\nพิมพ์คำว่า 'แจ้งซ่อม' เพื่อแจ้งปัญหา"
    )

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["step"] = 1
    await update.message.reply_text("กรุณาระบุแผนก / สถานที่")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step", 0)

    if step == 1:
        context.user_data["location"] = update.message.text
        context.user_data["step"] = 2
        await update.message.reply_text("ทรัพย์สินหรืออุปกรณ์ที่เสีย?")

    elif step == 2:
        context.user_data["asset"] = update.message.text
        context.user_data["step"] = 3
        await update.message.reply_text("อาการเสียเป็นอย่างไร?")

    elif step == 3:
        context.user_data["issue"] = update.message.text
        context.user_data["step"] = 4
        await update.message.reply_text("ความเร่งด่วน (ด่วน / ปกติ)")

    elif step == 4:
        priority = update.message.text
        now = datetime.now()

        sheet.append_row([
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M"),
            context.user_data["location"],
            context.user_data["asset"],
            context.user_data["issue"],
            priority,
            "รอดำเนินการ",
            update.message.from_user.full_name
        ])

        await update.message.reply_text(
            "📩 รับแจ้งเรียบร้อย\nบันทึกเข้าระบบแล้ว"
        )

        context.user_data.clear()

# ================== DAILY REPORT ==================

CHAT_ID = 123456789  # 🔴 ใส่ Chat ID จริงของคุณตรงนี้

async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    records = sheet.get_all_records()

    today = datetime.now().strftime("%Y-%m-%d")
    today_records = [r for r in records if r["วันที่"] == today]

    total = len(today_records)
    urgent = len([r for r in today_records if r["ความเร่งด่วน"] == "ด่วน"])
    pending = len([r for r in today_records if r["สถานะ"] == "รอดำเนินการ"])
    done = len([r for r in today_records if r["สถานะ"] == "เสร็จแล้ว"])

    message = f"""📊 สรุปแจ้งซ่อมประจำวัน

ทั้งหมด: {total}
ด่วน: {urgent}
รอดำเนินการ: {pending}
เสร็จแล้ว: {done}
"""

    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=message
    )

# ================== APP START ==================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("แจ้งซ่อม"), report))
app.add_handler(MessageHandler(filters.TEXT, handle_message))

# ⏰ ส่งรายงานทุกวัน 17:00 เวลาไทย
# Render ใช้ UTC → 17:00 ไทย = 10:00 UTC
app.job_queue.run_daily(daily_report, time(hour=10, minute=0))

app.run_polling()
