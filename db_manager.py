import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "qq_messages.db")
MAX_MESSAGES_PER_GROUP = 10000

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT,
            sender_id TEXT,
            sender_name TEXT,
            content TEXT,
            timestamp INTEGER,
            is_summarized BOOLEAN DEFAULT 0
        )
    ''')
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN is_profiled BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError:
        pass # Column already exists

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_group_id ON messages(group_id)')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT,
            summary TEXT,
            start_time INTEGER,
            end_time INTEGER,
            timestamp INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def insert_message(group_id, sender_id, sender_name, content, timestamp=None):
    if timestamp is None:
        timestamp = int(datetime.now().timestamp())
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO messages (group_id, sender_id, sender_name, content, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (group_id, sender_id, sender_name, content, timestamp))
    
    cursor.execute('''
        DELETE FROM messages 
        WHERE group_id = ? AND id NOT IN (
            SELECT id FROM messages 
            WHERE group_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        )
    ''', (group_id, group_id, MAX_MESSAGES_PER_GROUP))
    
    conn.commit()
    conn.close()

def get_unsummarized_messages(group_id, limit=1000):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, sender_id, sender_name, content, timestamp 
        FROM messages 
        WHERE group_id = ? AND is_summarized = 0 
        ORDER BY timestamp ASC 
        LIMIT ?
    ''', (group_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_recent_messages(group_id, limit=500):
    """
    获取最近 N 条消息，无论是否 summarized，用于滑动窗口总结。
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, sender_id, sender_name, content, timestamp 
        FROM messages 
        WHERE group_id = ?
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (group_id, limit))
    rows = cursor.fetchall()
    conn.close()
    
    # 因为是用 DESC 获取的，需要反转为时间正序
    return list(reversed(rows))

def mark_messages_as_summarized(message_ids):
    if not message_ids:
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    placeholders = ','.join(['?'] * len(message_ids))
    cursor.execute(f'''
        UPDATE messages 
        SET is_summarized = 1 
        WHERE id IN ({placeholders})
    ''', message_ids)
    conn.commit()
    conn.close()

def get_unprofiled_messages(group_id, limit=300):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, sender_id, sender_name, content, timestamp 
        FROM messages 
        WHERE group_id = ? AND is_profiled = 0 
        ORDER BY timestamp ASC 
        LIMIT ?
    ''', (group_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows

def count_unprofiled_messages(group_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(id) FROM messages WHERE group_id = ? AND is_profiled = 0
    ''', (group_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def mark_messages_as_profiled(message_ids):
    if not message_ids:
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    placeholders = ','.join(['?'] * len(message_ids))
    cursor.execute(f'''
        UPDATE messages 
        SET is_profiled = 1 
        WHERE id IN ({placeholders})
    ''', message_ids)
    conn.commit()
    conn.close()

def insert_group_event(group_id, summary, start_time, end_time):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO group_events (group_id, summary, start_time, end_time, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (group_id, summary, start_time, end_time, int(datetime.now().timestamp())))
    conn.commit()
    conn.close()
