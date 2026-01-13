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

    CATEGORIES = {
        'bbc': [
            "world", "business", "technology", "health", "science_and_environment"
        ],
        'cnn': [
            "world", "business", "africa", "asia", "europe", "middle-east", "us", "americas"
        ],
        'aljazeera': [
            "news", "economy", "opinion", "human-rights", "science-and-technology"
        ],
        'npr': [
            "world", "business", "science", "technology", "health"
        ]
    }

    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # Initialize category indices for each source
        self.category_indices = {source: 0 for source in self.CATEGORIES}

    def get_next_category(self, source: str) -> str:
        """Sıradaki kategoriyi döndür ve indexi güncelle"""
        if source not in self.CATEGORIES:
            return None
            
        cats = self.CATEGORIES[source]
        idx = self.category_indices[source]
        category = cats[idx]
        self.category_indices[source] = (idx + 1) % len(cats)
        return category

    def _fetch_content(self, url: str):
        """Generic method to fetch and parse URL content"""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                logger.warning(f"URL yanıt vermiyor ({response.status_code}): {url}")
                return None
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Fetch hatası ({url}): {e}")
            return None

    def _create_article(self, title, url, source):
        """Helper to create News object with sentiment"""
        # Validate title length
        if len(title) < 15 or len(title) > 250:
            return None

        # Calculate sentiment immediately
        sentiment = TextBlob(title).sentiment.polarity
        
        # Ensure full URL
        if url and not url.startswith('http'):
            # Base URLs mapping
            base_urls = {
                'BBC News': 'https://www.bbc.com',
                'CNN': 'https://edition.cnn.com',
                'Al Jazeera': 'https://www.aljazeera.com',
                'NPR': 'https://www.npr.org'
            }
            if source in base_urls:
                url = base_urls[source] + url

        try:
            return News(
                title=title,
                url=url,
                source=source,
                sentiment=sentiment,
                date=datetime.now()
            )
        except ValueError:
            return None

    def scrape_bbc(self) -> List[News]:
        """BBC News'den kategori bazlı haber çek"""
        category = self.get_next_category('bbc')
        url = f"https://www.bbc.com/news/{category}"
        
        soup = self._fetch_content(url)
        if not soup:
            return []

        articles = []
        seen_titles = set()
        
        logger.info(f"BBC'den '{category}' kategorisinden haberler çekiliyor...")
        headline_tags = soup.find_all(['h2', 'h3'], limit=150)
        
        for tag in headline_tags:
            title = tag.get_text(strip=True)
            if title in seen_titles: continue
            
            link_tag = tag.find_parent('a')
            if not link_tag or not link_tag.get('href'): continue
            
            seen_titles.add(title)
            article = self._create_article(title, link_tag['href'], 'BBC News')
            if article:
                articles.append(article)
                
        logger.info(f"BBC: {len(articles)} haber çekildi ({category})")
        return articles

    def scrape_cnn(self) -> List[News]:
        """CNN'den haber çek"""
        url = "https://edition.cnn.com/world"
        soup = self._fetch_content(url)
        if not soup:
            return []

        articles = []
        seen_titles = set()
        
        logger.info("CNN'den haberler çekiliyor...")
        headlines = soup.find_all('span', class_='container__headline-text')

        for headline in headlines[:50]:
            title = headline.get_text(strip=True)
            if title in seen_titles: continue
            
            parent = headline.find_parent('a')
            href = parent['href'] if parent and parent.get('href') else ''
            
            seen_titles.add(title)
            article = self._create_article(title, href, 'CNN')
            if article:
                articles.append(article)
                
        logger.info(f"CNN: {len(articles)} haber çekildi")
        return articles

    def scrape_aljazeera(self) -> List[News]:
        """Al Jazeera'dan haber çek"""
        url = "https://www.aljazeera.com/"
        soup = self._fetch_content(url)
        if not soup:
            return []

        articles = []
        seen_titles = set()
        
        logger.info("Al Jazeera'dan haberler çekiliyor...")
        all_links = soup.find_all('a', href=True)

        for link in all_links:
            title = link.get_text(strip=True)
            
            if any(skip in title.lower() for skip in ['skip to', 'home page', 'search', 'menu']):
                continue
                
            if title in seen_titles: continue
            seen_titles.add(title)

            article = self._create_article(title, link.get('href'), 'Al Jazeera')
            if article:
                articles.append(article)

            if len(articles) >= 25:
                break

        logger.info(f"Al Jazeera: {len(articles)} haber çekildi")
        return articles

    def scrape_npr(self) -> List[News]:
        """NPR'den haber çek"""
        url = "https://www.npr.org/sections/news/"
        soup = self._fetch_content(url)
        if not soup:
            return []

        articles = []
        seen_titles = set()
        
        logger.info("NPR'den haberler çekiliyor...")
        
        headlines = soup.find_all('h2', class_='title') or \
                    soup.find_all('h3', class_='title') or \
                    soup.find_all('h2', limit=50)

        for item in headlines[:50]:
            title = item.get_text(strip=True)
            if title in seen_titles: continue
            
            link = item.find_parent('a') or item.find('a')
            href = link.get('href', '') if link else ''
            
            seen_titles.add(title)
            article = self._create_article(title, href, 'NPR')
            if article:
                articles.append(article)

        logger.info(f"NPR: {len(articles)} haber çekildi")
        return articles

    def scrape_all(self, db_manager=None) -> List[News]:
        """
        Tüm kaynaklardan paralel olarak haber çek
        Threading kullanarak performansı artırır
        
        Args:
            db_manager: Database manager instance

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

        # Bugün database'de olan başlıkları al
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

        # Her kaynaktan yeni  haberleri filtrele
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