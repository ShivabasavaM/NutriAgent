import sqlite3
import os

DB_PATH = "nutriagent.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    access_token TEXT,
    refresh_token TEXT,
    expires_at REAL,
    height REAL,
    Weight REAL,
    goal TEXT,
    daily_calorie_target INTEGER
    )
    """)

    cursor.execute("INSERT or IGNORE INTO users (id) VALUES (1)")
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def update_token(access_token, refresh_token, expires_at):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE users 
    SET access_token = ?, refresh_token = ?, expires_at = ?
    where id = 1
    """, (access_token, refresh_token, expires_at))
    conn.commit()
    conn.close()

def get_tokens():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""SELECT access_token, refresh_token, expires_at FROM users where id=1""")
    row = cursor.fetchone()
    conn.close()

    if row and row[0]:
        return {
            "access_token" : row[0],
            "refresh_token" : row[1],
            "expires_at" : row[2]
        }
    return None


