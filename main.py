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

# === AUTO DELETE GROUPE ===
async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
        
    chat_id = str(update.effective_chat.id)
    data = load_data()
    
    # Commande /on dans groupe
    if update.message.text == "/on":
        if chat_id not in data["groups"]:
            data["groups"][chat_id] = {"enabled": True, "delay": 3}
        else:
            data["groups"][chat_id]["enabled"] = True
        save_data(data)
        await update.message.reply_text("Auto-suppression activée.")
        return

    # Commande /setdelay dans groupe
    if update.message.text and update.message.text.startswith("/setdelay"):
        parts = update.message.text.split()
        if len(parts) == 2 and parts[1].isdigit():
            delay = int(parts[1])
            if chat_id not in data["groups"]:
                data["groups"][chat_id] = {"enabled": True, "delay": delay}
            else:
                data["groups"][chat_id]["delay"] = delay
                if "enabled" not in data["groups"][chat_id]:
                    data["groups"][chat_id]["enabled"] = True
            save_data(data)
            await update.message.reply_text(f"Délai défini à {delay} sec.")
            return

    # Suppression auto groupe
    conf = data["groups"].get(chat_id, {})
    if conf.get("enabled", False):
        delay = conf.get("delay", 3)
        print(f"[GROUPE] Message reçu dans {chat_id} - Suppression dans {delay}s")
        await asyncio.sleep(delay)
        try:
            await update.message.delete()
            print("[GROUPE] Message supprimé.")
        except Exception as e:
            print("[GROUPE] Erreur suppression :", e)

# === AUTO DELETE CANAL ===
async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.channel_post.chat_id)
    text = update.channel_post.text or ""
    data = load_data()

    print(f"[CANAL] Message détecté dans canal {chat_id} : {text[:30]}...")

    # Commande /on dans canal
    if text == "/on":
        if chat_id not in data["groups"]:
            data["groups"][chat_id] = {"enabled": True, "delay": 3}
        else:
            data["groups"][chat_id]["enabled"] = True
        save_data(data)
        await context.bot.send_message(chat_id=chat_id, text="Auto-suppression activée.")
        return

    # Commande /setdelay dans canal
    if text.startswith("/setdelay"):
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            delay = int(parts[1])
            if chat_id not in data["groups"]:
                data["groups"][chat_id] = {"enabled": True, "delay": delay}
            else:
                data["groups"][chat_id]["delay"] = delay
                if "enabled" not in data["groups"][chat_id]:
                    data["groups"][chat_id]["enabled"] = True
            save_data(data)
            await context.bot.send_message(chat_id=chat_id, text=f"Délai défini à {delay} sec.")

    # Suppression auto canal
    conf = data["groups"].get(chat_id, {})
    if conf.get("enabled", False):
        delay = conf.get("delay", 3)  # Délai par défaut de 3 secondes
        print(f"[CANAL] Suppression programmée dans {delay}s")
        await asyncio.sleep(delay)
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=update.channel_post.message_id)
            print("[CANAL] Message supprimé.")
        except Exception as e:
            print("[CANAL] Erreur suppression :", e)

# === ADMIN ===
def is_admin(user_id):
    return user_id == 5116530698

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try:
        username = context.args[0].lstrip('@')
        user = await context.bot.get_chat(username)
        data = load_data()
        if user.id not in data["admins"]:
            data["admins"].append(user.id)
            save_data(data)
            await update.message.reply_text(f"{username} ajouté aux admins.")
    except:
        await update.message.reply_text("Erreur. Utilise /addadmin @username")

async def ban_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try:
        username = context.args[0].lstrip('@')
        user = await context.bot.get_chat(username)
        data = load_data()
        if user.id in data["admins"]:
            data["admins"].remove(user.id)
            save_data(data)
            await update.message.reply_text(f"{username} retiré des admins.")
    except:
        await update.message.reply_text("Erreur. Utilise /banadmin @username")

async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    text = "Admins :\n" + "\n".join([str(a) for a in data["admins"]])
    await update.message.reply_text(text)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    msg = " ".join(context.args)
    data = load_data()
    count = 0
    for user_id in data["users"]:
        try:
            await context.bot.send_message(user_id, msg)
            count += 1
        except:
            pass
    await update.message.reply_text(f"Message envoyé à {count} utilisateurs.")

async def broadcast_pub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    msg = " ".join(context.args)
    data = load_data()
    count = 0
    for chat_id in data["groups"]:
        try:
            await context.bot.send_message(chat_id, msg)
            count += 1
        except:
            pass
    await update.message.reply_text(f"Message envoyé dans {count} groupes/canaux.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(
        f"Groupes/Canaux : {len(data['groups'])}\n"
        f"Utilisateurs : {len(data['users'])}\n"
        f"Admins : {len(data['admins'])}"
    )

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
try:
    app.run_polling(drop_pending_updates=True, allowed_updates=["message", "channel_post"])
except Exception as e:
    print(f"Erreur: {e}")
finally:
    # Ensure clean shutdown
    print("Bot arrêté.")
    app.stop()
