import os
import requests
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)

# ==========================================
# CONFIGURATION (EDIT THESE)
# ==========================================
USDT_ADDRESS = "TNeruWPC3x3iavsFcLggjawwnfPLhiPq83"
EXPECTED_AMOUNT = 10.50

# Define conversation states
SHOW_ADDRESS, WAIT_FOR_TXID = range(2)

# ==========================================
# TELEGRAM BOT LOGIC
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 1: Explain the rules."""
    rules_text = (
        "Welcome to Krypto 2X 🚀\n\n"
        "Here are the rules:\n"
        "1. You will receive [Insert Digital Good/Service].\n"
        "2. Payments are strictly in USDT (TRC20).\n"
        "3. Access is granted automatically upon verification.\n\n"
        "Do you agree and wish to proceed?"
    )
    keyboard = [[InlineKeyboardButton("I Agree - Show Address", callback_data="agree")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Handle both new /start commands and restarting from existing prompts
    if update.message:
        await update.message.reply_text(rules_text, reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text(rules_text, reply_markup=reply_markup)
        
    return SHOW_ADDRESS

async def show_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 2: Show the USDT address and ask for TxID."""
    query = update.callback_query
    await query.answer()
    
    msg = (
        f"Please send exactly **{EXPECTED_AMOUNT} USDT (TRC20)** to this address:\n\n"
        f"`{USDT_ADDRESS}`\n\n"
        "Once you have sent the payment, please **paste your Transaction ID (TxHash)** below so I can verify it."
    )
    
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=msg, reply_markup=reply_markup, parse_mode='Markdown')
    return WAIT_FOR_TXID

async def verify_txid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 3: Receive TxID and verify the payment."""
    txid = update.message.text.strip()
    
    wait_msg = await update.message.reply_text("⏳ Checking the blockchain for this Transaction ID... Please wait.")
    
    # ==========================================
    # API VERIFICATION LOGIC GOES HERE
    # ==========================================
    # Mocking the verification result for now. 
    # You will integrate TronGrid or your custom API here later.
    payment_verified = False 
    
    if payment_verified:
        await wait_msg.edit_text("✅ Payment Confirmed! Here is your access link/file: [LINK]")
        return ConversationHandler.END
    else:
        await wait_msg.edit_text(
            "❌ Payment not found or invalid TxID. Make sure the transaction is complete and you pasted the correct TRC20 Hash.\n\n"
            "Please paste the correct Transaction ID, or type /start to restart."
        )
        return WAIT_FOR_TXID

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Payment cancelled. Type /start to try again.")
    return ConversationHandler.END

# ==========================================
# DUMMY WEB SERVER (FOR RENDER)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running online!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ==========================================
# MAIN EXECUTION
# ==========================================
def main() -> None:
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not BOT_TOKEN:
        print("Error: No TELEGRAM_BOT_TOKEN found in environment variables.")
        return

    # Start the Flask web server in a background thread
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Build and start the Telegram Bot
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SHOW_ADDRESS: [
                CallbackQueryHandler(show_address, pattern="^agree$"),
                CallbackQueryHandler(cancel, pattern="^cancel$")
            ],
            WAIT_FOR_TXID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, verify_txid),
                CallbackQueryHandler(cancel, pattern="^cancel$")
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)
    
    print("Bot is polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
