import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

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
        await update.message.reply_text(
            "📩 รับแจ้งเรียบร้อย\nแผนกธุรการจะดำเนินการต่อไปค่ะ"
        )
        context.user_data.clear()

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("แจ้งซ่อม"), report))
app.add_handler(MessageHandler(filters.TEXT, handle_message))
app.run_polling()
