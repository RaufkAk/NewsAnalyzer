import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from textblob import TextBlob
from typing import List
import logging
from models.News import News

# Logging ayarla
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class NewsScraper:
    """Haber sitelerinden veri toplayan ana sınıf"""

    # Her kaynak için kategoriler
    BBC_CATEGORIES = [
        "world", "business", "technology", "health", "science_and_environment"
    ]
    CNN_CATEGORIES = [
        "world", "business", "africa", "asia", "europe", "middle-east", "us", "americas"
    ]
    ALJAZEERA_CATEGORIES = [
        "news", "economy", "opinion", "human-rights", "science-and-technology"
    ]
    NPR_CATEGORIES = [
        "world", "business", "science", "technology", "health"
    ]

    # Her kaynak için kategori indexi (Streamlit session_state ile tutulabilir)
    category_indices = {
        'bbc': 0,
        'cnn': 0,
        'aljazeera': 0,
        'npr': 0
    }

    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def get_next_category(self, source):
        # Sıradaki kategoriyi döndür ve indexi güncelle
        if source == 'bbc':
            idx = NewsScraper.category_indices['bbc']
            cat = NewsScraper.BBC_CATEGORIES[idx]
            NewsScraper.category_indices['bbc'] = (idx + 1) % len(NewsScraper.BBC_CATEGORIES)
            return cat
        elif source == 'cnn':
            idx = NewsScraper.category_indices['cnn']
            cat = NewsScraper.CNN_CATEGORIES[idx]
            NewsScraper.category_indices['cnn'] = (idx + 1) % len(NewsScraper.CNN_CATEGORIES)
            return cat
        elif source == 'aljazeera':
            idx = NewsScraper.category_indices['aljazeera']
            cat = NewsScraper.ALJAZEERA_CATEGORIES[idx]
            NewsScraper.category_indices['aljazeera'] = (idx + 1) % len(NewsScraper.ALJAZEERA_CATEGORIES)
            return cat
        elif source == 'npr':
            idx = NewsScraper.category_indices['npr']
            cat = NewsScraper.NPR_CATEGORIES[idx]
            NewsScraper.category_indices['npr'] = (idx + 1) % len(NewsScraper.NPR_CATEGORIES)
            return cat
        return None

    def scrape_bbc(self) -> List[News]:
        """BBC News'den kategori bazlı haber çek"""
        category = self.get_next_category('bbc')
        url = f"https://www.bbc.com/news/{category}"
        articles = []
        try:
            logger.info(f"BBC'den '{category}' kategorisinden haberler çekiliyor...")
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                logger.warning(f"BBC yanıt vermiyor: {response.status_code}")
                return articles
            soup = BeautifulSoup(response.content, 'html.parser')
            headline_tags = soup.find_all(['h2', 'h3'], limit=150)
            for tag in headline_tags:
                title = tag.get_text(strip=True)
                if len(title) < 20 or len(title) > 200:
                    continue
                sentiment = TextBlob(title).sentiment.polarity
                link_tag = tag.find_parent('a')
                url_path = ''
                if link_tag and link_tag.get('href'):
                    href = link_tag['href']
                    if href.startswith('http'):
                        url_path = href
                    elif href.startswith('/'):
                        url_path = 'https://www.bbc.com' + href
                try:
                    article = News(
                        title=title,
                        url=url_path,
                        source='BBC News',
                        sentiment=sentiment,
                        date=datetime.now()
                    )
                    articles.append(article)
                except ValueError as e:
                    logger.warning(f"BBC article validation hatası: {e}")
                    continue
            logger.info(f"BBC: {len(articles)} haber çekildi ({category})")
        except Exception as e:
            logger.error(f"BBC hatası: {e}")
        return articles

    def scrape_cnn(self) -> List[News]:
        """CNN'den haber çek"""
        articles = []
        try:
            logger.info("CNN'den haberler çekiliyor...")
            url = "https://edition.cnn.com/world"
            response = requests.get(url, headers=self.headers, timeout=15)

            if response.status_code != 200:
                logger.warning(f"CNN yanıt vermiyor: {response.status_code}")
                return articles

            soup = BeautifulSoup(response.content, 'html.parser')
            headlines = soup.find_all('span', class_='container__headline-text')

            for headline in headlines[:50]:
                title = headline.get_text(strip=True)

                if len(title) < 20:
                    continue

                sentiment = TextBlob(title).sentiment.polarity

                parent = headline.find_parent('a')
                url_path = ''
                if parent and parent.get('href'):
                    href = parent['href']
                    if href.startswith('http'):
                        url_path = href
                    elif href.startswith('/'):
                        url_path = 'https://edition.cnn.com' + href

                # News dataclass oluştur
                try:
                    article = News(
                        title=title,
                        url=url_path,
                        source='CNN',
                        sentiment=sentiment,
                        date=datetime.now()
                    )
                    articles.append(article)
                except ValueError as e:
                    logger.warning(f"CNN article validation hatası: {e}")
                    continue

            logger.info(f"CNN: {len(articles)} haber çekildi")

        except Exception as e:
            logger.error(f"CNN hatası: {e}")

        return articles

    def scrape_aljazeera(self) -> List[News]:
        """Al Jazeera'dan haber çek"""
        articles = []
        try:
            logger.info("Al Jazeera'dan haberler çekiliyor...")
            url = "https://www.aljazeera.com/"
            response = requests.get(url, headers=self.headers, timeout=15)

            if response.status_code != 200:
                logger.warning(f"Al Jazeera yanıt vermiyor: {response.status_code}")
                return articles

            soup = BeautifulSoup(response.content, 'html.parser')
            all_links = soup.find_all('a', href=True)

            for link in all_links:
                title = link.get_text(strip=True)

                if len(title) < 20 or len(title) > 200:
                    continue

                # Navigation filtrele
                if any(skip in title.lower() for skip in ['skip to', 'home page', 'search', 'menu']):
                    continue

                sentiment = TextBlob(title).sentiment.polarity

                url_path = link.get('href', '')
                if url_path and not url_path.startswith('http'):
                    url_path = 'https://www.aljazeera.com' + url_path

                # News data class oluştur
                try:
                    article = News(
                        title=title,
                        url=url_path,
                        source='Al Jazeera',
                        sentiment=sentiment,
                        date=datetime.now()
                    )
                    articles.append(article)
                except ValueError as e:
                    logger.warning(f"Al Jazeera article validation hatası: {e}")
                    continue

                if len(articles) >= 25:
                    break

            logger.info(f"Al Jazeera: {len(articles)} haber çekildi")

        except Exception as e:
            logger.error(f"Al Jazeera hatası: {e}")

        return articles

    def scrape_npr(self) -> List[News]:
        """NPR'den haber çek"""
        articles = []
        try:
            logger.info("NPR'den haberler çekiliyor...")
            url = "https://www.npr.org/sections/world/"
            response = requests.get(url, headers=self.headers, timeout=15)

            if response.status_code != 200:
                logger.warning(f"NPR yanıt vermiyor: {response.status_code}")
                return articles

            soup = BeautifulSoup(response.content, 'html.parser')
            article_links = soup.find_all('a', {'href': lambda x: x and '/article/' in x})

            if not article_links:
                article_links = soup.find_all('h2', limit=60)

            for item in article_links[:50]:
                try:
                    if item.name == 'a':
                        title_elem = item.find(['h2', 'h3', 'span'])
                        title = title_elem.get_text(strip=True) if title_elem else item.get_text(strip=True)
                        url_path = item.get('href', '')
                    else:
                        title = item.get_text(strip=True)
                        link = item.find_parent('a')
                        url_path = link.get('href', '') if link else ''

                    if len(title) < 15 or len(title) > 250:
                        continue

                    sentiment = TextBlob(title).sentiment.polarity

                    if url_path and not url_path.startswith('http'):
                        url_path = 'https://www.npr.org' + url_path

                    # News data class oluştur
                    try:
                        article = News(
                            title=title,
                            url=url_path,
                            source='NPR',
                            sentiment=sentiment,
                            date=datetime.now()
                        )
                        articles.append(article)
                    except ValueError as e:
                        logger.warning(f"NPR article validation hatası: {e}")
                        continue

                except Exception as item_error:
                    logger.warning(f"NPR item parse hatası: {item_error}")
                    continue

            logger.info(f"NPR: {len(articles)} haber çekildi")

        except Exception as e:
            logger.error(f"NPR hatası: {e}")

        return articles

    def scrape_all(self) -> List[News]:
        """
        Tüm kaynaklardan paralel olarak haber çek
        Threading kullanarak performansı artırır

        Returns:
            List[News]: Toplanan tüm haberler (News nesneleri)
        """
        logger.info("Paralel scraping başlatılıyor...")

        # Tüm scraping fonksiyonları
        scraping_functions = [
            self.scrape_bbc,
            self.scrape_cnn,
            self.scrape_aljazeera,
            self.scrape_npr
        ]

        all_articles: List[News] = []

        # ThreadPoolExecutor ile paralel çalıştır
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Tüm fonksiyonları submit et
            futures = [executor.submit(func) for func in scraping_functions]

            # Sonuçları topla
            for future in futures:
                try:
                    articles = future.result(timeout=30)
                    all_articles.extend(articles)
                except Exception as e:
                    logger.error(f"Thread hatası: {e}")

        # Maksimum 30 haber döndür
        if len(all_articles) > 30:
            all_articles = all_articles[:30]
        logger.info(f"Toplam {len(all_articles)} haber çekildi (max 30)")
        return all_articles