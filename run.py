import telebot
from src.telegram_bot import bot

def setup_menu_commands():
    """Configures the blue Menu button in the Telegram UI."""
    # Force Telegram servers to drop the old cached list
    bot.delete_my_commands() 
    
    commands = [
        telebot.types.BotCommand("start", "Initialize the bot"),
        telebot.types.BotCommand("analyze", "Reply to an image/doc to analyze it"),
        telebot.types.BotCommand("authorise", "Grant access to a user/group (Admin)"),
        telebot.types.BotCommand("unauthorise", "Revoke access (Admin)"),
        telebot.types.BotCommand("list", "Show authorized users/groups (Admin)"),
        telebot.types.BotCommand("speedtest", "Run a GCP network speedtest (Admin)"),
        telebot.types.BotCommand("server", "Fetch GCP instance telemetry (Admin)"),
        telebot.types.BotCommand("clear", "Wipe the current conversational memory")
    ]
    
    # Send the new command list to Telegram servers
    bot.set_my_commands(commands)
    print("✅ Telegram Menu button configured.")

if __name__ == "__main__":
    print("Clearing previous webhooks...")
    bot.delete_webhook()
    
    # Run the setup function before polling starts
    setup_menu_commands()
    
    print("🚀 Starting bot in infinity polling mode...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
