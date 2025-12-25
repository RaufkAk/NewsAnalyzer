import unittest
from unittest.mock import patch, Mock, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scraper.manager import NewsScraper


class TestNewsScraper(unittest.TestCase):
    """NewsScraper için temel testler"""

    def setUp(self):
        """Her test öncesi çalışır"""
        self.scraper = NewsScraper(max_workers=2)

    def test_scraper_init(self):
        """Scraper'ın doğru başlatıldığını kontrol et"""
        self.assertEqual(self.scraper.max_workers, 2)
        self.assertIsNotNone(self.scraper.headers)

    @patch('scraper.manager.BeautifulSoup')
    @patch('scraper.manager.requests.get')
    def test_scrape_bbc(self, mock_get, mock_soup):
        """BBC scraping testi"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html></html>'
        mock_get.return_value = mock_response

        # Mock BeautifulSoup
        mock_tag = Mock()
        mock_tag.get_text.return_value = "Breaking news about technology today"
        mock_tag.find_parent.return_value = Mock(get=lambda x: '/news/test')

        mock_soup_instance = Mock()
        mock_soup_instance.find_all.return_value = [mock_tag]
        mock_soup.return_value = mock_soup_instance

        articles = self.scraper.scrape_bbc()

        self.assertIsInstance(articles, list)

    @patch('scraper.manager.requests.get')
    def test_scrape_failure(self, mock_get):
        """HTTP hatası durumunda boş liste dönmeli"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        articles = self.scraper.scrape_bbc()
        self.assertEqual(len(articles), 0)

if __name__ == '__main__':
    unittest.main(verbosity=2)