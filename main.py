import os
import logging
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram Bot Token and ProfitDrive API Key
TELEGRAM_BOT_TOKEN = '7820729855:AAG_ph7Skh4SqGxIWYYcRNigQqCKdnVW354'
PROFITDRIVE_API_KEY = '469|L92XQ8B7ZgaEePJEdQV24p8IPLWyhp15xHVTYT69'
PROFITDRIVE_UPLOAD_URL = 'https://pd.heracle.net/uploads'  # Replace with actual API endpoint

# Flask app setup for webhook handling
app = Flask(__name__)

@app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def webhook_handler():
    """Handle incoming updates from Telegram"""
    update = Update.de_json(request.get_json(), bot)
    print("Incoming request:", request.get_json())  # Debugging log
    dp.process_update(update)
    return "ok", 200

def start(update: Update, context: CallbackContext):
    """Send a welcome message when the /start command is issued."""
    update.message.reply_text("Hello! Send me a file, and I'll upload it to ProfitDrive.")

def handle_document(update: Update, context: CallbackContext):
    """Handle document uploads from the user with progress messages."""
    logger.info("handle_document function triggered")
    file = update.message.document

    # Confirm that the bot received the document
    update.message.reply_text("File received! Preparing to upload...")

    if file:
        try:
            # Get the file download URL from Telegram
            file_info = bot.get_file(file.file_id)
            file_url = file_info.file_path
            download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_url}"
            logger.info(f"Download URL: {download_url}")
            
            # Download the file locally
            local_file_path = f"/tmp/{file.file_name}"
            response = requests.get(download_url)
            with open(local_file_path, "wb") as f:
                f.write(response.content)
            logger.info(f"File downloaded locally to {local_file_path}")

            # Inform the user that the bot is uploading the file
            update.message.reply_text("Uploading your file to ProfitDrive, please wait...")

            # Upload the file to ProfitDrive
            with open(local_file_path, 'rb') as f:
                response = requests.post(
                    PROFITDRIVE_UPLOAD_URL,
                    headers={"Authorization": f"Bearer {PROFITDRIVE_API_KEY}"},
                    files={"file": f},
                    data={"parentId": "null", "relativePath": file.file_name}
                )
            
            # Log the response for debugging
            logger.info(f"ProfitDrive response: {response.status_code} - {response.text}")

            # Handle the response from ProfitDrive
            if response.status_code == 201:
                update.message.reply_text("File uploaded successfully!")
            else:
                logger.error(f"Upload failed. Status code: {response.status_code}, Message: {response.text}")
                update.message.reply_text(f"Failed to upload. Status code: {response.status_code}, Message: {response.text}")

            # Clean up the local file
            os.remove(local_file_path)
            logger.info("Local file removed after upload")

        except Exception as e:
            logger.error(f"Error during file handling: {e}")
            update.message.reply_text("An error occurred while processing your file. Please try again.")
    else:
        logger.warning("No document detected")
        update.message.reply_text("No document detected. Please send a valid file.")

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
