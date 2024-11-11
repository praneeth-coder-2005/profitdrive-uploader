import os
import logging
import requests
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters

# Set up logging for better debugging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables for security
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PROFITDRIVE_API_KEY = os.getenv('PROFITDRIVE_API_KEY')
PROFITDRIVE_UPLOAD_URL = 'https://pd.heracle.net/uploads'  # Replace with actual API endpoint

def start(update: Update, context: CallbackContext):
    """Send a welcome message when the /start command is issued."""
    update.message.reply_text("Hello! Send me a file and I'll upload it to ProfitDrive.")

def handle_document(update: Update, context: CallbackContext):
    """Handle document uploads from the user."""
    logger.info("handle_document function triggered")
    file = update.message.document
    if file:
        logger.info(f"Received document: {file.file_name}")
        try:
            # Download the file to a local temporary directory
            file_path = file.get_file().download()
            logger.info(f"File downloaded to: {file_path}")
            update.message.reply_text("Uploading your file to ProfitDrive...")

            # Upload the file to ProfitDrive
            with open(file_path, 'rb') as f:
                response = requests.post(
                    PROFITDRIVE_UPLOAD_URL,
                    headers={"Authorization": f"Bearer {PROFITDRIVE_API_KEY}"},
                    files={"file": f},
                    data={"parentId": "null", "relativePath": file.file_name}
                )

            # Log the response for debugging
            logger.info(f"ProfitDrive response: {response.status_code}, {response.text}")

            # Handle the response from ProfitDrive
            if response.status_code == 201:
                update.message.reply_text("File uploaded successfully!")
            else:
                logger.error(f"Upload failed. Status code: {response.status_code}, Message: {response.text}")
                update.message.reply_text(f"Failed to upload. Status code: {response.status_code}, Message: {response.text}")

            # Remove the local file after upload
            os.remove(file_path)
            logger.info("File removed after upload")

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
    # Create the Updater and pass it your bot's token.
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher

    # Add handlers for commands and messages
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))

    # Log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()
    logger.info("Bot started polling")
    updater.idle()

if __name__ == "__main__":
    main()
          
