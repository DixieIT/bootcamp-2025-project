import sqlite3

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            id TEXT PRIMARY KEY,
            purpose TEXT NOT NULL,
            name TEXT NOT NULL,
            template TEXT NOT NULL,
            user_id TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
def log_prompt_creation(id: str, purpose: str, name: str, template: str, user_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO prompts (id, purpose, name, template, user_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (id, purpose, name, template, user_id))
    conn.commit()
    conn.close()