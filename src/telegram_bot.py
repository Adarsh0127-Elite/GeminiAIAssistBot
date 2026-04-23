import telebot
import io
import os
import json
import subprocess
import PyPDF2
from PIL import Image
from src.config import TELEGRAM_BOT_TOKEN, ADMIN_ID
from src import gemini_api, speedtest_cmd

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# --- AUTHORIZATION SYSTEM ---
AUTH_FILE = "/home/adarsh027/GeminiAIAssistBot/authorized.json"

def load_auth():
    """Loads the list of authorized IDs from the JSON file."""
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_auth(auth_set):
    """Saves the list of authorized IDs to the JSON file."""
    with open(AUTH_FILE, "w") as f:
        json.dump(list(auth_set), f)

AUTHORIZED_IDS = load_auth()

def is_authorized(message):
    """Checks if the user or the group chat is allowed to use the bot."""
    if message.from_user.id == ADMIN_ID:
        return True
    if message.from_user.id in AUTHORIZED_IDS or message.chat.id in AUTHORIZED_IDS:
        return True
    return False

# --- ADMIN COMMANDS ---

@bot.message_handler(commands=['authorise'])
def authorise_access(message):
    if message.from_user.id != ADMIN_ID: return

    target_id = None
    target_name = ""
    args = message.text.split()

    # 1. If replying to a user's message
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name or str(target_id)
    # 2. If an ID was typed manually (e.g. /authorise 123456)
    elif len(args) > 1:
        try:
            target_id = int(args[1])
            target_name = f"User ID {target_id}"
        except ValueError:
            bot.reply_to(message, "⚠️ Invalid ID format. Please provide a numeric ID.")
            return
    # 3. Otherwise, authorize the current chat/group
    else:
        target_id = message.chat.id
        target_name = message.chat.title or "this chat"

    if target_id in AUTHORIZED_IDS:
        bot.reply_to(message, f"✅ {target_name} is already authorized.")
    else:
        AUTHORIZED_IDS.add(target_id)
        save_auth(AUTHORIZED_IDS)
        bot.reply_to(message, f"✅ Access granted to {target_name}.")

@bot.message_handler(commands=['revoke', 'unauthorise'])
def revoke_access(message):
    if message.from_user.id != ADMIN_ID: return 

    target_id = None
    target_name = ""
    args = message.text.split()

    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name or str(target_id)
    elif len(args) > 1:
        try:
            target_id = int(args[1])
            target_name = f"User ID {target_id}"
        except ValueError:
            bot.reply_to(message, "⚠️ Invalid ID format.")
            return
    else:
        target_id = message.chat.id
        target_name = message.chat.title or "this chat"

    if target_id == ADMIN_ID:
        bot.reply_to(message, "⚠️ You cannot revoke your own Admin access.")
        return

    if target_id in AUTHORIZED_IDS:
        AUTHORIZED_IDS.remove(target_id)
        save_auth(AUTHORIZED_IDS)
        bot.reply_to(message, f"🚫 Access revoked for {target_name}.")
    else:
        bot.reply_to(message, f"⚠️ {target_name} is not currently authorized.")

@bot.message_handler(commands=['list'])
def list_authorized(message):
    if message.from_user.id != ADMIN_ID: return

    bot.send_chat_action(message.chat.id, 'typing')
    if not AUTHORIZED_IDS:
        bot.reply_to(message, "📝 **Authorized List:**\n\nNo additional users or groups are currently authorized.", parse_mode='Markdown')
        return

    reply = "📝 **Authorized Users & Groups:**\n━━━━━━━━━━━━━━━━━━━\n"
    for auth_id in list(AUTHORIZED_IDS):
        try:
            chat_info = bot.get_chat(auth_id)
            name = chat_info.title if chat_info.title else chat_info.first_name
            reply += f"• `{auth_id}` - **{name}**\n"
        except Exception:
            reply += f"• `{auth_id}` - *(Name Unavailable)*\n"
            
    bot.reply_to(message, reply, parse_mode='Markdown')

@bot.message_handler(commands=['server'])
def server_status(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ Unauthorized.")
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        os_ver = subprocess.run(['cat', '/etc/os-release'], capture_output=True, text=True).stdout
        os_name = [line.split('=')[1].strip('"') for line in os_ver.split('\n') if line.startswith('PRETTY_NAME=')][0]
        uname = subprocess.run(['uname', '-r'], capture_output=True, text=True).stdout.strip()
        uptime = subprocess.run(['uptime', '-p'], capture_output=True, text=True).stdout.strip()
        cpu_cores = subprocess.run(['nproc'], capture_output=True, text=True).stdout.strip()
        cpu_load = subprocess.run(['cat', '/proc/loadavg'], capture_output=True, text=True).stdout.split()[0:3]
        load_str = " ".join(cpu_load)
        ram = subprocess.run(['free', '-h'], capture_output=True, text=True).stdout.split('\n')[1].split()
        ram_total, ram_used = ram[1], ram[2]
        disk = subprocess.run(['df', '-h', '/'], capture_output=True, text=True).stdout.split('\n')[1].split()
        disk_total, disk_used, disk_pct = disk[1], disk[2], disk[4]

        reply = (
            f"🖥️ **Advanced Server Telemetry**\n━━━━━━━━━━━━━━━━━━━\n"
            f"**OS:** `{os_name}`\n**Kernel:** `{uname}`\n**Uptime:** `{uptime}`\n\n"
            f"⚙️ **Compute:**\n• Cores: `{cpu_cores}`\n• Load (1/5/15m): `{load_str}`\n\n"
            f"🧠 **Memory (RAM):**\n• Used: `{ram_used}` / `{ram_total}`\n\n"
            f"💾 **Storage (Root):**\n• Used: `{disk_used}` / `{disk_total}` ({disk_pct})"
        )
        bot.reply_to(message, reply, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=['speedtest'])
def handle_speedtest(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ Unauthorized.")
        return

    status_msg = bot.reply_to(message, "⏳ *Running speedtest...*", parse_mode='Markdown')
    bot.send_chat_action(message.chat.id, 'upload_photo')
    try:
        image_url, caption = speedtest_cmd.run_speedtest()
        bot.send_photo(message.chat.id, photo=image_url, caption=caption, parse_mode='Markdown')
        bot.delete_message(message.chat.id, status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Speedtest failed: {e}", chat_id=message.chat.id, message_id=status_msg.message_id)

# --- AI COMMANDS (Authorized Users Only) ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Provides a detailed, structured welcome message outlining all capabilities."""
    if not is_authorized(message): return
    
    detailed_help = (
        "🤖 **Westside Systems Assistant | Gemini AI**\n\n"
        "Welcome! I am an advanced virtual assistant optimized for **systems engineering, AOSP development, Linux administration, and university-level analysis.**\n\n"
        "How can I assist you today? Here is what I can do:\n━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 **Conversational AI & Technical Advising:**\n"
        "- Ask complex technical questions regarding Python, Bash scripting, AOSP debugging, or server configurations.\n"
        "- Resolve math equations and physics problems (I can render LaTeX!).\n"
        "- Chat freely; I maintain short-term conversational memory.\n\n"
        
        "📂 **Advanced File Analysis:**\n"
        "*(Works with direct send OR by replying to an existing message)*\n\n"
        "**1. Multimodal Image Analysis**\n"
        "- Send or reply to an image with a prompt like:\n"
        "  └ `/analyze Locate the compiler error in this screenshot.`\n\n"
        "**2. Document & Log Parsing**\n"
        "- Send or reply to `.txt`, `.log`, or `.pdf` files.\n"
        "  - *Reply Example:* (Replying to a build log)\n"
        "    └ `/analyze Find the linker error.`\n"
        "  - *Direct Example:* (Caption for a science PDF)\n"
        "    └ `Summarize this chapter on Optics.`\n\n"
        
        "🛠️ **Control:**\n"
        "- `/clear`: Wipe our current conversational context to start a fresh topic.\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "Send your query or upload a file to begin."
    )
    
    bot.reply_to(message, detailed_help, parse_mode='Markdown')

@bot.message_handler(commands=['clear'])
def clear_history(message):
    if not is_authorized(message): return
    if gemini_api.clear_session(message.chat.id):
        bot.reply_to(message, "🧹 Context cleared. Starting fresh.")
    else:
        bot.reply_to(message, "No active context to clear.")

@bot.message_handler(commands=['analyze'])
def handle_analyze_reply(message):
    if not is_authorized(message): return
    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ You must reply to an image or document with `/analyze [prompt]`")
        return

    target_msg = message.reply_to_message
    bot.send_chat_action(message.chat.id, 'typing')
    prompt = message.text.replace('/analyze', '').strip() or "Analyze this file in detail."

    try:
        if target_msg.photo:
            file_info = bot.get_file(target_msg.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            image = Image.open(io.BytesIO(downloaded_file))
            response = gemini_api.analyze_image(prompt, image)
            bot.reply_to(message, response, parse_mode='Markdown')
            
        elif target_msg.document:
            file_name = target_msg.document.file_name.lower()
            if not (file_name.endswith('.txt') or file_name.endswith('.log') or file_name.endswith('.pdf')):
                bot.reply_to(message, "⚠️ Supported files: `.txt`, `.log`, `.pdf`.")
                return

            file_info = bot.get_file(target_msg.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            extracted_text = ""
            if file_name.endswith('.pdf'):
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(downloaded_file))
                for page in pdf_reader.pages:
                    extracted_text += page.extract_text() + "\n"
            else:
                extracted_text = downloaded_file.decode('utf-8', errors='ignore')
            
            response = gemini_api.analyze_document(prompt, extracted_text)
            bot.reply_to(message, response, parse_mode='Markdown')
        else:
            bot.reply_to(message, "⚠️ Message replied to does not contain a supported file.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(content_types=['photo'])
def handle_direct_photo(message):
    if not is_authorized(message): return
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image = Image.open(io.BytesIO(downloaded_file))
        prompt = message.caption if message.caption else "Describe this image in detail."
        response = gemini_api.analyze_image(prompt, image)
        bot.reply_to(message, response, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(content_types=['document'])
def handle_direct_document(message):
    if not is_authorized(message): return
    bot.send_chat_action(message.chat.id, 'typing')
    file_name = message.document.file_name.lower()
    
    if not (file_name.endswith('.txt') or file_name.endswith('.log') or file_name.endswith('.pdf')):
        return # Ignore silently

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        extracted_text = ""
        if file_name.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(downloaded_file))
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
        else:
            extracted_text = downloaded_file.decode('utf-8', errors='ignore')
            
        prompt = message.caption if message.caption else "Summarize this document."
        response = gemini_api.analyze_document(prompt, extracted_text)
        bot.reply_to(message, response, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    # Ignore messages that start with '/' so it doesn't try to answer invalid commands
    if message.text.startswith('/'): return
    if not is_authorized(message): return
    
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        response = gemini_api.generate_text_response(message.chat.id, message.text)
        bot.reply_to(message, response, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"API Error: {e}")
