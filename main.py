# Pipedream'in ihtiyaç duyabileceği kütüphaneleri yüklemek için
import subprocess
import sys

# Gerekli kütüphaneleri kontrol et ve yükle
try:
    import telethon
    import requests
    import dotenv
except ImportError:
    print("Gerekli kütüphaneler yükleniyor...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "telethon", "requests", "python-dotenv"])
    print("Kütüphaneler yüklendi.")

import os
import asyncio
from telethon import TelegramClient, events
import requests
from dotenv import load_dotenv

# .env veya ortam değişkenlerini yükle
load_dotenv()

# --- Telegram Ayarları (Pipedream Ortam Değişkenlerinden gelecek) ---
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_NAME = 'telegram_session'
# İzlenecek Telegram kanalının kullanıcı adı
SOURCE_CHANNEL = os.getenv('TELEGRAM_SOURCE_CHANNEL')

# --- Discord Ayarları ---
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Telegram istemcisini başlat
# Not: Pipedream'in dosya sisteminde oturum dosyasını saklayacağız
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

def send_to_discord(message_text, file_path=None):
    """Mesajı ve dosyayı Discord'a gönderir."""
    download_path = None
    try:
        # Pipedream'de dosya /tmp dizinine yazılır
        download_path = os.path.join("/tmp", os.path.basename(file_path))
        os.rename(file_path, download_path)

        with open(download_path, 'rb') as f:
            files = {'file': (os.path.basename(download_path), f)}
            payload = {'content': message_text}
            response = requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)

        if 200 <= response.status_code < 300:
            print(f"Mesaj başarıyla Discord'a gönderildi.")
        else:
            print(f"Discord'a gönderirken hata oluştu: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Discord'a gönderim sırasında bir hata meydana geldi: {e}")
    finally:
        if download_path and os.path.exists(download_path):
            os.remove(download_path)
            print(f"Geçici dosya silindi: {download_path}")

@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def handler(event):
    """Telegram'dan yeni mesaj geldiğinde tetiklenir."""
    message = event.message
    
    # Sadece dosya içeren mesajlarla ilgileniyoruz
    if message.document:
        print(f"Dosya bulundu: {message.document.attributes[-1].file_name}")
        message_text = f"**Yeni Hanbot Güncellemesi Geldi!**\n\n{message.text}"
        
        # Dosyayı indir
        file_path = await message.download_media()
        print(f"Dosya indirildi: {file_path}")

        # Discord'a gönder
        send_to_discord(message_text, file_path)
    else:
        print("Gelen mesaj dosya içermiyor, işlem yapılmadı.")


async def main():
    """Ana çalışma fonksiyonu."""
    await client.start()
    print(f"Telegram'a başarıyla bağlanıldı. '{SOURCE_CHANNEL}' kanalı dinleniyor...")
    await client.run_until_disconnected()

# Pipedream'de bir 'handler' fonksiyonu olması beklenir
async def handler(pd: "pipedream"):
    # Bu script sürekli çalışacağı için bu handler'ı sadece başlatma için kullanıyoruz.
    # Ancak Pipedream'in çalışma mantığı gereği, script'in kendisi ana işlem olmalı.
    # Bu yüzden script'i doğrudan çalıştıracağız.
    # Pipedream'in bir bug'ı veya özelliği olarak, bu handler'ı boş bırakıp
    # script'in geri kalanını modül seviyesinde çalıştırmak genellikle işe yarar.
    print("Pipedream iş akışı tetiklendi, bot zaten çalışıyor olmalı.")

# Ana programı doğrudan çalıştır
if __name__ == '__main__':
    print("Bot başlatılıyor...")
    client.loop.run_until_complete(main())
