import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

# Database path in var/ directory
DB_PATH = "var/database.db"

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    os.makedirs("var", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize all database tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Prompts table - store prompt definitions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompts (
                id TEXT PRIMARY KEY,
                purpose TEXT NOT NULL,
                name TEXT NOT NULL,
                template TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                user_id TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. Active prompts table - track which prompt is active per user/purpose
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_prompts (
                user_id TEXT NOT NULL,
                purpose TEXT NOT NULL,
                prompt_id TEXT NOT NULL,
                activated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, purpose),
                FOREIGN KEY (prompt_id) REFERENCES prompts(id)
            )
        ''')

        # 3. Predictions table - log all prediction requests/responses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                user_id TEXT NOT NULL,
                purpose TEXT NOT NULL,
                provider TEXT NOT NULL,
                prompt_id TEXT,
                latency_ms REAL
            )
        ''')

        # 4. Logs table - application logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                level TEXT NOT NULL,
                logger_name TEXT NOT NULL,
                message TEXT NOT NULL
            )
        ''')

        conn.commit()

# ============= PREDICTIONS LOGGING =============

def log_prediction(
    prompt: str,
    response: str,
    user_id: str,
    purpose: str,
    provider: str,
    prompt_id: str = "",
    latency_ms: float = 0.0
):
    """Log a prediction request/response"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO predictions (prompt, response, timestamp, user_id, purpose, provider, prompt_id, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (prompt, response, datetime.now(), user_id, purpose, provider, prompt_id, latency_ms))
        conn.commit()

def get_predictions(limit: int = 10, user_id: str = "", purpose: str = ""):
    """Get prediction history with optional filtering"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM predictions WHERE 1=1"
        params = []

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if purpose:
            query += " AND purpose = ?"
            params.append(purpose)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return cursor.fetchall()

# ============= APPLICATION LOGS =============

def log_to_db(level: str, logger_name: str, message: str):
    """Log an application event to database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO logs (timestamp, level, logger_name, message)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now(), level, logger_name, message))
        conn.commit()

def get_logs(limit: int = 100, level: str = ""):
    """Get application logs with optional level filtering"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        if level:
            cursor.execute('''
                SELECT * FROM logs
                WHERE level = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (level, limit))
        else:
            cursor.execute('''
                SELECT * FROM logs
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))

        return cursor.fetchall()

