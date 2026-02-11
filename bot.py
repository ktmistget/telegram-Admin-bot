import os
import json
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters
)

# ================== CONFIG ==================

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = -5105711109  # กลุ่มธุรการของคุณ

# ================== GOOGLE SHEET SETUP ==================

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

sheet = client.open("ระบบแจ้งซ่อมสำนักงาน").sheet1

# ================== GENERATE TICKET ==================

def generate_ticket():
    records = sheet.get_all_records()
    count = len(records) + 1
    year = datetime.now().year
    return f"MT-{year}-{str(count).zfill(4)}"

# ================== MAIN HANDLER ==================

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

        # ===== บันทึกลง Google Sheet =====
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
        await update.message.
