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
AUTH_FILE = "/home/adarsh/gemini/authorized.json"

def load_auth():
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_auth(auth_set):
    with open(AUTH_FILE, "w") as f:
        json.dump(list(auth_set), f)

AUTHORIZED_IDS = load_auth()

def is_authorized(message):
    if message.from_user.id == ADMIN_ID:
        return True
    if message.from_user.id in AUTHORIZED_IDS or message.chat.id in AUTHORIZED_IDS:
        return True
    return False

# --- ADMIN COMMANDS ---

@bot.message_handler(commands=['authorise'])
def authorise_access(message):
    if message.from_user.id != ADMIN_ID: return

    target_id, target_name = None, ""
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name or "User"
    else:
        target_id = message.chat.id
        target_name = message.chat.title or "this private chat"

    if target_id in AUTHORIZED_IDS:
        bot.reply_to(message, f"✅ {target_name} is already authorized.")
    else:
        AUTHORIZED_IDS.add(target_id)
        save_auth(AUTHORIZED_IDS)
        bot.reply_to(message, f"✅ Access granted to {target_name}.")

@bot.message_handler(commands=['revoke'])
def revoke_access(message):
    if message.from_user.id != ADMIN_ID: return 

    target_id, target_name = None, ""
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name or "User"
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
        bot.reply_to(message, f"⚠️ {target_name} is not in the authorized list.")

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
            f"⚙️ **Compute:**\n• Cores: `{cpu_cores}`\n• Load: `{load_str}`\n\n"
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

# --- AI COMMANDS ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not is_authorized(message): return
    bot.reply_to(message, "🤖 **Advanced Gemini AI Active.**\n\nSend me text, or reply to an image/document with `/analyze [prompt]`.", parse_mode='Markdown')

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
    if not (file_name.endswith('.txt') or file_name.endswith('.log') or file_name.endswith('.pdf')): return

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
    if message.text.startswith('/'): return
    if not is_authorized(message): return
    
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        response = gemini_api.generate_text_response(message.chat.id, message.text)
        bot.reply_to(message, response, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"API Error: {e}")
