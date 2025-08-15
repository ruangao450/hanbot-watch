import os
import asyncio
from telethon import TelegramClient, events
import requests
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()

# --- Telegram Ayarları ---
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_NAME = 'telegram_session'
# İzlenecek Telegram kanalının kullanıcı adı (örneğin 'duyurukanali')
SOURCE_CHANNEL = os.getenv('TELEGRAM_SOURCE_CHANNEL')

# --- Discord Ayarları ---
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Telegram istemcisini başlat
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

def send_to_discord(message_text, file_path=None):
    """Mesajı ve dosyayı Discord'a gönderir."""
    try:
        if file_path:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                payload = {'content': message_text}
                response = requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)
        else:
            payload = {'content': message_text}
            response = requests.post(DISCORD_WEBHOOK_URL, data=payload)

        # Yanıtı kontrol et
        if 200 <= response.status_code < 300:
            print(f"Mesaj başarıyla Discord'a gönderildi. Status: {response.status_code}")
        else:
            print(f"Discord'a gönderirken hata oluştu: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Discord'a gönderim sırasında bir hata meydana geldi: {e}")
    finally:
        # Geçici dosyayı sil
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"Geçici dosya silindi: {file_path}")

@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def handler(event):
    """Telegram'dan yeni mesaj geldiğinde tetiklenir."""
    message = event.message
    message_text = f"**Yeni Hanbot Güncellemesi Geldi!**\n\n{message.text}"

    # Eğer mesaj bir dosya içeriyorsa
    if message.document:
        print(f"Dosya bulundu: {message.document.attributes[-1].file_name}")
        
        # Dosyayı indir
        file_path = await message.download_media()
        print(f"Dosya indirildi: {file_path}")

        # Discord'a gönder
        send_to_discord(message_text, file_path)
    else:
        # Sadece metin mesajıysa dosyayı gönderme
        print("Mesajda dosya bulunamadı, sadece metin gönderiliyor.")
        send_to_discord(message_text)

async def main():
    """Ana çalışma fonksiyonu."""
    print("Bot başlatılıyor...")
    await client.start()
    print(f"Telegram'a başarıyla bağlanıldı. '{SOURCE_CHANNEL}' kanalı dinleniyor...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    # Asenkron döngüyü çalıştır
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(main())
    else:
        loop.run_until_complete(main())
