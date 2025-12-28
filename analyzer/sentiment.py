import pandas as pd
from textblob import TextBlob
from collections import Counter
import re
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsAnalyzer:
    """Haber metinleri için analiz yardımcıları"""

    def __init__(self):
        self.stop_words = {
            'this', 'that', 'with', 'from', 'have', 'been', 'more',
            'will', 'says', 'after', 'could', 'would', 'about', 'their',
            'said', 'also', 'when', 'where', 'what', 'which', 'there'
        }

    def analyze_sentiment(self, text: str) -> Dict[str, any]:
        """Metin için sentiment skoru ve etiketi döndürür"""
        if not text or not text.strip():
            return {'score': 0.0, 'label': 'Neutral', 'subjectivity': 0.0}

        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            if polarity > 0.1:
                label = 'Positive'
            elif polarity < -0.1:
                label = 'Negative'
            else:
                label = 'Neutral'

            return {
                'score': round(polarity, 3),
                'label': label,
                'subjectivity': round(subjectivity, 3)
            }
        except Exception as e:
            logger.error(f"Sentiment hatası: {e}")
            return {'score': 0.0, 'label': 'Neutral', 'subjectivity': 0.0}

    def analyze_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """DataFrame'e sentiment etiketi ekler"""
        if df.empty:
            return df

        df['sentiment_label'] = df['sentiment'].apply(
            lambda x: 'Positive' if x > 0.1 else ('Negative' if x < -0.1 else 'Neutral')
        )
        return df

    def extract_keywords(self, text: str, top_n: int = 10) -> List[Tuple[str, int]]:
        """Metinden sık geçen kelimeleri çıkarır"""
        if not text:
            return []

        words = re.findall(r'\b\w{4,}\b', text.lower())
        words = [w for w in words if w not in self.stop_words]

        return Counter(words).most_common(top_n)

    def get_trending_topics(self, df: pd.DataFrame, top_n: int = 20) -> List[Tuple[str, int]]:
        """Başlıklardan trend kelimeleri üretir"""
        if df.empty or 'title' not in df.columns:
            return []

        return self.extract_keywords(' '.join(df['title']), top_n)

    def sentiment_by_source(self, df: pd.DataFrame) -> pd.DataFrame:
        """Kaynak bazında sentiment istatistikleri"""
        if df.empty or 'source' not in df.columns:
            return pd.DataFrame()

        return df.groupby('source').agg({
            'sentiment': ['mean', 'std', 'count'],
            'sentiment_label': lambda x: x.value_counts().to_dict()
        }).round(3)

    def sentiment_over_time(self, df: pd.DataFrame) -> pd.DataFrame:
        """Zaman bazlı sentiment ortalamaları"""
        if df.empty or 'date' not in df.columns:
            return pd.DataFrame()

        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])

        if df.empty:
            return pd.DataFrame()

        df['day'] = df['date'].dt.date
        return df.groupby('day').agg(
            sentiment=('sentiment', 'mean'),
            article_count=('id', 'count')
        ).round(3)

    def get_sentiment_distribution(self, df: pd.DataFrame) -> Dict[str, int]:
        """Sentiment dağılımı"""
        if df.empty or 'sentiment_label' not in df.columns:
            return {'Positive': 0, 'Neutral': 0, 'Negative': 0}

        dist = df['sentiment_label'].value_counts().to_dict()
        for k in ['Positive', 'Neutral', 'Negative']:
            dist.setdefault(k, 0)

        return dist

    def get_summary_statistics(self, df: pd.DataFrame) -> Dict:
        """Genel özet bilgiler"""
        if df.empty:
            return {}

        return {
            'total_articles': len(df),
            'avg_sentiment': round(df['sentiment'].mean(), 3),
            'sources_count': df['source'].nunique(),
            'sentiment_distribution': self.get_sentiment_distribution(df)
        }

    def filter_by_sentiment(self, df: pd.DataFrame, sentiment_type: str) -> pd.DataFrame:
        """Sentiment tipine göre filtreleme"""
        if df.empty or 'sentiment_label' not in df.columns:
            return pd.DataFrame()

        return df[df['sentiment_label'] == sentiment_type].copy()

    def get_top_positive_news(self, df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        """En pozitif haberler"""
        return df.nlargest(n, 'sentiment') if not df.empty else pd.DataFrame()

    def get_top_negative_news(self, df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        """En negatif haberler"""
        return df.nsmallest(n, 'sentiment') if not df.empty else pd.DataFrame()