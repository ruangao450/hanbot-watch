import os
import asyncio
import json
import datetime
import re
from telethon import TelegramClient
from telethon.sessions import StringSession
import requests

# --- GÜVENLİK KONTROLÜ ---
# GitHub Sırlarının (Secrets) alınıp alınmadığını kontrol et
SESSION_STRING = os.getenv('TELEGRAM_SESSION_STRING')
SOURCE_CHANNEL = os.getenv('TELEGRAM_SOURCE_CHANNEL')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
VOICE_CHANNEL_ID = os.getenv('VOICE_CHANNEL_ID')

if not all([SESSION_STRING, SOURCE_CHANNEL, DISCORD_WEBHOOK_URL, DISCORD_BOT_TOKEN, VOICE_CHANNEL_ID]):
    print("!!!!!! HATA !!!!!!")
    print("GitHub Secrets'daki değişkenlerden biri veya birkaçı eksik! Lütfen 'Settings > Secrets and variables > Actions' menüsünü kontrol edin.")
    print(f"SESSION_STRING dolu mu? {'Evet' if SESSION_STRING else 'HAYIR'}")
    print(f"SOURCE_CHANNEL dolu mu? {'Evet' if SOURCE_CHANNEL else 'HAYIR'}")
    print(f"DISCORD_WEBHOOK_URL dolu mu? {'Evet' if DISCORD_WEBHOOK_URL else 'HAYIR'}")
    print(f"DISCORD_BOT_TOKEN dolu mu? {'Evet' if DISCORD_BOT_TOKEN else 'HAYIR'}")
    print(f"VOICE_CHANNEL_ID dolu mu? {'Evet' if VOICE_CHANNEL_ID else 'HAYIR'}")
    exit() # Hata varsa programı hemen durdur

def update_voice_channel_name(version_number):
    print(f"-> Ses kanalı adı güncelleniyor: {version_number}")
    url = f"https://discord.com/api/v10/channels/{VOICE_CHANNEL_ID}"
    new_name = f"✅ Updated: {version_number}"
    headers = { "Authorization": f"Bot {DISCORD_BOT_TOKEN}", "Content-Type": "application/json" }
    payload = { "name": new_name }
    try:
        response = requests.patch(url, headers=headers, json=payload)
        if response.status_code == 200: print(" -> Başarılı: Ses kanalı adı güncellendi.")
        else: print(f" -> HATA: Kanal adı güncellenemedi. Durum: {response.status_code} - {response.text}")
    except Exception as e: print(f" -> HATA: API isteği sırasında hata: {e}")

def send_to_discord_embed(description, filename, message_link):
    print("-> Discord'a embed mesajı gönderiliyor...")
    try:
        embed_data = { "embeds": [{ "title": "🛡️ Hanbot Version Watch (TEST)", "color": 3447003, "fields": [{ "name": "✅ Status: New Version Detected", "value": "This is a test message processing the last available update.", "inline": False }, { "name": "📁 File Name", "value": f"`{filename}`", "inline": False }, { "name": "📋 Release Notes", "value": description or "No specific notes provided.", "inline": False }, { "name": "⬇️ Download Link", "value": f"[Click here to download from Telegram]({message_link})", "inline": False }], "footer": { "text": "Hanbot Watcher" }, "timestamp": datetime.datetime.utcnow().isoformat() }] }
        response = requests.post(DISCORD_WEBHOOK_URL, json=embed_data)
        if response.status_code >= 400: print(f" -> HATA: Discord'a mesaj gönderilemedi. Durum: {response.status_code} - {response.text}")
        else: print(" -> Başarılı: Embed mesajı gönderildi.")
    except Exception as e: print(f" -> HATA: Embed gönderiminde hata: {e}")

async def main():
    print("TEST MODU BAŞLATILDI: Son dosya içeren mesaj aranıyor...")
    async with TelegramClient(StringSession(SESSION_STRING), 12345, 'dummy') as client:
        print(f"'{SOURCE_CHANNEL}' kanalına bağlanıldı...")
        
        message_to_process = None
        # Son 20 mesajı kontrol et, dosya içeren ilkini bul
        async for message in client.iter_messages(SOURCE_CHANNEL, limit=20):
            print(f"  - Mesaj ID {message.id} kontrol ediliyor... Dosya var mı? {'Evet' if message.document else 'Hayır'}")
            if message and message.document:
                print(f"  -> İşlenecek mesaj bulundu!")
                message_to_process = message
                break
        
        if message_to_process:
            filename = message_to_process.document.attributes[-1].file_name
            description_text = message_to_process.text
            message_link = f"https://t.me/{SOURCE_CHANNEL}/{message_to_process.id}"
            print(f"İşlenecek dosya: {filename}")

            match = re.search(r'\((\d{2,}\.\d{2,}\.\d{3,}\.\d{4,})\)', description_text)
            if match:
                version = match.group(1)
                print(f"Versiyon numarası bulundu: {version}")
                update_voice_channel_name(version)
            else:
                print("Mesajda versiyon numarası bulunamadı, ses kanalı güncellenmeyecek.")
            
            send_to_discord_embed(description_text, filename, message_link)
        else:
            print("Son 20 mesajda dosya içeren bir mesaj bulunamadı. Test sonlandırılıyor.")
            
    print("Test tamamlandı.")

if __name__ == "__main__":
    asyncio.run(main())
