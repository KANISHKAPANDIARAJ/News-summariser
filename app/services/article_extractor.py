"""Article extraction pipeline with SSRF validation, multi-strategy scrapers, and metadata extraction."""

from typing import Dict, Any, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

from app.utils.validators import is_safe_url
from app.utils.logger import logger
from app.services.text_cleaner import TextCleaner

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

class ArticleExtractionError(Exception):
    """Custom exception raised when article content cannot be extracted."""
    pass

class ArticleExtractor:
    def __init__(self, timeout: int = 15, max_bytes: int = 2 * 1024 * 1024):
        self.timeout = timeout
        self.max_bytes = max_bytes

    def extract(self, url: str) -> Dict[str, Any]:
        """Runs the multi-strategy extraction pipeline on a target URL."""
        # 1. Anti-SSRF and URL validation
        safe, err_msg = is_safe_url(url)
        if not safe:
            logger.warning(f"SSRF or invalid URL blocked: {url} -> {err_msg}")
            raise ArticleExtractionError(f"URL security validation failed: {err_msg}")

        # 2. Try Primary Strategy: Newspaper3k (if installed and working)
        result = self._try_newspaper(url)
        if result and len(result.get("text", "").strip()) >= 50:
            logger.info(f"Article extracted successfully via Newspaper3k from: {url}")
            return result

        # 3. Fallback Strategy: Requests + BeautifulSoup semantic extraction
        logger.info(f"Trying fallback BeautifulSoup semantic extractor for: {url}")
        result = self._try_beautifulsoup(url)
        if result and len(result.get("text", "").strip()) >= 50:
            logger.info(f"Article extracted successfully via BeautifulSoup fallback from: {url}")
            return result

        raise ArticleExtractionError("Unable to extract sufficient article text from the provided URL.")

    def _try_newspaper(self, url: str) -> Optional[Dict[str, Any]]:
        try:
            from newspaper import Article
            article = Article(url, request_timeout=self.timeout)
            article.download()
            article.parse()

            if not article.text or len(article.text.strip()) < 50:
                return None

            return {
                "title": article.title or "",
                "author": ", ".join(article.authors) if article.authors else "",
                "publisher": urlparse(url).netloc,
                "published_date": str(article.publish_date) if article.publish_date else "",
                "url": url,
                "image_url": article.top_image or "",
                "text": article.text,
                "language": article.meta_lang or TextCleaner.detect_language(article.text),
            }
        except Exception as e:
            logger.warning(f"Newspaper3k extraction failed for {url}: {e}")
            return None

    def _try_beautifulsoup(self, url: str) -> Optional[Dict[str, Any]]:
        try:
            resp = requests.get(
                url,
                headers=DEFAULT_HEADERS,
                timeout=self.timeout,
                stream=True,
                allow_redirects=True,
            )
            resp.raise_for_status()

            # Check content length
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                logger.warning(f"Non-HTML content type for {url}: {content_type}")
                return None

            content = resp.raw.read(self.max_bytes, decode_content=True).decode("utf-8", errors="replace")
            soup = BeautifulSoup(content, "html.parser")

            # Extract Title
            title = ""
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = og_title["content"].strip()
            elif soup.title and soup.title.string:
                title = soup.title.string.strip()
            elif soup.h1:
                title = soup.h1.get_text().strip()

            # Extract Author
            author = ""
            meta_author = soup.find("meta", attrs={"name": "author"})
            if meta_author and meta_author.get("content"):
                author = meta_author["content"].strip()

            # Extract Publisher
            publisher = urlparse(url).netloc
            og_site = soup.find("meta", property="og:site_name")
            if og_site and og_site.get("content"):
                publisher = og_site["content"].strip()

            # Extract Published Date
            published_date = ""
            meta_time = soup.find("meta", property="article:published_time") or soup.find("time")
            if meta_time:
                published_date = meta_time.get("content") or meta_time.get("datetime") or meta_time.get_text()

            # Extract Image
            image_url = ""
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                image_url = og_image["content"].strip()

            # Extract Body Text: Strip scripts, styles, nav, footer
            for tag in soup(["script", "style", "nav", "footer", "aside", "header", "noscript"]):
                tag.decompose()

            # Target main article container if available
            article_body = soup.find("article") or soup.find("main") or soup.find(class_=re.compile(r"article|content|post-body|entry-content", re.I))
            source_elem = article_body if article_body else soup.body

            if not source_elem:
                return None

            paragraphs = [p.get_text().strip() for p in source_elem.find_all("p") if len(p.get_text().strip()) > 30]
            raw_text = "\n\n".join(paragraphs)

            if len(raw_text.strip()) < 50:
                return None

            return {
                "title": title,
                "author": author,
                "publisher": publisher,
                "published_date": published_date,
                "url": url,
                "image_url": image_url,
                "text": raw_text,
                "language": TextCleaner.detect_language(raw_text),
            }
        except Exception as e:
            logger.error(f"BeautifulSoup extraction error for {url}: {e}")
            return None
