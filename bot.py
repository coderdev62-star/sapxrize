import asyncio
import logging
import os
import html
from typing import Optional
from aiohttp import ClientSession
import json

from database import set_owner, get_owner, remove_owner, get_messages_count

logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.session: Optional[ClientSession] = None
        self.banner_path = "data/banner.png"
        self.banner_file_id: Optional[str] = None
    
    async def start(self):
        """Запускает сессию aiohttp."""
        self.session = ClientSession()
        logger.info("Bot API сессия запущена")
    
    async def stop(self):
        """Останавливает сессию aiohttp."""
        if self.session:
            await self.session.close()
            logger.info("Bot API сессия остановлена")
    
    async def _request(self, method: str, **kwargs) -> Optional[dict]:
        """Выполняет запрос к Telegram Bot API."""
        if not self.session:
            return None
        
        url = f"{self.api_url}/{method}"
        
        try:
            async with self.session.post(url, json=kwargs) as response:
                result = await response.json()
                if result.get('ok'):
                    return result.get('result')
                else:
                    error_desc = result.get('description', 'Unknown error')
                    logger.error(f"API Error: {error_desc}")
                    raise Exception(f"API Error: {error_desc}")
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise
    
    async def get_updates(self, offset: int = 0, timeout: int = 30) -> list:
        """Получает обновления через long polling."""
        result = await self._request('getUpdates', offset=offset, timeout=timeout)
        return result if result else []
    
    async def send_message(self, chat_id: int, text: str, parse_mode: str = 'HTML',
                          reply_markup: Optional[dict] = None) -> Optional[dict]:
        """Отправляет текстовое сообщение."""
        return await self._request('sendMessage', 
                                   chat_id=chat_id, 
                                   text=text, 
                                   parse_mode=parse_mode,
                                   reply_markup=reply_markup)
    
    async def send_photo(self, chat_id: int, photo: str, caption: str = '',
                        parse_mode: str = 'HTML', reply_markup: Optional[dict] = None) -> Optional[dict]:
        """Отправляет фото (путь или file_id)."""
        if os.path.exists(photo):
            # Отправляем файл
            from aiohttp import FormData
            
            form = FormData()
            form.add_field('chat_id', str(chat_id))
            form.add_field('caption', caption)
            form.add_field('parse_mode', parse_mode)
            if reply_markup:
                form.add_field('reply_markup', json.dumps(reply_markup))
            
            try:
                with open(photo, 'rb') as f:
                    form.add_field('photo', f, filename='photo.png', content_type='image/png')
                    url = f"{self.api_url}/sendPhoto"
                    async with self.session.post(url, data=form) as response:
                        result = await response.json()
                        if result.get('ok'):
                            return result.get('result')
                        else:
                            logger.error(f"Send photo error: {result.get('description')}")
                            return None
            except Exception as e:
                logger.error(f"Send photo file error: {e}")
                return None
        else:
            # Отправляем по file_id
            return await self._request('sendPhoto',
                                      chat_id=chat_id,
                                      photo=photo,
                                      caption=caption,
                                      parse_mode=parse_mode,
                                      reply_markup=reply_markup)
    
    async def edit_message_text(self, chat_id: int, message_id: int, text: str,
                               parse_mode: str = 'HTML', reply_markup: Optional[dict] = None) -> bool:
        """Редактирует текст сообщения."""
        params = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': parse_mode
        }
        if reply_markup is not None:
            params['reply_markup'] = reply_markup
        
        result = await self._request('editMessageText', **params)
        return result is not None
    
    async def edit_message_reply_markup(self, chat_id: int, message_id: int,
                                       reply_markup: Optional[dict] = None) -> bool:
        """Редактирует inline-кнопки сообщения."""
        result = await self._request('editMessageReplyMarkup',
                                     chat_id=chat_id,
                                     message_id=message_id,
                                     reply_markup=reply_markup)
        return result is not None
    
    async def answer_callback_query(self, callback_query_id: str, text: str = '',
                                    show_alert: bool = False) -> bool:
        """Отвечает на callback query."""
        result = await self._request('answerCallbackQuery',
                                     callback_query_id=callback_query_id,
                                     text=text,
                                     show_alert=show_alert)
        return result is not None
    
    def _escape_html(self, text: str) -> str:
        """Экранирует HTML."""
        return html.escape(text, quote=False)
    
    async def handle_command_start(self, chat_id: int, message_id: int) -> Optional[int]:
        """Обрабатывает команду /start."""
        owner = get_owner()
        
        if owner is None:
            # Первый запуск - отправляем баннер с кнопкой активации
            caption = (
                "🩸 <b>SPAXRIZE</b> — вотчер личных чатов\n\n"
                "Бот следит за твоими личными чатами и уведомляет о:\n"
                "• 🗑 Удалённых сообщениях\n"
                "• ✏️ Изменённых сообщениях\n\n"
                "Нажми кнопку ниже для активации."
            )
            
            keyboard = {
                'inline_keyboard': [[
                    {'text': '🩸 Добавить в автоматизацию', 'callback_data': 'watch:activate'}
                ]]
            }
            
            # Отправляем баннер
            if os.path.exists(self.banner_path):
                result = await self.send_photo(chat_id, self.banner_path, caption, 
                                              reply_markup=keyboard)
                if result:
                    self.banner_file_id = result.get('photo', [{}])[0].get('file_id')
            else:
                # Если баннера нет, отправляем текст
                await self.send_message(chat_id, caption, reply_markup=keyboard)
            
            return None
        else:
            # Владелец уже назначен
            if chat_id == owner:
                status_text = (
                    f"✅ <b>SPAXRIZE активен</b>\n\n"
                    f"👤 Владелец: {chat_id}\n"
                    f"💾 Сообщений в кэше: {get_messages_count()}\n\n"
                    f"<b>Команды:</b>\n"
                    f"/status — статус бота\n"
                    f"/test — тестовое уведомление\n"
                    f"/stop — остановить слежение"
                )
                await self.send_message(chat_id, status_text)
            else:
                await self.send_message(chat_id, "⛔ Бот уже привязан к другому аккаунту")
            
            return owner
    
    async def handle_command_status(self, chat_id: int):
        """Обрабатывает команду /status."""
        owner = get_owner()
        
        if owner is None:
            await self.send_message(chat_id, "⚠️ Бот не активирован. Используй /start")
        elif chat_id != owner:
            await self.send_message(chat_id, "⛔ Ты не владелец бота")
        else:
            status_text = (
                f"✅ <b>Статус SPAXRIZE</b>\n\n"
                f"👤 Владелец: {owner}\n"
                f"💾 Сообщений в кэше: {get_messages_count()}\n"
                f"🔄 Статус: Активен"
            )
            await self.send_message(chat_id, status_text)
    
    async def handle_command_test(self, chat_id: int):
        """Обрабатывает команду /test."""
        owner = get_owner()
        
        if owner is None:
            await self.send_message(chat_id, "⚠️ Бот не активирован. Используй /start")
        elif chat_id != owner:
            await self.send_message(chat_id, "⛔ Ты не владелец бота")
        else:
            await self.send_message(chat_id, "🩸 <b>Тестовое уведомление</b>\n\nКанал доставки работает!")
            logger.info(f"Тестовое уведомление отправлено {chat_id}")
    
    async def handle_command_stop(self, chat_id: int):
        """Обрабатывает команду /stop."""
        owner = get_owner()
        
        if owner is None:
            await self.send_message(chat_id, "⚠️ Бот не активирован")
        elif chat_id != owner:
            await self.send_message(chat_id, "⛔ Ты не владелец бота")
        else:
            remove_owner()
            await self.send_message(chat_id, "🛑 <b>SPAXRIZE остановлен</b>\n\nВладелец снят. Используй /start для повторной активации.")
            logger.info(f"Владелец {chat_id} остановил бота")
    
    async def handle_callback_activate(self, chat_id: int, message_id: int) -> bool:
        """Обрабатывает callback активации."""
        owner = get_owner()
        
        if owner is None:
            # Назначаем владельца
            set_owner(chat_id)
            
            # Редактируем сообщение
            new_text = (
                "✅ <b>Успешно добавлено!</b>\n\n"
                "SPAXRIZE активен и начал работу.\n\n"
                "⚠️ <b>Важно:</b> Сообщения, написанные ДО активации, восстановить невозможно.\n\n"
                "<b>Команды:</b>\n"
                "/status — статус бота\n"
                "/test — тестовое уведомление\n"
                "/stop — остановить слежение"
            )
            
            await self.edit_message_text(chat_id, message_id, new_text)
            await self.answer_callback_query(chat_id, "Активировано!")
            logger.info(f"Владелец активирован: {chat_id}")
            return True
        elif owner == chat_id:
            await self.answer_callback_query(chat_id, "Уже активен!", show_alert=True)
            return False
        else:
            await self.answer_callback_query(chat_id, "⛔ Уже привязан к другому аккаунту", show_alert=True)
            return False
    
    async def process_updates(self, notify_callback):
        """Обрабатывает обновления от Telegram."""
        offset = 0
        
        # Задержка перед началом polling чтобы старые процессы успели завершиться
        logger.info("Waiting 30s before starting polling...")
        await asyncio.sleep(30)
        logger.info("Starting Bot API polling...")
        
        while True:
            try:
                updates = await self.get_updates(offset=offset, timeout=30)
                
                if updates:
                    logger.info(f"Received {len(updates)} updates")
                
                for update in updates:
                    offset = update['update_id'] + 1
                    
                    # Обработка сообщений
                    if 'message' in update:
                        message = update['message']
                        chat_id = message['chat']['id']
                        message_id = message['message_id']
                        
                        if 'text' in message:
                            text = message['text']
                            # Обработка команд
                            if text == '/start':
                                await self.send_message(chat_id, "🩸 SPAXRIZE Bot\n\nЭтот бот сохраняет сообщения из Telegram.", reply_markup={'inline_keyboard': [[{'text': '🩸 Добавить в автоматизацию', 'callback_data': 'activate'}]]})
                            elif text == '/status':
                                await self.send_message(chat_id, f"✅ Бот активен\nСессия: {self.api_url}")
                            elif text == '/test':
                                await notify_callback(chat_id, text="🧪 Тестовое уведомление")
                                await self.send_message(chat_id, "🧪 Тестовое уведомление отправлено")
                            elif text == '/stop':
                                await self.send_message(chat_id, "⛔ Бот остановлен")
                                return
                            
                    # Обработка callback query
                    elif 'callback_query' in update:
                        callback = update['callback_query']
                        chat_id = callback['from']['id']
                        callback_id = callback['id']
                        data = callback['data']
                        
                        if data == 'activate':
                            await self.handle_activation(chat_id, callback_id, notify_callback)
            except Exception as e:
                error_msg = str(e)
                if 'Conflict' in error_msg:
                    # Conflict ошибка - ждем и пробуем снова
                    logger.warning(f"Conflict detected, waiting 30s before retry...")
                    await asyncio.sleep(30)
                    continue
                else:
                    logger.error(f"Error getting updates: {e}")
                    await asyncio.sleep(5)
                    continue
