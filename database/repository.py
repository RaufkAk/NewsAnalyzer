import os
import sqlite3
import pandas as pd
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Optional


class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = os.path.join(os.path.dirname(__file__), "news.db")

        self.initializeDatabase()

    @contextmanager
    def dbConnection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initializeDatabase(self):
        with self.dbConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE,
                    source TEXT NOT NULL,
                    sentiment REAL,
                    date TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source ON articles(source)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON articles(date)")

    # ---------------- INSERT ----------------

    def dbInsertArticle(self, article) -> Optional[int]:
        data = article.dictConverter() if hasattr(article, "dictConverter") else article

        with self.dbConnection() as conn:
            cursor = conn.cursor()

            if data.get("url"):
                cursor.execute(
                    "SELECT id FROM articles WHERE url = ?", (data["url"],)
                )
                if cursor.fetchone():
                    return None

            cursor.execute("""
                INSERT INTO articles (title, url, source, sentiment, date)
                VALUES (?, ?, ?, ?, ?)
            """, (
                data["title"],
                data["url"],
                data["source"],
                data["sentiment"],
                data.get("date", datetime.now())
            ))

            return cursor.lastrowid

    def dbInsertArticlesBulk(self, articles: List) -> Dict[str, int]:
        result = {"saved": 0, "duplicate": 0}

        for article in articles:
            if self.dbInsertArticle(article):
                result["saved"] += 1
            else:
                result["duplicate"] += 1

        return result

    # ---------------- SELECT ----------------

    def dbGetAllArticles(
        self, source: Optional[str] = None, limit: int = 1000
    ) -> pd.DataFrame:
        with self.dbConnection() as conn:
            query = "SELECT * FROM articles"
            params = []

            if source:
                query += " WHERE source = ?"
                params.append(source)

            query += " ORDER BY date DESC LIMIT ?"
            params.append(limit)

            df = pd.read_sql_query(query, conn, params=params)

            if not df.empty:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")

            return df

    def dbGetArticleById(self, article_id: int) -> Optional[Dict]:
        with self.dbConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ---------------- UPDATE ----------------

    def dbUpdateArticle(self, article_id: int, updates: Dict) -> bool:
        with self.dbConnection() as conn:
            cursor = conn.cursor()

            fields = ", ".join([f"{k} = ?" for k in updates])
            values = list(updates.values()) + [article_id]

            cursor.execute(
                f"UPDATE articles SET {fields} WHERE id = ?", values
            )
            return True

    # ---------------- DELETE ----------------

    def dbDeleteArticle(self, article_id: int) -> bool:
        with self.dbConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM articles WHERE id = ?", (article_id,))
            return True

    def dbDeleteAllArticles(self) -> bool:
        with self.dbConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM articles")
            return True

    # ---------------- EXTRA ----------------

    def dbSearchArticles(self, keyword: str, limit: int = 50) -> pd.DataFrame:
        with self.dbConnection() as conn:
            query = """
                SELECT * FROM articles
                WHERE title LIKE ?
                ORDER BY date DESC
                LIMIT ?
            """
            df = pd.read_sql_query(
                query, conn, params=(f"%{keyword}%", limit)
            )

            if not df.empty:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")

            return df

    def dbGetStatistics(self) -> Dict:
        with self.dbConnection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM articles")
            total = cursor.fetchone()[0]

            cursor.execute("""
                SELECT source, COUNT(*)
                FROM articles
                GROUP BY source
            """)
            sources = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT AVG(sentiment) FROM articles")
            avg = cursor.fetchone()[0] or 0

            return {
                "total_articles": total,
                "sources": sources,
                "avg_sentiment": round(avg, 3)
            }