import pandas as pd
from textblob import TextBlob
from collections import Counter
import re
from typing import List, Dict, Tuple
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsAnalyzer:


    def __init__(self):
        # Comprehensive English stop words list
        self.stop_words = {
            'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren', "aren't",
            'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can', 
            'cannot', 'could', 'couldn', "couldn't", 'did', 'didn', "didn't", 'do', 'does', 'doesn', "doesn't", 'doing',
            'don', "don't", 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', 'hadn', "hadn't", 'has',
            'hasn', "hasn't", 'have', 'haven', "haven't", 'having', 'he', 'her', 'here', 'hers', 'herself', 'him',
            'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'isn', "isn't", 'it', "it's", 'its', 'itself',
            'let', 'me', 'more', 'most', 'mustn', "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on',
            'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', 'shan',
            "shan't", 'she', "she's", 'should', 'shouldn', "shouldn't", 'so', 'some', 'such', 'than', 'that', "that's",
            'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', "there's", 'these', 'they', "they'd",
            "they'll", "they're", "they've", 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very',
            'was', 'wasn', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', 'weren', "weren't", 'what',
            "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's", 'whom', 'why', "why's",
            'with', 'won', "won't", 'would', 'wouldn', "wouldn't", 'you', "you'd", "you'll", "you're", "you've",
            'your', 'yours', 'yourself', 'yourselves', 'will', 'says', 'said', 'citing'
        }

    def analyze_sentiment(self, text: str) -> Dict[str, any]:
        "Metin için sentiment skoru ve etiketi döndürür"
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

        # Remove special characters and digits, keep only letters
        clean_text = re.sub(r'[^a-zA-Z\s]', '', text.lower())
        
        # Split by whitespace
        words = clean_text.split()
        
        # Filter stop words and short words (length < 3)
        words = [w for w in words if w not in self.stop_words and len(w) > 3]

        return Counter(words).most_common(top_n)

    def get_trending_topics(self, df: pd.DataFrame, top_n: int = 20) -> List[Tuple[str, int]]:
        """Başlıklardan trend kelimeleri üretir"""
        if df.empty or 'title' not in df.columns:
            return []

        return self.extract_keywords(' '.join(df['title'].astype(str)), top_n)

    def sentiment_by_source(self, df: pd.DataFrame) -> pd.DataFrame:
        """Kaynak bazında sentiment istatistikleri"""
        if df.empty or 'source' not in df.columns:
            return pd.DataFrame()

        # Group by and aggregate
        stats = df.groupby('source').agg({
            'sentiment': ['mean', 'std', 'count']
        }).round(3)
        
        
        stats.columns = ['_'.join(col).strip() for col in stats.columns.values]
        stats = stats.reset_index()
        
       
        return stats

    def sentiment_over_time(self, df: pd.DataFrame) -> pd.DataFrame:
        """Zaman bazlı sentiment ortalamaları"""
        if df.empty or 'date' not in df.columns:
            return pd.DataFrame()

        df = df.copy()
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])

        if df.empty:
            return pd.DataFrame()

        df['day'] = df['date'].dt.date
        result = df.groupby('day').agg(
            avg_sentiment=('sentiment', 'mean'),
            count=('id', 'count') if 'id' in df.columns else ('sentiment', 'count')
        ).round(3).reset_index()
        
        return result

    def get_sentiment_distribution(self, df: pd.DataFrame) -> Dict[str, int]:
        """Sentiment dağılımı"""
        if df.empty or 'sentiment_label' not in df.columns:
            return {'Positive': 0, 'Neutral': 0, 'Negative': 0}

        dist = df['sentiment_label'].value_counts().to_dict()
        for k in ['Positive', 'Neutral', 'Negative']:
            dist.setdefault(k, 0)

        return dist

    def get_recent_article_count(self, df: pd.DataFrame, days: int = 1) -> int:
        """Son n gündeki haber sayısı"""
        if df.empty or 'date' not in df.columns:
            return 0
        
        # Ensure date type
        dates = pd.to_datetime(df['date'], errors='coerce')
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
        return len(dates[dates > cutoff])

    def get_summary_statistics(self, df: pd.DataFrame) -> Dict:
        """Genel özet bilgiler"""
        if df.empty:
            return {}

        dist = self.get_sentiment_distribution(df)
        total = len(df)
        positive_count = dist.get('Positive', 0)

        return {
            'total_articles': total,
            'avg_sentiment': round(df['sentiment'].mean(), 3),
            'sources_count': df['source'].nunique(),
            'sentiment_distribution': dist,
            'positive_pct': round((positive_count / total * 100), 1) if total > 0 else 0
        }

    def get_top_positive_news(self, df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        """En pozitif haberler"""
        if df.empty or 'sentiment' not in df.columns:
            return pd.DataFrame()
        return df.nlargest(n, 'sentiment')

    def get_top_negative_news(self, df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        """En negatif haberler"""
        if df.empty or 'sentiment' not in df.columns:
            return pd.DataFrame()
        return df.nsmallest(n, 'sentiment')