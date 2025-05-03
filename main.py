import asyncio
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# === CONFIG ===
TOKEN = "7334376683:AAEhwjysajszFcaMjLdyNgsy4pw1_HLcbSs"
DATA_FILE = "data.json"

# === BASE DE DONNÉES ===
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"admins": [5116530698], "groups": {}, "users": []}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# === FONCTION POUR GARDER L'AUTO-SUPPRESSION ACTIVE ===
async def keep_auto_delete_alive():
    while True:
        data = load_data()
        for chat_id in data["groups"]:
            data["groups"][chat_id]["enabled"] = True  # ✅ Garde l'auto-suppression active
        save_data(data)
        print("[AUTO-SUPPRESSION] Vérification et réactivation automatique.")
        await asyncio.sleep(1800)  # ✅ Vérifie toutes les 30 min

# === START ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data(data)

    keyboard = [[InlineKeyboardButton("Rejoindre le canal", url="https://t.me/sineur_x_bot")]]
    text = (
        "Bienvenue !\nCe bot supprime automatiquement les messages dans les groupes et canaux.\n"
        "Commandes disponibles pour tous :\n"
        "/on - Activer l’auto-suppression\n"
        "/off - Désactiver l’auto-suppression\n"
        "/setdelay [secondes] - Définir le délai de suppression"
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# === COMMANDES PUBLIQUES ===
async def cmd_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    data = load_data()
    if chat_id not in data["groups"]:
        data["groups"][chat_id] = {"enabled": True, "delay": 3}
    else:
        data["groups"][chat_id]["enabled"] = True
    save_data(data)
    await update.message.reply_text("Auto-suppression activée.")

async def cmd_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    data = load_data()
    data["groups"].setdefault(chat_id, {})["enabled"] = False
    save_data(data)
    await update.message.reply_text("Auto-suppression désactivée.")

async def cmd_setdelay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    data = load_data()
    try:
        delay = int(context.args[0])
        data["groups"].setdefault(chat_id, {})["delay"] = delay
        save_data(data)
        await update.message.reply_text(f"Délai défini à {delay} sec.")
    except:
        await update.message.reply_text("Usage : /setdelay 10")

# === AUTO DELETE CANAL ===
async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.channel_post.chat_id)
    text = update.channel_post.text or ""
    data = load_data()

    print(f"[CANAL] Message détecté dans canal {chat_id} : {text[:30]}...")

    # Enregistrement du canal automatiquement
    if chat_id not in data["groups"]:
        data["groups"][chat_id] = {"enabled": False, "delay": 3}
        save_data(data)

    conf = data["groups"].get(chat_id, {})
    if conf.get("enabled", False):
        delay = conf.get("delay", 3)
        print(f"[CANAL] Suppression programmée dans {delay}s")
        await asyncio.sleep(delay)
        
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=update.channel_post.message_id)
            print("[CANAL] Message supprimé.")
        except Exception as e:
            print("[CANAL] Erreur suppression :", e)

# === MAIN ===
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("on", cmd_on))
app.add_handler(CommandHandler("off", cmd_off))
app.add_handler(CommandHandler("setdelay", cmd_setdelay))

app.add_handler(CommandHandler("addadmin", add_admin))
app.add_handler(CommandHandler("banadmin", ban_admin))
app.add_handler(CommandHandler("admins", list_admins))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("broadcast_pub", broadcast_pub))
app.add_handler(CommandHandler("stats", stats))

app.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, auto_delete))
app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, handle_channel_post))

print("Bot lancé...")
async def main():
    asyncio.create_task(keep_auto_delete_alive())  # ✅ Active la réactivation toutes les 30 min
    await app.run_polling(drop_pending_updates=True, allowed_updates=["message", "channel_post"])

try:
    asyncio.run(main())
except Exception as e:
    print(f"Erreur: {e}")
finally:
    print("Bot arrêté.")