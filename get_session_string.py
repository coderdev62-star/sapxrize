"""
Скрипт для получения строки сессии Telethon.
Запустите после авторизации через auth.py
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

print(f"🩸 SPAXRIZE - Получение строки сессии")
print(f"Сессия: {session_path}")
print()

async def main():
    # Создаем клиент со строковой сессией
    from telethon.sessions import StringSession
    string_client = TelegramClient(StringSession(), API_ID, API_HASH)
    await string_client.connect()
    
    print("🔄 Авторизация через QR-код для создания строковой сессии...")
    print()
    
    # QR-код авторизация
    qr_login = await string_client.qr_login()
    
    print("📱 Сканируйте QR-код в Telegram:")
    print("   Настройки → Устройства → Связать устройство → Сканировать QR-код")
    print()
    
    # Показываем QR-код
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
    
    session_string = string_client.session.save()
    
    print("✅ Строка сессии получена:")
    print()
    print("=" * 60)
    print(session_string)
    print("=" * 60)
    print()
    print("Скопируйте эту строку и добавьте как SESSION_STRING на Render")
    
    await string_client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
