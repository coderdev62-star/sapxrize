import asyncio
import logging
import os
import sys
import aiohttp
from dotenv import load_dotenv
from telethon import TelegramClient
from aiohttp import web

from database import init_db, get_owner
from watcher import MessageWatcher
from bot import TelegramBot

# Загрузка переменных окружения
load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
SESSION = os.getenv('SESSION', 'watcher_session')
SESSION_STRING = os.getenv('SESSION_STRING')  # Строковая сессия для Render
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
PORT = int(os.getenv('PORT', '8080'))
PING_INTERVAL = int(os.getenv('PING_INTERVAL', '300'))  # 5 минут по умолчанию


class SecretFilter(logging.Filter):
    """Фильтр для маскирования секретов в логах."""
    
    def __init__(self):
        super().__init__()
        self.secrets = []
        
        if API_HASH:
            self.secrets.append(API_HASH)
        if BOT_TOKEN:
            self.secrets.append(BOT_TOKEN)
    
    def filter(self, record):
        msg = record.getMessage()
        for secret in self.secrets:
            if secret and secret in msg:
                record.msg = msg.replace(secret, '***MASKED***')
                record.args = ()
        return True


def setup_logging():
    """Настраивает логирование."""
    os.makedirs('data', exist_ok=True)
    
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    
    # Формат логов
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    
    # Консольный handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SecretFilter())
    
    # Файловый handler
    file_handler = logging.FileHandler('data/watcher.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.addFilter(SecretFilter())
    
    # Настройка root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return logging.getLogger(__name__)


logger = setup_logging()


# HTTP сервер для health check
app = web.Application()


async def health_check(request):
    """Health check endpoint для пинга."""
    return web.Response(text="OK", status=200)


async def start_http_server():
    """Запускает HTTP сервер для health check."""
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logger.info(f"HTTP сервер запущен на порту {PORT} (health check: /health)")


async def self_ping_task():
    """Задача само-пинга для поддержания активности."""
    logger.info(f"Само-пинг активирован (интервал: {PING_INTERVAL} сек)")
    
    while True:
        try:
            await asyncio.sleep(PING_INTERVAL)
            
            # Пингуем сами себя
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f'http://localhost:{PORT}/health') as resp:
                        if resp.status == 200:
                            logger.debug("Само-пинг успешен")
                except Exception as e:
                    logger.warning(f"Ошибка само-пинга: {e}")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Ошибка в задаче само-пинга: {e}")


async def notify_owner(bot: TelegramBot, chat_id: int, text: str = None, 
                     photo_path: str = None, caption: str = None):
    """Отправляет уведомление владельцу."""
    try:
        if photo_path and os.path.exists(photo_path):
            await bot.send_photo(chat_id, photo_path, caption or '', parse_mode='HTML')
        elif text:
            await bot.send_message(chat_id, text, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {e}")


async def main():
    """Главная функция - запускает оба компонента."""
    logger.info("🩸 SPAXRIZE запускается...")
    
    # Инициализация БД
    init_db()
    
    # Создание клиентов
    if SESSION_STRING:
        # Используем строковую сессию (для Render)
        from telethon.sessions import StringSession
        telethon_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        logger.info("Используется строковая сессия")
    else:
        # Используем файловую сессию (локально)
        session_path = f"data/{SESSION}"
        telethon_client = TelegramClient(session_path, API_ID, API_HASH)
        logger.info(f"Используется файловая сессия: {session_path}")
    
    bot = TelegramBot(BOT_TOKEN)
    
    # Запуск бота
    await bot.start()
    
    # Создание вотчера
    watcher = MessageWatcher(telethon_client, lambda chat_id, **kwargs: notify_owner(bot, chat_id, **kwargs))
    watcher.register_handlers()
    
    # Запуск Telethon
    await telethon_client.connect()
    
    # Проверка авторизации
    if not await telethon_client.is_user_authorized():
        logger.error("Пользователь не авторизован. Запустите скрипт авторизации отдельно.")
        await bot.stop()
        return
    
    logger.info(f"Авторизован как: {(await telethon_client.get_me()).first_name}")
    
    # Уведомление владельцу о старте (если уже активен)
    owner_id = get_owner()
    if owner_id:
        await notify_owner(bot, owner_id, "🩸 SPAXRIZE запущен")
        logger.info(f"Уведомление о старте отправлено владельцу {owner_id}")
    
    # Запуск обоих компонентов параллельно
    try:
        # Запуск HTTP сервера для health check
        logger.info("Запуск HTTP сервера...")
        http_task = asyncio.create_task(start_http_server())
        
        # Запуск само-пинга
        ping_task = asyncio.create_task(self_ping_task())
        
        # Telethon с catch_up=True для догрузки пропущенных апдейтов
        logger.info("Запуск MTProto-клиента...")
        telethon_task = asyncio.create_task(telethon_client.run_until_disconnected())
        
        logger.info("Запуск Bot API...")
        bot_task = asyncio.create_task(bot.process_updates(lambda *args, **kwargs: None))
        
        # Ждём завершения любого из задач
        await asyncio.gather(telethon_task, bot_task, ping_task)
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки...")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
    finally:
        logger.info("Остановка...")
        await telethon_client.disconnect()
        await bot.stop()
        logger.info("SPAXRIZE остановлен")


if __name__ == "__main__":
    # Генерация баннера при первом запуске
    if not os.path.exists("data/banner.png"):
        logger.info("Генерация баннера...")
        from generate_banner import generate_banner
        generate_banner()
    
    asyncio.run(main())
