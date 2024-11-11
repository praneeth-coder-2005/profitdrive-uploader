import os
import logging
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters

# Set up logging for better debugging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables for security
TELEGRAM_BOT_TOKEN = '7820729855:AAG_ph7Skh4SqGxIWYYcRNigQqCKdnVW354'
PROFITDRIVE_API_KEY = '469|L92XQ8B7ZgaEePJEdQV24p8IPLWyhp15xHVTYT69'
PROFITDRIVE_UPLOAD_URL = 'https://pd.heracle.net/uploads'  # Replace with actual API endpoint

# Flask app setup for webhook handling
app = Flask(__name__)

@app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def webhook_handler():
    print("Incoming request:", request.get_json())  # Debugging log
    update = Update.de_json(request.get_json(), bot)
    dp.process_update(update)
    return "ok", 200

def start(update: Update, context: CallbackContext):
    """Send a welcome message when the /start command is issued."""
    update.message.reply_text("Hello! Send me a file and I'll upload it to ProfitDrive.")

def handle_document(update: Update, context: CallbackContext):
    """Handle document uploads from the user."""
    print("handle_document function triggered")  # Debugging log
    update.message.reply_text("Processing your document...")

    file = update.message.document
    if file:
        print(f"Received document: {file.file_name}")  # Debugging log
        try:
            # Download the file to a local temporary directory
            file_path = file.get_file().download()
            print(f"File downloaded to: {file_path}")  # Debugging log
            update.message.reply_text("Uploading your file to ProfitDrive...")

            # Upload the file to ProfitDrive
            with open(file_path, 'rb') as f:
                response = requests.post(
                    PROFITDRIVE_UPLOAD_URL,
                    headers={"Authorization": f"Bearer {PROFITDRIVE_API_KEY}"},
                    files={"file": f},
                    data={"parentId": "null", "relativePath": file.file_name}
                )
            print(f"Upload response: {response.status_code} - {response.text}")  # Debugging log

            # Handle the response from ProfitDrive
            if response.status_code == 201:
                update.message.reply_text("File uploaded successfully!")
            else:
                logger.error(f"Upload failed. Status code: {response.status_code}, Message: {response.text}")
                update.message.reply_text(f"Failed to upload. Status code: {response.status_code}, Message: {response.text}")

            # Remove the local file after upload
            os.remove(file_path)
            print("File removed after upload")  # Debugging log

        except Exception as e:
            logger.error(f"Error during file handling: {e}")
            update.message.reply_text("An error occurred while processing your file.")
    else:
        logger.warning("No document detected")
        update.message.reply_text("No document detected.")

def error(update: Update, context: CallbackContext):
    """Log errors caused by Updates."""
    logger.warning(f"Update {update} caused error {context.error}")

def main():
    """Start the bot."""
    global bot, dp
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher
    bot = updater.bot

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    dp.add_error_handler(error)

    # Set the webhook
    webhook_url = f"https://profitdrive-uploader.onrender.com/{TELEGRAM_BOT_TOKEN}"
    bot.set_webhook(webhook_url)
    logger.info(f"Webhook set to {webhook_url}")

    # Run the Flask app
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()
