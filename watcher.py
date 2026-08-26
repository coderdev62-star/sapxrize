import os
import asyncio
import logging
from datetime import datetime
from typing import Optional
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import html

from database import (
    save_message, get_message, delete_message, update_message_text,
    get_owner
)

logger = logging.getLogger(__name__)


class MessageWatcher:
    def __init__(self, client: TelegramClient, notify_callback):
        self.client = client
        self.notify_callback = notify_callback
        self.media_dir = "data/media"
        os.makedirs(self.media_dir, exist_ok=True)
    
    def _escape_html(self, text: str) -> str:
        """Экранирует HTML-специальные символы."""
        return html.escape(text, quote=False)
    
    def _get_sender_info(self, event) -> tuple:
        """Получает информацию об отправителе."""
        sender = event.sender
        if sender:
            name = getattr(sender, 'first_name', '') or getattr(sender, 'username', '') or 'Unknown'
            username = getattr(sender, 'username', None)
            return name, username
        return 'Unknown', None
    
    def _get_message_kind(self, message) -> str:
        """Определяет тип сообщения."""
        if message.photo:
            return 'photo'
        elif message.video:
            return 'video'
        elif message.video_note:
            return 'video_note'
        elif message.voice:
            return 'voice'
        elif message.sticker:
            return 'sticker'
        elif message.gif:
            return 'gif'
        elif message.audio:
            return 'audio'
        elif message.document:
            return 'document'
        elif message.contact:
            return 'contact'
        elif message.geo:
            return 'geo'
        else:
            return 'text'
    
    def _format_message_text(self, message, kind: str) -> Optional[str]:
        """Форматирует текст сообщения для хранения."""
        if message.text:
            return message.text
        
        # Для медиа формируем описание
        kind_names = {
            'photo': '🖼 Фото',
            'video': '🎬 Видео',
            'video_note': '🎥 Видео-кружок',
            'voice': '🎤 Голосовое',
            'sticker': '🙂 Стикер',
            'gif': '🎞 GIF',
            'audio': '🎵 Аудио',
            'document': '📎 Документ',
            'contact': '👤 Контакт',
            'geo': '📍 Геолокация'
        }
        
        text = kind_names.get(kind, '📩 Сообщение')
        
        if message.message:
            caption = self._escape_html(message.message)
            text += f"\n{caption}"
        
        return text
    
    async def _download_media(self, message, msg_id: int) -> Optional[str]:
        """Скачивает медиа-файл для входящих сообщений."""
        if not message.media:
            return None
        
        try:
            # Определяем расширение
            ext = '.jpg'
            if isinstance(message.media, MessageMediaDocument):
                doc = message.media.document
                if hasattr(doc, 'mime_type'):
                    mime = doc.mime_type
                    if 'video' in mime:
                        ext = '.mp4'
                    elif 'audio' in mime:
                        ext = '.mp3'
                    elif 'gif' in mime:
                        ext = '.gif'
            
            filename = f"{msg_id}{ext}"
            filepath = os.path.join(self.media_dir, filename)
            
            await self.client.download_media(message, filepath)
            logger.info(f"Медиа скачано: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Ошибка скачивания медиа: {e}")
            return None
    
    async def handle_new_message(self, event):
        """Обрабатывает новые сообщения."""
        if not event.is_private:
            return
        
        message = event.message
        msg_id = message.id
        chat_id = event.chat_id
        sender_id = message.from_id.user_id if message.from_id else chat_id
        
        name, username = self._get_sender_info(event)
        is_incoming = message.out is False  # out=True = исходящее
        
        kind = self._get_message_kind(message)
        text = self._format_message_text(message, kind)
        
        media_path = None
        if is_incoming and kind == 'photo':
            media_path = await self._download_media(message, msg_id)
        
        date = message.date.isoformat() if message.date else datetime.now().isoformat()
        
        success = save_message(
            msg_id, chat_id, sender_id, name, username,
            is_incoming, kind, text, media_path, date
        )
        
        if success:
            logger.info(f"💾 Сохранено сообщение от {name} (id={msg_id}, kind={kind})")
    
    async def handle_deleted_message(self, event):
        """Обрабатывает удалённые сообщения."""
        if not event.is_private:
            return
        
        deleted_ids = event.deleted_ids
        owner_id = get_owner()
        
        if not owner_id:
            return
        
        for msg_id in deleted_ids:
            cached = get_message(msg_id)
            
            if not cached:
                logger.info(f"🗑 Удалённое сообщение {msg_id} нет в кэше (пришло до запуска)")
                continue
            
            if not cached['is_incoming']:
                # Исходящее - просто удаляем из кэша
                delete_message(msg_id)
                logger.info(f"🗑 Исходящее сообщение {msg_id} удалено из кэша")
                continue
            
            # Входящее - уведомляем владельца
            sender_name = self._escape_html(cached['sender_name'])
            kind = cached['kind']
            text = cached['text']
            media_path = cached['media_path']
            
            notification = f"🗑 <b>Удалённое сообщение</b>\n\n"
            notification += f"👤 <b>От:</b> {sender_name}\n"
            
            if media_path and os.path.exists(media_path):
                # Отправляем фото с подписью
                caption = notification + f"\n{text}"
                try:
                    await self.notify_callback(owner_id, photo_path=media_path, caption=caption)
                    os.remove(media_path)
                    logger.info(f"🗑 Удалённое сообщение от {sender_name} восстановлено (с фото)")
                except Exception as e:
                    logger.error(f"Ошибка отправки фото: {e}")
                    # Fallback - отправляем только текст
                    notification += f"\n{text}"
                    await self.notify_callback(owner_id, text=notification)
            else:
                notification += f"\n{text}"
                await self.notify_callback(owner_id, text=notification)
                logger.info(f"🗑 Удалённое сообщение от {sender_name} восстановлено")
            
            delete_message(msg_id)
    
    async def handle_edited_message(self, event):
        """Обрабатывает изменённые сообщения."""
        if not event.is_private:
            return
        
        message = event.message
        msg_id = message.id
        
        if message.out:  # Только входящие
            return
        
        cached = get_message(msg_id)
        
        old_text = cached['text'] if cached else None
        new_text = self._format_message_text(message, self._get_message_kind(message))
        
        if not cached:
            # Сообщения нет в кэше - просто сохраняем новую версию
            chat_id = event.chat_id
            sender_id = message.from_id.user_id if message.from_id else chat_id
            name, username = self._get_sender_info(event)
            kind = self._get_message_kind(message)
            date = message.date.isoformat() if message.date else datetime.now().isoformat()
            
            save_message(msg_id, chat_id, sender_id, name, username, True, kind, new_text, None, date)
            logger.info(f"✏️ Новое редактирование {msg_id} (старая версия неизвестна)")
            return
        
        if old_text != new_text:
            sender_name = self._escape_html(cached['sender_name'])
            owner_id = get_owner()
            
            if owner_id:
                notification = f"✏️ <b>Изменённое сообщение</b>\n\n"
                notification += f"👤 <b>От:</b> {sender_name}\n\n"
                notification += f"❌ <b>Было:</b>\n{old_text}\n\n"
                notification += f"✅ <b>Стало:</b>\n{new_text}"
                
                await self.notify_callback(owner_id, text=notification)
                logger.info(f"✏️ Изменено сообщение от {sender_name}")
            
            update_message_text(msg_id, new_text)
    
    def register_handlers(self):
        """Регистрирует обработчики событий."""
        self.client.add_event_handler(
            self.handle_new_message,
            events.NewMessage(incoming=True, outgoing=True)
        )
        
        self.client.add_event_handler(
            self.handle_deleted_message,
            events.MessageDeleted()
        )
        
        self.client.add_event_handler(
            self.handle_edited_message,
            events.MessageEdited()
        )
        
        logger.info("Обработчики событий зарегистрированы")
