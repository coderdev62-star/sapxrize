import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

DB_PATH = "data/watcher.db"


def get_connection() -> sqlite3.Connection:
    """Создает подключение к базе данных."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """Инициализирует структуру базы данных."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                msg_id INTEGER PRIMARY KEY,
                chat_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                sender_name TEXT NOT NULL,
                sender_username TEXT,
                is_incoming INTEGER NOT NULL,
                kind TEXT NOT NULL,
                text TEXT,
                media_path TEXT,
                date TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS owners (
                chat_id INTEGER PRIMARY KEY,
                created_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        raise


def save_message(msg_id: int, chat_id: int, sender_id: int, sender_name: str,
                 sender_username: Optional[str], is_incoming: bool, kind: str,
                 text: Optional[str], media_path: Optional[str], date: str) -> bool:
    """Сохраняет сообщение в кэш."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO messages 
            (msg_id, chat_id, sender_id, sender_name, sender_username, is_incoming, kind, text, media_path, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (msg_id, chat_id, sender_id, sender_name, sender_username, 
              1 if is_incoming else 0, kind, text, media_path, date))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения сообщения {msg_id}: {e}")
        return False


def get_message(msg_id: int) -> Optional[Dict[str, Any]]:
    """Получает сообщение из кэша по ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT msg_id, chat_id, sender_id, sender_name, sender_username, 
                   is_incoming, kind, text, media_path, date
            FROM messages WHERE msg_id = ?
        """, (msg_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'msg_id': row[0],
                'chat_id': row[1],
                'sender_id': row[2],
                'sender_name': row[3],
                'sender_username': row[4],
                'is_incoming': bool(row[5]),
                'kind': row[6],
                'text': row[7],
                'media_path': row[8],
                'date': row[9]
            }
        return None
    except Exception as e:
        logger.error(f"Ошибка получения сообщения {msg_id}: {e}")
        return None


def delete_message(msg_id: int) -> bool:
    """Удаляет сообщение из кэша."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM messages WHERE msg_id = ?", (msg_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Ошибка удаления сообщения {msg_id}: {e}")
        return False


def update_message_text(msg_id: int, new_text: str) -> bool:
    """Обновляет текст сообщения в кэше."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE messages SET text = ? WHERE msg_id = ?", (new_text, msg_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Ошибка обновления текста сообщения {msg_id}: {e}")
        return False


def set_owner(chat_id: int) -> bool:
    """Назначает владельца бота."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        created_at = datetime.now().isoformat()
        cursor.execute("INSERT OR REPLACE INTO owners (chat_id, created_at) VALUES (?, ?)",
                      (chat_id, created_at))
        
        conn.commit()
        conn.close()
        logger.info(f"Владелец назначен: {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Ошибка назначения владельца: {e}")
        return False


def get_owner() -> Optional[int]:
    """Получает ID владельца бота."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT chat_id FROM owners LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else None
    except Exception as e:
        logger.error(f"Ошибка получения владельца: {e}")
        return None


def remove_owner() -> bool:
    """Удаляет владельца бота."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM owners")
        
        conn.commit()
        conn.close()
        logger.info("Владелец удалён")
        return True
    except Exception as e:
        logger.error(f"Ошибка удаления владельца: {e}")
        return False


def get_messages_count() -> int:
    """Возвращает количество сообщений в кэше."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    except Exception as e:
        logger.error(f"Ошибка получения количества сообщений: {e}")
        return 0
