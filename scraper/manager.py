import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from textblob import TextBlob
from typing import List
import logging
import random
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
        seen_titles = set()
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
                
                # Duplicate kontrolü
                if title in seen_titles:
                    continue
                seen_titles.add(title)
                
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
        seen_titles = set()
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
                
                # Duplicate kontrolü
                if title in seen_titles:
                    continue
                seen_titles.add(title)

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
        seen_titles = set()
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
                
                # Duplicate kontrolü
                if title in seen_titles:
                    continue
                seen_titles.add(title)

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
        seen_titles = set()
        try:
            logger.info("NPR'den haberler çekiliyor...")
            url = "https://www.npr.org/sections/news/"
            response = requests.get(url, headers=self.headers, timeout=15)

            if response.status_code != 200:
                logger.warning(f"NPR yanıt vermiyor: {response.status_code}")
                return articles

            soup = BeautifulSoup(response.content, 'html.parser')
            
            # NPR'ın yeni yapısına göre başlıkları bul
            headlines = soup.find_all('h2', class_='title')
            
            if not headlines:
                # Alternatif selectors
                headlines = soup.find_all('h3', class_='title')
            
            if not headlines:
                # Tüm h2'leri dene
                headlines = soup.find_all('h2', limit=50)

            for item in headlines[:50]:
                try:
                    title = item.get_text(strip=True)
                    
                    # Parent link'i bul
                    link = item.find_parent('a') or item.find('a')
                    url_path = link.get('href', '') if link else ''

                    if len(title) < 15 or len(title) > 250:
                        continue
                    
                    # Duplicate kontrolü
                    if title in seen_titles:
                        continue
                    seen_titles.add(title)

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

    def scrape_all(self, db_manager=None) -> List[News]:
        """
        Tüm kaynaklardan paralel olarak haber çek
        Threading kullanarak performansı artırır
        
        Args:
            db_manager: Database manager instance (duplicate kontrolü için)

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

        all_articles_by_source = []

        # ThreadPoolExecutor ile paralel çalıştır
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Tüm fonksiyonları submit et
            futures = [executor.submit(func) for func in scraping_functions]

            # Sonuçları kaynak bazında topla
            for future in futures:
                try:
                    articles = future.result(timeout=30)
                    if articles:
                        all_articles_by_source.append(articles)
                except Exception as e:
                    logger.error(f"Thread hatası: {e}")

        # Bugün database'de olan başlıkları al (duplicate kontrolü için)
        existing_titles = set()
        if db_manager:
            try:
                from datetime import date
                today = date.today()
                all_db_articles = db_manager.dbGetAllArticles(limit=10000)
                if not all_db_articles.empty:
                    # Bugünkü haberleri filtrele
                    today_articles = all_db_articles[
                        all_db_articles['date'].dt.date == today
                    ]
                    existing_titles = set(today_articles['title'].tolist())
                    logger.info(f"Bugün database'de {len(existing_titles)} haber var")
            except Exception as e:
                logger.warning(f"Database kontrolü yapılamadı: {e}")

        # Her kaynaktan yeni (duplicate olmayan) haberleri filtrele
        filtered_by_source = []
        for source_articles in all_articles_by_source:
            new_articles = [
                article for article in source_articles 
                if article.title not in existing_titles
            ]
            if new_articles:
                filtered_by_source.append(new_articles)
                logger.info(f"{source_articles[0].source}: {len(new_articles)} yeni haber")
            else:
                # Hiç yeni haber yoksa, orijinalden en az 1 tane al
                filtered_by_source.append(source_articles[:1])
                logger.info(f"{source_articles[0].source}: Yeni haber yok, 1 tane alındı")

        # Önce her kaynaktan en az 1 haber garantisi
        selected_articles: List[News] = []
        max_per_batch = 30
        
        # Her kaynaktan ilk haberi al
        for source_articles in filtered_by_source:
            if source_articles and len(selected_articles) < max_per_batch:
                selected_articles.append(source_articles[0])
        
        # Geri kalan haberleri round-robin ile ekle
        max_length = max(len(articles) for articles in filtered_by_source) if filtered_by_source else 0
        for i in range(1, max_length):  # 1'den başla çünkü 0. index zaten alındı
            for source_articles in filtered_by_source:
                if i < len(source_articles) and len(selected_articles) < max_per_batch:
                    selected_articles.append(source_articles[i])
        
        # Biraz karıştır ama her kaynaktan en az 1 haber garantisini koru
        guaranteed = selected_articles[:len(filtered_by_source)]
        rest = selected_articles[len(filtered_by_source):]
        random.shuffle(rest)
        selected_articles = guaranteed + rest
        
        logger.info(f"Toplam {len(selected_articles)} haber seçildi (her kaynaktan min 1)")
        return selected_articles