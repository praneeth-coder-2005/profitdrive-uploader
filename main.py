import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram Bot Token and ProfitDrive API Key
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
PROFITDRIVE_API_KEY = 'YOUR_PROFITDRIVE_API_KEY'
PROFITDRIVE_UPLOAD_URL = 'https://pd.heracle.net/uploads'  # Replace with actual API endpoint

def start(update: Update, context: CallbackContext):
    """Send a welcome message when the /start command is issued."""
    update.message.reply_text("Hello! Send me a file, and I'll upload it to ProfitDrive.")

def handle_document(update: Update, context: CallbackContext):
    """Handle document uploads from the user with simple download/upload."""
    logger.info("handle_document function triggered")
    file = update.message.document
    if file:
        try:
            # Confirm that the bot received the document
            update.message.reply_text("File received! Preparing to upload...")

            # Get file download URL
            file_info = context.bot.get_file(file.file_id)
            download_url = file_info.file_path
            download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{download_url}"
            logger.info(f"Download URL: {download_url}")

            # Download the file locally
            local_file_path = f"/tmp/{file.file_name}"
            file_response = requests.get(download_url)
            with open(local_file_path, "wb") as f:
                f.write(file_response.content)
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
            logger.info(f"ProfitDrive response: {response.status_code} - {response.text}")

            # Handle the response from ProfitDrive
            if response.status_code == 201:
                update.message.reply_text("File uploaded successfully!")
            else:
                update.message.reply_text(f"Failed to upload. Status code: {response.status_code}, Message: {response.text}")

        except Exception as e:
            logger.error(f"Error during file handling: {e}")
            update.message.reply_text("An error occurred while processing your file.")
    else:
        update.message.reply_text("No document detected. Please send a valid file.")

def main():
    """Start the bot using polling."""
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    dp.add_error_handler(lambda update, context: logger.warning(f"Error: {context.error}"))

    # Start polling
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
