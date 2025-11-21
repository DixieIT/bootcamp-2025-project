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
def add_prompt(id: str, purpose: str, name: str, template: str, user_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO prompts (id, purpose, name, template, user_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (id, purpose, name, template, user_id))
    conn.commit()
    conn.close()
def get_prompt_by_id(prompt_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM prompts WHERE id = ?', (prompt_id,))
    prompt = cursor.fetchone()
    conn.close()
    return prompt
def list_prompts(purpose: str | None = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if purpose:
        cursor.execute('SELECT * FROM prompts WHERE purpose = ?', (purpose,))
    else:
        cursor.execute('SELECT * FROM prompts')
    prompts = cursor.fetchall()
    conn.close()
    return prompts
def update_prompt_template(prompt_id: str, template: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE prompts
        SET template = ?
        WHERE id = ?
    ''', (template, prompt_id))
    conn.commit()
    conn.close()
def set_active_prompt(user_id: str, purpose: str, prompt_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_prompts (
            user_id TEXT,
            purpose TEXT,
            prompt_id TEXT,
            PRIMARY KEY (user_id, purpose)
        )
    ''')
    cursor.execute('''
        INSERT OR REPLACE INTO active_prompts (user_id, purpose, prompt_id)
        VALUES (?, ?, ?)
    ''', (user_id, purpose, prompt_id))
    conn.commit()
    conn.close()
def get_active_prompt(user_id: str, purpose: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT prompt_id FROM active_prompts
        WHERE user_id = ? AND purpose = ?
    ''', (user_id, purpose))
    row = cursor.fetchone()
    conn.close()
    if row:
        return get_prompt_by_id(row['prompt_id'])
    return None
