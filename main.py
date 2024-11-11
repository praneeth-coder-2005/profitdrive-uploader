import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters
import os

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Set up Telegram bot token and ProfitDrive API key
TELEGRAM_BOT_TOKEN = '7820729855:AAG_ph7Skh4SqGxIWYYcRNigQqCKdnVW354'
PROFITDRIVE_API_KEY = '469|L92XQ8B7ZgaEePJEdQV24p8IPLWyhp15xHVTYT69'
PROFITDRIVE_UPLOAD_URL = 'https://pd.heracle.net/uploads'  # ProfitDrive upload endpoint

def start(update: Update, context: CallbackContext):
    """Send a welcome message when the /start command is issued."""
    update.message.reply_text("Hello! Send me a file, and I'll upload it to ProfitDrive.")

def handle_document(update: Update, context: CallbackContext):
    """Handle document uploads from the user."""
    file = update.message.document
    if file:
        update.message.reply_text("File received! Downloading and uploading to ProfitDrive...")

        # Get the file download URL from Telegram
        file_info = context.bot.get_file(file.file_id)
        download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_info.file_path}"
        
        try:
            # Download the file
            file_response = requests.get(download_url)
            file_response.raise_for_status()
            
            # Save the file locally
            local_file_path = f"/tmp/{file.file_name}"
            with open(local_file_path, "wb") as f:
                f.write(file_response.content)
            logger.info(f"Downloaded file to {local_file_path}")

            # Upload the file to ProfitDrive
            with open(local_file_path, 'rb') as f:
                response = requests.post(
                    PROFITDRIVE_UPLOAD_URL,
                    headers={"Authorization": f"Bearer {PROFITDRIVE_API_KEY}"},
                    files={"file": f},
                    data={"parentId": "null", "relativePath": file.file_name}
                )

            # Check the ProfitDrive response
            if response.status_code == 201:
                upload_data = response.json()
                file_url = upload_data['fileEntry']['url']
                update.message.reply_text(f"File uploaded successfully! Access it at: {file_url}")
            else:
                update.message.reply_text(f"Failed to upload. Status code: {response.status_code}, Message: {response.text}")
            
            # Clean up local file
            os.remove(local_file_path)
        
        except Exception as e:
            logger.error(f"Error during file handling: {e}")
            update.message.reply_text("An error occurred while processing your file.")
    else:
        update.message.reply_text("Please send a valid file.")

def main():
    """Start the bot using polling."""
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
