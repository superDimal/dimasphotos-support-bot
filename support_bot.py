import os, threading, pymongo
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Support Bot is Online"
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- 2. DATABASE (Shares your main database) ---
# EDIT THIS: Paste your main MongoDB link here
MONGO_URI = "mongodb+srv://dimaspicbase:dimasphotosdatabase27@cluster0.uhbjpus.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = pymongo.MongoClient(MONGO_URI)
db = client["family_bot_db"]
users_col = db["users"] 

# --- 3. CONFIGURATION ---
TOKEN = '8350603733:AAER0jxLBezxZ7k4JguZn4eOTp2-EXYVNx0' # EDIT THIS
DIMA_USER_ID = 8545617249 # EDIT THIS (Paste the number from @userinfobot)
ADMIN_GROUP_ID = -1003912990952 

async def start(update, context):
    uid = str(update.effective_user.id)
    if not users_col.find_one({"uid": uid}):
        users_col.insert_one({"uid": uid, "family": "Guest", "admin_topic": None})
    await update.message.reply_text("Hi! You'll receive updates here. To talk to Dima, just type your message!")

async def broadcast(update, context):
    if update.effective_user.id != DIMA_USER_ID: return
    if not context.args:
        await update.message.reply_text("Usage: /update [message]")
        return
    text = "📢 **NEW UPDATE:**\n\n" + " ".join(context.args)
    count = 0
    for user in users_col.find({}):
        try:
            await context.bot.send_message(chat_id=int(user["uid"]), text=text, parse_mode="Markdown")
            count += 1
        except: continue
    await update.message.reply_text(f"✅ Sent to {count} users!")

async def handle_msg(update, context):
    user, uid, chat_id, msg = update.effective_user, str(update.effective_user.id), update.effective_chat.id, update.effective_message
    if chat_id == ADMIN_GROUP_ID:
        target = users_col.find_one({"admin_topic": msg.message_thread_id})
        if target and msg.text: await context.bot.send_message(int(target["uid"]), msg.text)
        return
    if msg.chat.type == "private":
        user_doc = users_col.find_one({"uid": uid})
        if not user_doc or not user_doc.get("admin_topic"):
            new_t = await context.bot.create_forum_topic(ADMIN_GROUP_ID, f"Chat: {user.full_name}")
            users_col.update_one({"uid": uid}, {"$set": {"admin_topic": new_t.message_thread_id}}, upsert=True)
            tid = new_t.message_thread_id
        else: tid = user_doc["admin_topic"]
        await context.bot.forward_message(ADMIN_GROUP_ID, uid, msg.message_id, message_thread_id=tid)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("update", broadcast))
    app_bot.add_handler(MessageHandler(filters.ALL, handle_msg))
    app_bot.run_polling(drop_pending_updates=True)
