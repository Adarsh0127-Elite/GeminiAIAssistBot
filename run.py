import telebot
from src.telegram_bot import bot
from src.config import ADMIN_ID

def setup_menu_commands():
    """Configures scoped Menu buttons in the Telegram UI."""
    # Force Telegram servers to drop the old cached list
    bot.delete_my_commands() 
    
    # 1. Base commands for everyone (Authorized Users & Groups)
    base_commands = [
        telebot.types.BotCommand("start", "Initialize the bot"),
        telebot.types.BotCommand("analyze", "Reply to an image/doc to analyze it"),
        telebot.types.BotCommand("clear", "Wipe the current conversational memory")
    ]
    # Set this menu as the default for all chats
    bot.set_my_commands(base_commands, scope=telebot.types.BotCommandScopeDefault())
    
    # 2. Admin commands (Only visible to you)
    admin_commands = base_commands + [
        telebot.types.BotCommand("authorise", "Grant access to a user/group"),
        telebot.types.BotCommand("unauthorise", "Revoke access"),
        telebot.types.BotCommand("list", "Show authorized users/groups"),
        telebot.types.BotCommand("speedtest", "Run a GCP network speedtest"),
        telebot.types.BotCommand("server", "Fetch GCP instance telemetry")
    ]
    
    # Push the admin menu explicitly to your personal chat ID
    if ADMIN_ID:
        try:
            bot.set_my_commands(admin_commands, scope=telebot.types.BotCommandScopeChat(ADMIN_ID))
            print("✅ Admin Menu configured successfully.")
        except Exception as e:
            print(f"⚠️ Could not set admin menu: {e}")

    print("✅ Default Menu button configured.")

if __name__ == "__main__":
    print("Clearing previous webhooks...")
    bot.delete_webhook()
    
    # Run the setup function before polling starts
    setup_menu_commands()
    
    print("🚀 Starting bot in infinity polling mode...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
