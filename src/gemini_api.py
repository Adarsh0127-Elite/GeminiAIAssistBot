import google.generativeai as genai
from src.config import GEMINI_API_KEY, GEMINI_MODEL_NAME

genai.configure(api_key=GEMINI_API_KEY)

user_sessions = {}

def get_chat_session(chat_id):
    """Initializes a highly advanced chat session using structured prompt engineering."""
    if chat_id not in user_sessions:
        instructions = """
        You are an elite AI assistant and expert systems engineer. 
        Your primary domain expertise includes:
        - Advanced Linux system administration and bash scripting.
        - Android Open Source Project (AOSP) compilation, kernel debugging, and custom ROM development (like LunarisAOSP).
        - University-level Physics, Chemistry, and Mathematics.

        OPERATIONAL GUIDELINES:
        1. Always format responses clearly using Markdown.
        2. Use LaTeX for any complex mathematical or scientific equations.
        3. When debugging code or logs, explicitly identify the root cause before suggesting a fix.
        4. Do not offer unsolicited advice; answer the specific question asked.
        5. Maintain a professional, highly analytical, and direct tone.
        """
        
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL_NAME,
            system_instruction=instructions
        )
        user_sessions[chat_id] = model.start_chat(history=[])
    
    return user_sessions[chat_id]

def generate_text_response(chat_id, text):
    session = get_chat_session(chat_id)
    response = session.send_message(text)
    return response.text

def analyze_image(prompt, image):
    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    response = model.generate_content([prompt, image])
    return response.text

def analyze_document(prompt, text_content):
    # Truncate to ensure we don't exceed the context window limits
    truncated_content = text_content[:35000] 
    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    response = model.generate_content(f"{prompt}\n\nDocument Data:\n{truncated_content}")
    return response.text

def clear_session(chat_id):
    if chat_id in user_sessions:
        del user_sessions[chat_id]
        return True
    return False
