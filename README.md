### Gemini Telegram BOT

### Description

This project is a chatbot application that uses Google's Generative AI (Gemini) to generate responses. It is built with Python. The chatbot can be interacted via a Telegram bot.

```bash
git clone -b main https://github.com/Adarsh0127-Elite/GeminiAIAssistBot.git
```
### Install required filea
```bash
sudo apt update && sudo apt upgrade && sudo apt install python3-pip -y && sudo apt install python3.10-venv -y && python3 -m venv venv && source venv/bin/activate && pip install speedtest-cli && pip install -r requirements.txt
```
#### Setup Systemd Service
```bash
sudo nano /etc/systemd/system/geminibot.service
```
### Paste the following configuration:(Change your user accordingly)
```bash
[Unit]
Description=Modular Gemini Telegram Bot
After=network.target network-online.target

[Service]
Type=simple
User=adarsh027
Group=adarsh027
WorkingDirectory=/home/adarsh027/GeminiAIAssistBot
EnvironmentFile=/home/adarsh027/GeminiAIAssistBot/.env
ExecStart=/home/adarsh027/GeminiAIAssistBot/venv/bin/python3 /home/adarsh027/GeminiAIAssistBot/run.py
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target
```

### Import your configs
```bash
nano .env
```

### Copy and Paste all these in .env
Note: Create a telegram bot using @BotFather after creating Telegram Bot you will get you bot token 
For your telegram id aka Admin id use @UserInfoToBot
```bash
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
GEMINI_API_KEY=YOUR_API_KEY
GEMINI_MODEL_NAME=gemini-2.5-flash
ADMIN_ID=YOUR_TELEGRAM_ID
```

### Start your service
```bash
sudo systemctl daemon-reload
sudo systemctl enable geminibot.service
sudo systemctl start geminibot.service
```

### Restart your service
```bash
sudo systemctl restart geminibot.service
```

### If anything crashes can grab logs using 
```bash
sudo journalctl -u geminibot.service -f
```

### Credits:
- [Adarsh0127-Elite](https://github.com/Adarsh0127-Elite)
