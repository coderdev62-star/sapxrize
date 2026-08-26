"""
Скрипт авторизации Telethon.
Запустите этот скрипт один раз перед первым использованием main.py
"""
import os
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
SESSION = os.getenv('SESSION', 'watcher_session')

os.makedirs('data', exist_ok=True)
session_path = f"data/{SESSION}"

print(f"🩸 SPAXRIZE - Авторизация")
print(f"Сессия: {session_path}")
print(f"API ID: {API_ID}")
print()

async def main():
    client = TelegramClient(session_path, API_ID, API_HASH)
    
    # Подключаемся к Telegram
    await client.connect()
    
    # Попробовать QR-код авторизацию
    print("🔄 Попытка авторизации через QR-код...")
    qr_login = await client.qr_login()
    
    print("📱 Сканируйте QR-код в Telegram:")
    print("   Настройки → Устройства → Связать устройство → Сканировать QR-код")
    print()
    
    # Показываем QR-код в консоли
    try:
        import qrcode
        qr = qrcode.QRCode()
        qr.add_data(qr_login.url)
        qr.print_ascii()
    except ImportError:
        print(f"🔗 Или откройте эту ссылку в браузере:")
        print(f"   {qr_login.url}")
        print()
    
    # Ждём сканирования
    await qr_login.wait()
    
    me = await client.get_me()
    print(f"✅ Авторизован как: {me.first_name} (@{me.username})")
    print(f"📱 Телефон: {me.phone}")
    print()
    print("Сессия сохранена. Теперь можно запускать main.py")
    
    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
