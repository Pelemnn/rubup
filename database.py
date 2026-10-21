import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "stats.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS income_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            comments_count INTEGER,
            amount_rub REAL,
            report_num TEXT,
            source TEXT DEFAULT 'auto'
        )
    ''')
    conn.commit()
    conn.close()

def add_report(comments_count: int, amount_rub: float, report_num: str = "", source: str = "auto"):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO income_reports (timestamp, comments_count, amount_rub, report_num, source)
        VALUES (?, ?, ?, ?, ?)
    ''', (datetime.utcnow(), comments_count, amount_rub, report_num, source))
    conn.commit()
    conn.close()

def get_stats(days: int = None) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    if days:
        since_date = datetime.utcnow() - timedelta(days=days)
        cur.execute('''
            SELECT COUNT(*), SUM(comments_count), SUM(amount_rub)
            FROM income_reports
            WHERE timestamp >= ?
        ''', (since_date,))
    else:
        cur.execute('''
            SELECT COUNT(*), SUM(comments_count), SUM(amount_rub)
            FROM income_reports
        ''')
        
    row = cur.fetchone()
    conn.close()
    
    reports_count = row[0] or 0
    total_comments = row[1] or 0
    total_rub = row[2] or 0.0
    
    return {
        "reports_count": reports_count,
        "total_comments": total_comments,
        "total_rub": round(total_rub, 2),
        "days": days
    }
