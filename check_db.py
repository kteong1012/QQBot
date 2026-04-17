import sqlite3

def check_messages(user_id):
    conn = sqlite3.connect('/home/carson/.openclaw/workspace/qq-robot/data/qq_messages.db')
    cursor = conn.cursor()
    cursor.execute("SELECT sender_id, sender_name, content FROM messages WHERE sender_id=?", (user_id,))
    rows = cursor.fetchall()
    
    print(f"Total messages for {user_id}: {len(rows)}")
    if rows:
        print(f"Sample data: {rows[0]}")
    conn.close()

check_messages("536466383")
