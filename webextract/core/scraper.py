"""Web scraping functionality using Playwright."""

import logging
import random
import time
from typing import List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from ..config.settings import settings
from .models import ExtractedContent

logger = logging.getLogger(__name__)


class WebScraper:
    """Modern web scraper using Playwright with error handling and rate limiting."""

    def __init__(self):
        self.last_request_time = 0
        self._playwright = None
        self._browser = None
        self._context = None

    def __enter__(self):
        self._setup_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup_browser()

    def _setup_browser(self):
        """Setup Playwright browser with stealth configuration."""
        if not self._playwright:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-extensions",
                    "--disable-plugins",
                    "--disable-images",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--disable-features=TranslateUI",
                    "--disable-ipc-flooding-protection",
                ],
            )

            # Create a browser context with additional stealth settings
            self._context = self._browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=random.choice(settings.USER_AGENTS),
                java_script_enabled=True,
                accept_downloads=False,
                ignore_https_errors=True,
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                },
            )

            # Add stealth scripts
            self._context.add_init_script(
                """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                window.chrome = {
                    runtime: {},
                };

                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });

                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
            """
            )

    def _cleanup_browser(self):
        """Cleanup Playwright resources."""
        if self._context:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None

        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    def _rate_limit(self):
        """Implement rate limiting."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < settings.REQUEST_DELAY:
            sleep_time = settings.REQUEST_DELAY - time_since_last_request
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL with robust error handling."""
        self._rate_limit()

        if not self._browser:
            self._setup_browser()

        for attempt in range(settings.RETRY_ATTEMPTS):
            page = None
            try:
                page = self._context.new_page()

                # Add random delay between attempts
                if attempt > 0:
                    delay = random.uniform(1, 3) * attempt
                    time.sleep(delay)

                # Set viewport and headers for this specific page
                headers = settings.get_headers()
                page.set_extra_http_headers(headers)

                logger.info(
                    f"Fetching {url} (attempt {attempt + 1}/{settings.RETRY_ATTEMPTS})"
                )

                # Set longer timeout for first attempt, shorter for retries
                timeout = (
                    settings.REQUEST_TIMEOUT * 1000
                    if attempt == 0
                    else (settings.REQUEST_TIMEOUT // 2) * 1000
                )

                # Navigate to page
                response = page.goto(
                    url, wait_until="domcontentloaded", timeout=timeout
                )

                if not response:
                    logger.warning(f"No response received for {url}")
                    if attempt < settings.RETRY_ATTEMPTS - 1:
                        continue
                    return None

                status_code = response.status
                logger.debug(f"Response status: {status_code} for {url}")

                # Handle specific HTTP status codes
                if status_code == 403:
                    logger.warning(f"Access forbidden (403) for {url}")
                    if attempt < settings.RETRY_ATTEMPTS - 1:
                        # Try with different user agent and longer delay
                        self._context.set_extra_http_headers(
                            {"User-Agent": random.choice(settings.USER_AGENTS)}
                        )
                        continue
                    else:
                        logger.error(
                            f"Persistent 403 error for {url} - site may block automated access"
                        )
                        return None

                elif status_code == 429:
                    wait_time = settings.RETRY_DELAY * (2**attempt)
                    logger.warning(
                        f"Rate limited (429) for {url}, waiting {wait_time}s"
                    )
                    if attempt < settings.RETRY_ATTEMPTS - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Persistent rate limiting for {url}")
                        return None

                elif 400 <= status_code < 500:
                    logger.error(f"Client error {status_code} for {url}")
                    return None

                elif status_code >= 500:
                    logger.warning(f"Server error {status_code} for {url}")
                    if attempt < settings.RETRY_ATTEMPTS - 1:
                        time.sleep(settings.RETRY_DELAY * (attempt + 1))
                        continue
                    else:
                        logger.error(f"Persistent server error for {url}")
                        return None

                # Check content type
                content_type = response.headers.get("content-type", "").lower()
                if "text/html" not in content_type:
                    logger.warning(f"Non-HTML content type for {url}: {content_type}")
                    if "json" in content_type or "xml" in content_type:
                        # Still try to process JSON/XML content
                        pass
                    elif (
                        "image" in content_type
                        or "video" in content_type
                        or "audio" in content_type
                    ):
                        logger.error(f"Cannot process media content from {url}")
                        return None

                # Wait for dynamic content with error handling
                try:
                    # Wait for network to be idle (no requests for 500ms)
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    # If network idle fails, just wait a bit
                    try:
                        page.wait_for_timeout(2000)
                    except Exception:
                        pass

                # Get page content
                html_content = page.content()

                # Validate content length
                if len(html_content.strip()) < 100:
                    logger.warning(
                        f"Very short content received from {url}: {len(html_content)} chars"
                    )
                    if attempt < settings.RETRY_ATTEMPTS - 1:
                        continue

                logger.debug(
                    f"Successfully fetched {len(html_content)} characters from {url}"
                )
                return html_content

            except PlaywrightTimeoutError as e:
                logger.warning(f"Timeout for {url} (attempt {attempt + 1}): {e}")
                if attempt < settings.RETRY_ATTEMPTS - 1:
                    time.sleep(settings.RETRY_DELAY)

            except Exception as e:
                error_msg = str(e).lower()

                if "net::err_connection_refused" in error_msg:
                    logger.error(f"Connection refused for {url}: {e}")
                    return None  # Don't retry connection refused

                elif "net::err_name_not_resolved" in error_msg:
                    logger.error(f"DNS resolution failed for {url}: {e}")
                    return None  # Don't retry DNS failures

                elif "net::err_internet_disconnected" in error_msg:
                    logger.error(f"No internet connection: {e}")
                    return None

                elif "net::err_timed_out" in error_msg or "timeout" in error_msg:
                    logger.warning(f"Network timeout for {url}: {e}")
                    if attempt < settings.RETRY_ATTEMPTS - 1:
                        time.sleep(settings.RETRY_DELAY * (attempt + 1))
                        continue

                elif "connection" in error_msg:
                    logger.warning(f"Connection error for {url}: {e}")
                    if attempt < settings.RETRY_ATTEMPTS - 1:
                        time.sleep(settings.RETRY_DELAY * (attempt + 1))
                        continue

                else:
                    logger.error(f"Unexpected error for {url}: {e}")
                    if attempt < settings.RETRY_ATTEMPTS - 1:
                        time.sleep(settings.RETRY_DELAY)
                        continue

            finally:
                if page:
                    try:
                        page.close()
                    except Exception:
                        pass

        logger.error(f"All attempts failed for {url}")
        return None

    def clean_html(self, html: str) -> BeautifulSoup:
        """Parse and clean HTML content."""
        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception as e:
            logger.warning(f"Failed to parse with lxml, trying html.parser: {e}")
            try:
                soup = BeautifulSoup(html, "html.parser")
            except Exception as e:
                logger.error(f"Failed to parse HTML: {e}")
                return BeautifulSoup("", "html.parser")

        # Remove unwanted elements
        unwanted_tags = [
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "noscript",
            "iframe",
        ]
        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()

        # Remove elements with certain classes/ids that are typically ads or navigation
        unwanted_selectors = [
            ".advertisement",
            ".ad",
            ".ads",
            ".banner",
            ".popup",
            ".modal",
            ".navigation",
            ".menu",
            ".sidebar",
            ".breadcrumb",
            ".pagination",
            "#advertisement",
            "#ad",
            "#ads",
            "#banner",
            "#popup",
            "#modal",
            "#navigation",
            "#menu",
            "#sidebar",
            "#breadcrumb",
            "#pagination",
        ]

        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()

        return soup

    def extract_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text from parsed HTML."""
        # Try multiple content selectors in order of preference
        content_selectors = [
            "main",
            "article",
            '[role="main"]',
            ".main-content",
            ".content",
            "#content",
            ".post",
            ".entry",
            ".article-body",
            ".story-body",
            ".entry-content",
            ".text-content",
            ".page-content",
            ".main-text",
        ]

        main_content = None
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                # Take the largest element if multiple found
                main_content = max(elements, key=lambda x: len(x.get_text()))
                break

        # Fallback to body if no main content found
        if not main_content:
            main_content = soup.find("body") or soup

        # Extract text and clean it
        text = main_content.get_text(separator=" ", strip=True)

        # Clean up extra whitespace
        import re

        text = re.sub(r"\s+", " ", text).strip()

        # Limit content length
        if len(text) > settings.MAX_CONTENT_LENGTH:
            text = text[: settings.MAX_CONTENT_LENGTH] + "..."
            logger.debug(
                f"Content truncated to {settings.MAX_CONTENT_LENGTH} characters"
            )

        return text

    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract important links from the page."""
        links = []

        try:
            for link in soup.find_all("a", href=True):
                href = link.get("href")
                if href:
                    absolute_url = urljoin(base_url, href)
                    if self._is_valid_link(absolute_url):
                        links.append(absolute_url)
        except Exception as e:
            logger.warning(f"Error extracting links: {e}")

        # Remove duplicates and limit count
        unique_links = list(
            dict.fromkeys(links)
        )  # Preserves order while removing duplicates
        return unique_links[:20]

    def _is_valid_link(self, url: str) -> bool:
        """Check if a link is valid and useful."""
        try:
            parsed = urlparse(url)

            if parsed.scheme not in ["http", "https"]:
                return False

            # Skip common non-content links
            skip_patterns = [
                "javascript:",
                "mailto:",
                "tel:",
                "ftp:",
                "#",
                "/admin",
                "/login",
                "/logout",
                "/register",
                "/signin",
                "/signup",
                ".pdf",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".ppt",
                ".pptx",
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".bmp",
                ".svg",
                ".webp",
                ".mp3",
                ".mp4",
                ".avi",
                ".mov",
                ".wmv",
                ".flv",
                ".css",
                ".js",
                ".ico",
                ".xml",
                ".json",
                ".rss",
            ]

            url_lower = url.lower()
            for pattern in skip_patterns:
                if pattern in url_lower:
                    return False

            # Skip very long URLs (likely tracking or session URLs)
            if len(url) > 200:
                return False

            return True
        except Exception:
            return False

    def extract_metadata(self, soup: BeautifulSoup) -> dict:
        """Extract page metadata."""
        metadata = {}

        try:
            # Meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                metadata["description"] = meta_desc.get("content", "")

            # Meta keywords
            meta_keywords = soup.find("meta", attrs={"name": "keywords"})
            if meta_keywords:
                metadata["keywords"] = meta_keywords.get("content", "")

            # Open Graph data
            og_tags = soup.find_all(
                "meta", attrs={"property": lambda x: x and x.startswith("og:")}
            )
            for tag in og_tags:
                prop = tag.get("property", "").replace("og:", "")
                content = tag.get("content", "")
                if prop and content:
                    metadata[f"og_{prop}"] = content

            # Twitter Card data
            twitter_tags = soup.find_all(
                "meta",
                attrs={"name": lambda x: x and x.startswith("twitter:")},
            )
            for tag in twitter_tags:
                name = tag.get("name", "").replace("twitter:", "")
                content = tag.get("content", "")
                if name and content:
                    metadata[f"twitter_{name}"] = content

            # Canonical URL
            canonical = soup.find("link", attrs={"rel": "canonical"})
            if canonical:
                metadata["canonical_url"] = canonical.get("href", "")

        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")

        return metadata

    def scrape(self, url: str) -> Optional[ExtractedContent]:
        """Main scraping method."""
        logger.info(f"Scraping: {url}")

        try:
            html = self.fetch_page(url)
            if not html:
                return None

            soup = self.clean_html(html)

            # Extract all content
            title = soup.find("title")
            title_text = title.get_text(strip=True) if title else None

            main_content = self.extract_text(soup)
            if not main_content or len(main_content.strip()) < 10:
                logger.warning(f"No meaningful content extracted from {url}")
                return None

            links = self.extract_links(soup, url)
            metadata = self.extract_metadata(soup)

            return ExtractedContent(
                title=title_text,
                description=metadata.get("description"),
                main_content=main_content,
                links=links,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Error during scraping of {url}: {e}")
            return None
