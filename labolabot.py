#!/usr/bin/env python3
“””
🤖 LABOLABOT — Bot Telegram boutique
“””

import json
import logging
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
Application,
CommandHandler,
CallbackQueryHandler,
MessageHandler,
ConversationHandler,
filters,
ContextTypes,
)

# ══════════════════════════════════════════════

# ⚙️  CONFIGURATION

# ══════════════════════════════════════════════

TOKEN        = “8705132613:AAEzxbzFTNoLwwOBWKdEtDRs1bS7Tvs8PPk”
ADMIN_ID     = 6023169098
ADMIN_USER   = “@labomoula25”
PRODUCTS_FILE = “products.json”

# ══════════════════════════════════════════════

# États

# ══════════════════════════════════════════════

ASK_ADDRESS       = 1
ADMIN_SELECT_PROD = 2
ADMIN_EDIT_FIELD  = 3
ADMIN_EDIT_VALUE  = 4

logging.basicConfig(
format=”%(asctime)s - %(levelname)s - %(message)s”, level=logging.INFO
)
logger = logging.getLogger(**name**)

# ══════════════════════════════════════════════

# 🗂️  PRODUITS

# ══════════════════════════════════════════════

def load_products():
with open(PRODUCTS_FILE, “r”, encoding=“utf-8”) as f:
return json.load(f)

def save_products(products):
with open(PRODUCTS_FILE, “w”, encoding=“utf-8”) as f:
json.dump(products, f, ensure_ascii=False, indent=2)

# ══════════════════════════════════════════════

# 🏠  MENU PRINCIPAL

# ══════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
context.user_data.clear()
keyboard = [
[InlineKeyboardButton(“🛍️ Voir le menu”, callback_data=“menu”)],
[InlineKeyboardButton(“🛒 Mon panier”, callback_data=“panier”),
InlineKeyboardButton(“⏰ Horaires”, callback_data=“horaires”)],
[InlineKeyboardButton(“📞 Contact”, callback_data=“contact”)],
]
await update.message.reply_text(
“👋 Bienvenue sur *Labolabot* !\n\nCommande tes produits facilement 🎉”,
parse_mode=“Markdown”,
reply_markup=InlineKeyboardMarkup(keyboard),
)

async def accueil_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
keyboard = [
[InlineKeyboardButton(“🛍️ Voir le menu”, callback_data=“menu”)],
[InlineKeyboardButton(“🛒 Mon panier”, callback_data=“panier”),
InlineKeyboardButton(“⏰ Horaires”, callback_data=“horaires”)],
[InlineKeyboardButton(“📞 Contact”, callback_data=“contact”)],
]
await query.edit_message_text(
“🏠 *Menu principal*”,
parse_mode=“Markdown”,
reply_markup=InlineKeyboardMarkup(keyboard),
)

# ══════════════════════════════════════════════

# 🛍️  CATALOGUE

# ══════════════════════════════════════════════

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
products = load_products()
keyboard = []
for p in products:
keyboard.append([InlineKeyboardButton(p[“nom”], callback_data=f”produit_{p[‘id’]}”)])
keyboard.append([InlineKeyboardButton(“🏠 Retour”, callback_data=“accueil”)])
await query.edit_message_text(
“🛍️ *Notre catalogue* :\n\nChoisis un produit :”,
parse_mode=“Markdown”,
reply_markup=InlineKeyboardMarkup(keyboard),
)

async def show_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
prod_id = query.data.replace(“produit_”, “”)
products = load_products()
p = next((x for x in products if x[“id”] == prod_id), None)
if not p:
await query.edit_message_text(“❌ Produit introuvable.”)
return

```
keyboard = []
row = []
for i, opt in enumerate(p["prix_options"]):
    row.append(InlineKeyboardButton(
        f"{opt['label']} — {opt['prix']}€",
        callback_data=f"add_{p['id']}_{i}"
    ))
    if len(row) == 2:
        keyboard.append(row)
        row = []
if row:
    keyboard.append(row)

keyboard.append([InlineKeyboardButton("🎬 Voir la vidéo", callback_data=f"video_{p['id']}")])
keyboard.append([InlineKeyboardButton("🛒 Mon panier", callback_data="panier"),
                 InlineKeyboardButton("◀️ Retour", callback_data="menu")])

desc = p.get("description") or "Aucune description."
caption = f"*{p['nom']}*\n\n📝 {desc}\n\n💰 Choisis ton grammage :"

if p.get("photo"):
    try:
        await query.message.reply_photo(
            photo=p["photo"],
            caption=caption,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        await query.delete_message()
        return
    except Exception:
        pass

await query.edit_message_text(
    caption, parse_mode="Markdown",
    reply_markup=InlineKeyboardMarkup(keyboard)
)
```

async def show_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
prod_id = query.data.replace(“video_”, “”)
products = load_products()
p = next((x for x in products if x[“id”] == prod_id), None)
if p and p.get(“video”):
await query.message.reply_video(video=p[“video”], caption=f”🎬 {p[‘nom’]}”)
else:
await query.answer(“📹 Vidéo non disponible.”, show_alert=True)

# ══════════════════════════════════════════════

# 🛒  PANIER

# ══════════════════════════════════════════════

def get_cart(context):
if “cart” not in context.user_data:
context.user_data[“cart”] = []
return context.user_data[“cart”]

def cart_total(cart):
return sum(item[“prix”] for item in cart)

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
parts = query.data.split(”_”)
prod_id = parts[1]
opt_idx = int(parts[2])
products = load_products()
p = next((x for x in products if x[“id”] == prod_id), None)
if not p:
await query.answer(“❌ Produit introuvable.”, show_alert=True)
return
opt = p[“prix_options”][opt_idx]
cart = get_cart(context)
cart.append({
“nom”: p[“nom”],
“label”: opt[“label”],
“prix”: opt[“prix”],
})
await query.answer(f”✅ {p[‘nom’]} {opt[‘label’]} ajouté !”, show_alert=True)

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
cart = get_cart(context)
if not cart:
await query.edit_message_text(
“🛒 Ton panier est vide.”,
reply_markup=InlineKeyboardMarkup([
[InlineKeyboardButton(“🛍️ Voir le menu”, callback_data=“menu”)],
[InlineKeyboardButton(“🏠 Accueil”, callback_data=“accueil”)],
])
)
return

```
lines = ["🛒 *Ton panier :*\n"]
for i, item in enumerate(cart):
    lines.append(f"{i+1}. {item['nom']} {item['label']} — {item['prix']}€")
total = cart_total(cart)
lines.append(f"\n💰 *Total : {total}€*")

keyboard = [
    [InlineKeyboardButton("🚀 Commander", callback_data="commander")],
    [InlineKeyboardButton("🗑️ Vider le panier", callback_data="vider_panier")],
    [InlineKeyboardButton("🛍️ Continuer", callback_data="menu")],
]
await query.edit_message_text(
    "\n".join(lines), parse_mode="Markdown",
    reply_markup=InlineKeyboardMarkup(keyboard)
)
```

async def clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
context.user_data[“cart”] = []
await query.edit_message_text(
“🗑️ Panier vidé !”,
reply_markup=InlineKeyboardMarkup([
[InlineKeyboardButton(“🛍️ Voir le menu”, callback_data=“menu”)],
])
)

# ══════════════════════════════════════════════

# 📦  COMMANDE

# ══════════════════════════════════════════════

async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
cart = get_cart(context)
if not cart:
await query.answer(“🛒 Ton panier est vide !”, show_alert=True)
return
await query.edit_message_text(
“📦 *Finaliser la commande*\n\nEnvoie-moi ton *adresse de livraison complète* :”,
parse_mode=“Markdown”,
)
return ASK_ADDRESS

async def receive_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
address = update.message.text
user = update.effective_user
cart = get_cart(context)
total = cart_total(cart)
prenom = user.first_name or “N/A”
pseudo = f”@{user.username}” if user.username else “Pas de pseudo”

```
lines = [f"• {item['nom']} {item['label']} — {item['prix']}€" for item in cart]

admin_msg = (
    f"🛒 *NOUVELLE COMMANDE*\n\n"
    f"👤 Prénom : {prenom}\n"
    f"📱 Pseudo : {pseudo}\n"
    f"📍 Adresse : {address}\n\n"
    + "\n".join(lines)
    + f"\n\n💰 *Total : {total}€*"
)

msg_encode = urllib.parse.quote(
    f"COMMANDE\nPrénom: {prenom}\nPseudo: {pseudo}\nAdresse: {address}\n"
    + "\n".join(lines)
    + f"\nTOTAL: {total}€"
)
tme_link = f"https://t.me/labomoula25?text={msg_encode}"

try:
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
    admin_notified = True
except Exception:
    admin_notified = False

summary = (
    f"📋 *Récapitulatif :*\n\n"
    + "\n".join(lines)
    + f"\n\n💰 *Total : {total}€*\n"
    f"📍 *Adresse :* {address}\n\n"
)

if admin_notified:
    client_text = (
        summary
        + "✅ *Commande transmise !*\n\n"
        f"On te contacte très vite via {ADMIN_USER} 👍\n\n"
        f"Ou envoie directement ta commande :\n👉 [Cliquer ici]({tme_link})"
    )
else:
    client_text = (
        summary
        + f"💰 *Total à régler : {total}€*\n\n"
        f"👉 [Envoyer ma commande directement]({tme_link})\n\n"
        f"Ou contacte : {ADMIN_USER}"
    )

await update.message.reply_text(
    client_text, parse_mode="Markdown",
    disable_web_page_preview=True,
    reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Retour accueil", callback_data="accueil")]
    ])
)
context.user_data["cart"] = []
return ConversationHandler.END
```

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(“❌ Commande annulée.”)
return ConversationHandler.END

# ══════════════════════════════════════════════

# ℹ️  INFOS

# ══════════════════════════════════════════════

async def show_horaires(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
await query.edit_message_text(
“⏰ *Horaires d’ouverture*\n\n🕙 10h00 – 00h00\n📅 7 jours / 7”,
parse_mode=“Markdown”,
reply_markup=InlineKeyboardMarkup([
[InlineKeyboardButton(“🏠 Retour”, callback_data=“accueil”)]
])
)

async def show_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
await query.edit_message_text(
f”📞 *Contact*\n\n👤 {ADMIN_USER}\n\n⏰ 10h00 – 00h00 — 7j/7”,
parse_mode=“Markdown”,
reply_markup=InlineKeyboardMarkup([
[InlineKeyboardButton(“💬 Contacter”, url=“https://t.me/labomoula25”)],
[InlineKeyboardButton(“🏠 Retour”, callback_data=“accueil”)],
])
)

# ══════════════════════════════════════════════

# 🔧  ADMIN

# ══════════════════════════════════════════════

def is_admin(update: Update) -> bool:
return update.effective_user.id == ADMIN_ID

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not is_admin(update):
await update.message.reply_text(“⛔ Accès refusé.”)
return ConversationHandler.END
products = load_products()
keyboard = [[InlineKeyboardButton(p[“nom”], callback_data=f”edit_{p[‘id’]}”)]
for p in products]
keyboard.append([InlineKeyboardButton(“❌ Annuler”, callback_data=“cancel_admin”)])
await update.message.reply_text(
“🔧 *Panel Admin*\nChoisis le produit à modifier :”,
parse_mode=“Markdown”,
reply_markup=InlineKeyboardMarkup(keyboard),
)
return ADMIN_SELECT_PROD

async def admin_select_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
if query.data == “cancel_admin”:
await query.edit_message_text(“✅ Admin annulé.”)
return ConversationHandler.END
prod_id = query.data.replace(“edit_”, “”)
context.user_data[“edit_prod_id”] = prod_id
products = load_products()
p = next((x for x in products if x[“id”] == prod_id), None)
keyboard = [
[InlineKeyboardButton(“📝 Nom”, callback_data=“field_nom”)],
[InlineKeyboardButton(“📄 Description”, callback_data=“field_description”)],
[InlineKeyboardButton(“🖼️ Photo (file_id)”, callback_data=“field_photo”)],
[InlineKeyboardButton(“🎬 Vidéo (file_id)”, callback_data=“field_video”)],
[InlineKeyboardButton(“❌ Annuler”, callback_data=“cancel_admin”)],
]
await query.edit_message_text(
f”✏️ Modifier *{p[‘nom’]}*\nQue veux-tu changer ?”,
parse_mode=“Markdown”,
reply_markup=InlineKeyboardMarkup(keyboard),
)
return ADMIN_EDIT_FIELD

async def admin_choose_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
if query.data == “cancel_admin”:
await query.edit_message_text(“✅ Admin annulé.”)
return ConversationHandler.END
field = query.data.replace(“field_”, “”)
context.user_data[“edit_field”] = field
labels = {“nom”: “Nom”, “description”: “Description”, “photo”: “File ID photo”, “video”: “File ID vidéo”}
await query.edit_message_text(
f”✏️ Envoie la nouvelle valeur pour *{labels.get(field, field)}* :”,
parse_mode=“Markdown”,
)
return ADMIN_EDIT_VALUE

async def admin_set_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
value = update.message.text
prod_id = context.user_data.get(“edit_prod_id”)
field = context.user_data.get(“edit_field”)
products = load_products()
for p in products:
if p[“id”] == prod_id:
p[field] = value
break
save_products(products)
await update.message.reply_text(f”✅ *{field}* mis à jour !”, parse_mode=“Markdown”)
return ConversationHandler.END

# ══════════════════════════════════════════════

# 🚀  LANCEMENT

# ══════════════════════════════════════════════

def main():
app = Application.builder().token(TOKEN).build()

```
order_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_order, pattern="^commander$")],
    states={ASK_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_address)]},
    fallbacks=[CommandHandler("annuler", cancel_order)],
)

admin_conv = ConversationHandler(
    entry_points=[CommandHandler("admin", admin_panel)],
    states={
        ADMIN_SELECT_PROD: [CallbackQueryHandler(admin_select_product)],
        ADMIN_EDIT_FIELD:  [CallbackQueryHandler(admin_choose_field)],
        ADMIN_EDIT_VALUE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_set_value)],
    },
    fallbacks=[CommandHandler("annuler", cancel_order)],
)

app.add_handler(CommandHandler("start", start))
app.add_handler(order_conv)
app.add_handler(admin_conv)
app.add_handler(CallbackQueryHandler(accueil_callback, pattern="^accueil$"))
app.add_handler(CallbackQueryHandler(show_menu, pattern="^menu$"))
app.add_handler(CallbackQueryHandler(show_product, pattern="^produit_"))
app.add_handler(CallbackQueryHandler(show_video, pattern="^video_"))
app.add_handler(CallbackQueryHandler(add_to_cart, pattern="^add_"))
app.add_handler(CallbackQueryHandler(show_cart, pattern="^panier$"))
app.add_handler(CallbackQueryHandler(clear_cart, pattern="^vider_panier$"))
app.add_handler(CallbackQueryHandler(show_horaires, pattern="^horaires$"))
app.add_handler(CallbackQueryHandler(show_contact, pattern="^contact$"))

print("🤖 Labolabot démarré !")
app.run_polling()
```

if **name** == “**main**”:
main()
