from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from utils.config import TELEGRAM_TOKEN
from utils.logger import setup_logger
from helpers.channel_helpers import start_add_channel, add_channel, start_delete_channel, delete_channel
from helpers.menu_helpers import start, handle_menu_selection, new_summary_timer, remove_timer, confirm_remove_timer, cancel_remove_timer, handle_custom_timer_input, status, help_menu, start_summarize_text, handle_default_timer_setting
from helpers.single_summary_helpers import summarize_text_command, handle_rating, send_rating_buttons

# Initialize logger
logger = setup_logger()

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('new_timer', new_summary_timer))
    application.add_handler(CommandHandler('remove_timer', remove_timer))
    application.add_handler(CommandHandler('confirm_remove_timer', handle_default_timer_setting))
    application.add_handler(CommandHandler('confirm_remove_timer', confirm_remove_timer))
    application.add_handler(CommandHandler('cancel_remove_timer', cancel_remove_timer))
    application.add_handler(CommandHandler('channel_add_start', start_add_channel))
    application.add_handler(CommandHandler('add_channel', add_channel))
    application.add_handler(CommandHandler('channel_delete_start', start_delete_channel))
    application.add_handler(CommandHandler('delete_channel', delete_channel))
    application.add_handler(CommandHandler('status', status))
    application.add_handler(CommandHandler('help', help_menu))
    application.add_handler(CommandHandler('new_rating', send_rating_buttons))
    application.add_handler(CommandHandler('summarize_text', summarize_text_command))
    application.add_handler(CommandHandler('summarize_text_start', start_summarize_text))

    # Custom Time Message Handler
    application.add_handler(MessageHandler(filters.Regex(r'^\d{2}:\d{2}$'), handle_custom_timer_input))  # Handle custom time input

    # Channel Name and Link Handlers
    application.add_handler(MessageHandler(filters.Regex(r'^(?:@|https://t\.me/(?!.*\d+$)).*'), add_channel))  # Handle channel addition, exclude post links

    # Telegram Post Summarization Handler
    application.add_handler(MessageHandler(filters.Regex(r'https://t\.me/.*\d+$'), summarize_text_command))  # Handle post summarization

    # CallbackQuery Handlers
    application.add_handler(CallbackQueryHandler(handle_rating, pattern="^rate_"))
    application.add_handler(CallbackQueryHandler(handle_menu_selection, pattern='^(?!rate_).*$'))

    logger.info("Bot started.")
    application.run_polling()

if __name__ == '__main__':
    main()
