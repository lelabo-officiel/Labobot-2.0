import json
import logging
import os
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, filters, ContextTypes

TOKEN = "8705132613:AAF7fD0dLzfkdO5OMf1F0WxKgoBsT8WU2c4"
ADMIN_ID = 6023169098
ADMIN_USER = "@labomoula25"
PRODUCTS_FILE = "products.json"

ASK_ADDRESS = 1
ADMIN_SELECT_PROD = 2
ADMIN_EDIT_FIELD = 3
ADMIN_EDIT_VALUE = 4

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

PRODUCT_EMOJIS = {
    "coke": "❄️",
    "heroine_pure": "💉",
    "heroine_coupe": "💉",
    "hashish": "🟡",
    "weed_cali": "🌿",
}

def get_emoji(prod_id):
    return PRODUCT_EMOJIS.get(prod_id, "🌿")

def load_products():
    logger.info("Chemin: " + os.getcwd())
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

def menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍️  Voir le catalogue", callback_data="menu")],
        [InlineKeyboardButton("🛒  Mon panier", callback_data="panier"), InlineKeyboardButton("🕐  Horaires", callback_data="horaires")],
        [InlineKeyboardButton("💬  Nous contacter", callback_data="contact")],
    ])

async def send_accueil(message, context, edit=False):
    text = (
        "🏪 *LE LABO — Boutique Privée*\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        "Bienvenue ✨\n\n"
        "❄️  Cocaïne colombienne pure\n"
        "💉  Héroïne hollandaise\n"
        "🌿  Weed californienne\n"
        "🟡  Hashish premium\n\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "⚡️ Livraison rapide & discrète\n"
        "🔒 Service 7j/7 — 10h à minuit"
    )
    if edit:
        await message.edit_text(text, parse_mode="Markdown", reply_markup=menu_keyboard())
    else:
        await message.reply_text(text, parse_mode="Markdown", reply_markup=menu_keyboard())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await send_accueil(update.message, context)

async def accueil_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await send_accueil(query.message, context, edit=True)
    except Exception:
        try:
            await query.message.delete()
        except Exception:
            pass
        await send_accueil(query.message, context, edit=False)

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    products = load_products()
    keyboard = []
    for p in products:
        emoji = get_emoji(p["id"])
        keyboard.append([InlineKeyboardButton(emoji + "  " + p["nom"], callback_data="produit|" + p["id"])])
    keyboard.append([InlineKeyboardButton("🏠  Accueil", callback_data="accueil")])
    await query.edit_message_text(
        "🛍️ *Catalogue — Le Labo*\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        "Choisis ton produit 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    prod_id = query.data.split("|")[1]
    products = load_products()
    p = next((x for x in products if x["id"] == prod_id), None)
    if not p:
        await query.edit_message_text("Produit introuvable.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Retour", callback_data="menu")]]))
        return
    emoji = get_emoji(prod_id)
    keyboard = []
    for i, opt in enumerate(p["prix_options"]):
        keyboard.append([InlineKeyboardButton(emoji + "  " + opt["label"] + " — " + str(opt["prix"]) + "€  →  Ajouter au panier", callback_data="add|" + p["id"] + "|" + str(i))])
    keyboard.append([InlineKeyboardButton("🎬  Voir la vidéo", callback_data="video|" + p["id"])])
    keyboard.append([InlineKeyboardButton("🔙  Retour catalogue", callback_data="menu")])
    desc = p.get("description") or "Aucune description."
    caption = (
        emoji + " *" + p["nom"].upper() + "*\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        + desc + "\n\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "👇 *Clique sur ton grammage pour l'ajouter au panier :*"
    )
    if p.get("photo"):
        try:
            await query.message.reply_photo(photo=p["photo"], caption=caption, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
            await query.delete_message()
            return
        except Exception as e:
            logger.error("Erreur photo: " + str(e))
    await query.edit_message_text(caption, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    prod_id = query.data.split("|")[1]
    products = load_products()
    p = next((x for x in products if x["id"] == prod_id), None)
    if p and p.get("video"):
        emoji = get_emoji(prod_id)
        await query.message.reply_video(video=p["video"], caption=emoji + " *" + p["nom"] + "*", parse_mode="Markdown")
    else:
        await query.answer("Vidéo non disponible.", show_alert=True)

def get_cart(context):
    if "cart" not in context.user_data:
        context.user_data["cart"] = []
    return context.user_data["cart"]

def cart_total(cart):
    return sum(item["prix"] for item in cart)

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    prod_id = parts[1]
    opt_idx = int(parts[2])
    products = load_products()
    p = next((x for x in products if x["id"] == prod_id), None)
    if not p:
        await query.answer("Produit introuvable.", show_alert=True)
        return
    opt = p["prix_options"][opt_idx]
    cart = get_cart(context)
    cart.append({"nom": p["nom"], "label": opt["label"], "prix": opt["prix"], "prod_id": prod_id})
    emoji = get_emoji(prod_id)
    total = cart_total(cart)
    keyboard = [
        [InlineKeyboardButton("✅  Commander maintenant", callback_data="commander_direct")],
        [InlineKeyboardButton("🛍️  Continuer mes achats", callback_data="menu")],
        [InlineKeyboardButton("🛒  Voir mon panier", callback_data="panier")],
    ]
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass
    await query.message.reply_text(
        "✅ *Ajouté au panier !*\n\n"
        + emoji + " " + p["nom"] + " — *" + opt["label"] + "* — " + str(opt["prix"]) + "€\n\n"
        "🛒 Total panier : *" + str(total) + "€*\n\n"
        "Que veux-tu faire ?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def commander_direct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cart = get_cart(context)
    if not cart:
        await query.answer("Ton panier est vide !", show_alert=True)
        return
    await query.edit_message_text(
        "📦 *Finaliser la commande*\n\n"
        "Envoie-moi ton *adresse de livraison complète* :\n\n"
        "_Ex: 12 rue de la Paix, Paris 75001_",
        parse_mode="Markdown"
    )
    return ASK_ADDRESS

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cart = get_cart(context)
    if not cart:
        await query.edit_message_text(
            "🛒 *Ton panier est vide*\n\n_Ajoute des produits pour commencer !_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛍️  Voir le catalogue", callback_data="menu")],
                [InlineKeyboardButton("🏠  Accueil", callback_data="accueil")]
            ])
        )
        return
    lines = ["🛒 *Ton panier :*\n", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"]
    for item in cart:
        emoji = get_emoji(item.get("prod_id", ""))
        lines.append(emoji + " " + item["nom"] + " " + item["label"] + " — *" + str(item["prix"]) + "€*")
    total = cart_total(cart)
    lines.append("▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬")
    lines.append("💰 *Total : " + str(total) + "€*")
    keyboard = [
        [InlineKeyboardButton("✅  Commander maintenant", callback_data="commander")],
        [InlineKeyboardButton("🗑  Vider le panier", callback_data="vider_panier")],
        [InlineKeyboardButton("🛍️  Continuer", callback_data="menu"), InlineKeyboardButton("🏠  Accueil", callback_data="accueil")]
    ]
    await query.edit_message_text("\n".join(lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["cart"] = []
    await query.edit_message_text(
        "🗑 Panier vidé !",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛍️  Voir le catalogue", callback_data="menu")],
            [InlineKeyboardButton("🏠  Accueil", callback_data="accueil")]
        ])
    )

async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cart = get_cart(context)
    if not cart:
        await query.answer("Ton panier est vide !", show_alert=True)
        return
    await query.edit_message_text(
        "📦 *Finaliser la commande*\n\n"
        "Envoie-moi ton *adresse de livraison complète* :\n\n"
        "_Ex: 12 rue de la Paix, Paris 75001_",
        parse_mode="Markdown"
    )
    return ASK_ADDRESS

async def receive_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text
    user = update.effective_user
    cart = get_cart(context)
    total = cart_total(cart)
    prenom = user.first_name or "N/A"
    pseudo = "@" + user.username if user.username else "Pas de pseudo"
    lines = ["— " + item["nom"] + " " + item["label"] + " : " + str(item["prix"]) + "€" for item in cart]
    admin_msg = (
        "🔔 *NOUVELLE COMMANDE*\n\n"
        "👤 " + prenom + "\n"
        "📱 " + pseudo + "\n"
        "📍 " + address + "\n\n"
        + "\n".join(lines) + "\n\n"
        "💰 *Total : " + str(total) + "€*"
    )
    msg_encode = urllib.parse.quote("COMMANDE\nPrenom: " + prenom + "\nPseudo: " + pseudo + "\nAdresse: " + address + "\n" + "\n".join(lines) + "\nTOTAL: " + str(total) + "EUR")
    tme_link = "https://t.me/labomoula25?text=" + msg_encode
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
        admin_notified = True
    except Exception:
        admin_notified = False
    summary = (
        "✅ *Commande confirmée !*\n\n"
        + "\n".join(lines) + "\n\n"
        "💰 *Total : " + str(total) + "€*\n"
        "📍 " + address + "\n\n"
    )
    if admin_notified:
        client_text = summary + "On te contacte très rapidement via " + ADMIN_USER + " 🚀\n\n[📩 Confirmer ma commande](" + tme_link + ")"
    else:
        client_text = summary + "[📩 Envoyer ma commande](" + tme_link + ")\n\nContacte : " + ADMIN_USER
    await update.message.reply_text(
        client_text, parse_mode="Markdown", disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠  Retour à l'accueil", callback_data="accueil")]])
    )
    context.user_data["cart"] = []
    return ConversationHandler.END

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Commande annulée.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Accueil", callback_data="accueil")]]))
    return ConversationHandler.END

async def show_horaires(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🕐 *Horaires — Le Labo*\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        "🟢 Ouvert tous les jours\n"
        "⏰ 10h00 — 00h00\n\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "_Disponible 7j/7_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙  Retour", callback_data="accueil")]])
    )

async def show_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "💬 *Contact — Le Labo*\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        "👤 " + ADMIN_USER + "\n"
        "⏰ 10h — 00h • 7j/7\n\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "_On te répond rapidement_ ⚡️",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💬  Envoyer un message", url="https://t.me/labomoula25")],
            [InlineKeyboardButton("🔙  Retour", callback_data="accueil")]
        ])
    )

async def fallback_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_accueil(update.message, context)

async def cmd_fileid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Envoie-moi ta photo ou vidéo !")

async def get_photo_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    photo = update.message.photo[-1]
    await update.message.reply_text("file_id photo :\n`" + photo.file_id + "`", parse_mode="Markdown")

async def get_video_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    video = update.message.video
    await update.message.reply_text("file_id video :\n`" + video.file_id + "`", parse_mode="Markdown")

def is_admin(update: Update) -> bool:
    return update.effective_user.id == ADMIN_ID

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("Acces refuse.")
        return ConversationHandler.END
    products = load_products()
    keyboard = [[InlineKeyboardButton(p["nom"], callback_data="edit|" + p["id"])] for p in products]
    keyboard.append([InlineKeyboardButton("Annuler", callback_data="cancel_admin")])
    await update.message.reply_text("*Panel Admin*\nChoisis le produit :", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADMIN_SELECT_PROD

async def admin_select_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel_admin":
        await query.edit_message_text("Annulé.")
        return ConversationHandler.END
    prod_id = query.data.split("|")[1]
    context.user_data["edit_prod_id"] = prod_id
    products = load_products()
    p = next((x for x in products if x["id"] == prod_id), None)
    keyboard = [
        [InlineKeyboardButton("Nom", callback_data="field_nom")],
        [InlineKeyboardButton("Description", callback_data="field_description")],
        [InlineKeyboardButton("Photo (file_id)", callback_data="field_photo")],
        [InlineKeyboardButton("Video (file_id)", callback_data="field_video")],
        [InlineKeyboardButton("Annuler", callback_data="cancel_admin")],
    ]
    await query.edit_message_text("Modifier *" + p["nom"] + "* :", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADMIN_EDIT_FIELD

async def admin_choose_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel_admin":
        await query.edit_message_text("Annulé.")
        return ConversationHandler.END
    field = query.data.replace("field_", "")
    context.user_data["edit_field"] = field
    labels = {"nom": "Nom", "description": "Description", "photo": "File ID photo", "video": "File ID video"}
    await query.edit_message_text("Envoie la nouvelle valeur pour *" + labels.get(field, field) + "* :", parse_mode="Markdown")
    return ADMIN_EDIT_VALUE

async def admin_set_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text
    prod_id = context.user_data.get("edit_prod_id")
    field = context.user_data.get("edit_field")
    products = load_products()
    for p in products:
        if p["id"] == prod_id:
            p[field] = value
            break
    save_products(products)
    await update.message.reply_text("✅ *" + field + "* mis à jour !", parse_mode="Markdown")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    order_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_order, pattern="^commander$"),
            CallbackQueryHandler(commander_direct, pattern="^commander_direct$"),
        ],
        states={ASK_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_address)]},
        fallbacks=[CommandHandler("annuler", cancel_order)],
    )

    admin_conv = ConversationHandler(
        entry_points=[CommandHandler("admin", admin_panel)],
        states={
            ADMIN_SELECT_PROD: [CallbackQueryHandler(admin_select_product, pattern="^edit")],
            ADMIN_EDIT_FIELD: [CallbackQueryHandler(admin_choose_field)],
            ADMIN_EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_set_value)],
        },
        fallbacks=[CommandHandler("annuler", cancel_order)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("fileid", cmd_fileid))
    app.add_handler(MessageHandler(filters.PHOTO, get_photo_id))
    app.add_handler(MessageHandler(filters.VIDEO, get_video_id))
    app.add_handler(order_conv)
    app.add_handler(admin_conv)
    app.add_handler(CallbackQueryHandler(accueil_callback, pattern="^accueil$"))
    app.add_handler(CallbackQueryHandler(show_menu, pattern="^menu$"))
    app.add_handler(CallbackQueryHandler(show_product, pattern="^produit\\|"))
    app.add_handler(CallbackQueryHandler(show_video, pattern="^video\\|"))
    app.add_handler(CallbackQueryHandler(add_to_cart, pattern="^add\\|"))
    app.add_handler(CallbackQueryHandler(show_cart, pattern="^panier$"))
    app.add_handler(CallbackQueryHandler(clear_cart, pattern="^vider_panier$"))
    app.add_handler(CallbackQueryHandler(show_horaires, pattern="^horaires$"))
    app.add_handler(CallbackQueryHandler(show_contact, pattern="^contact$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_message))

    print("Labolabot demarre !")
    app.run_polling()

if __name__ == "__main__":
    main()
