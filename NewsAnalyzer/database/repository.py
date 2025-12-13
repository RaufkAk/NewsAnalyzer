import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:

    def __init__(self, db_path='news.db'):
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE,
                    source TEXT NOT NULL,
                    sentiment REAL,
                    date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON articles(source)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON articles(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sentiment ON articles(sentiment)')

            logger.info("Database initialized")

    def insert_article(self, title: str, url: str, source: str, sentiment: float, date: datetime) -> Optional[int]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT id FROM articles WHERE url = ?', (url,))
                if cursor.fetchone():
                    return None
                
                cursor.execute('''
                    INSERT INTO articles (title, url, source, sentiment, date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (title, url, source, sentiment, date))
                
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            return None

    def get_all_articles(self) -> pd.DataFrame:
        with self.get_connection() as conn:
            df = pd.read_sql_query("SELECT * FROM articles ORDER BY date DESC", conn)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            return df

    def get_statistics(self) -> Dict:
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as total FROM articles")
            total = cursor.fetchone()['total']

            cursor.execute("SELECT source, COUNT(*) as count FROM articles GROUP BY source")
            sources = {row['source']: row['count'] for row in cursor.fetchall()}

            cursor.execute("SELECT AVG(sentiment) as avg_sentiment FROM articles")
            avg_sentiment = cursor.fetchone()['avg_sentiment'] or 0

            return {
                'total_articles': total,
                'sources': sources,
                'avg_sentiment': round(avg_sentiment, 3)
            }


if __name__ == "__main__":
    db = DatabaseManager('test_news.db')
    
    test_id = db.insert_article(
        title='Test Article',
        url='https://example.com/test',
        source='Test Source',
        sentiment=0.5,
        date=datetime.now()
    )
    
    print(f"Inserted article with ID: {test_id}")
    
    stats = db.get_statistics()
    print(f"Statistics: {stats}")
    
    df = db.get_all_articles()
    print(f"Total articles: {len(df)}")