"""Improved web scraper with simplified extraction and robust resource management."""

import logging
import re
import time
from contextlib import contextmanager
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, NavigableString, Tag
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from ..config import get_default_config, get_http_headers
from .exceptions import (
    ContentTooLargeError,
    ErrorHandler,
    ExtractionError,
    InvalidURLError,
    ScrapingError,
)
from .models import ExtractedContent

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Simplified content extractor with two reliable strategies."""

    def __init__(self, config=None):
        self.config = config or get_default_config()

    def extract_content(self, soup: BeautifulSoup, url: str) -> ExtractedContent:
        """Extract content using simplified, reliable strategies."""
        # Strategy 1: Smart semantic extraction (80% of cases)
        main_content = self._extract_semantic_content(soup)

        # Strategy 2: Intelligent fallback for complex pages (20% of cases)
        if len(main_content) < 100:
            main_content = self._extract_content_blocks(soup)

        # Extract other metadata
        title = self._extract_title(soup)
        description = self._extract_description(soup)
        links = self._extract_links(soup, url)
        metadata = self._extract_metadata(soup)

        return ExtractedContent(
            url=url,
            title=title,
            description=description,
            main_content=main_content,
            links=links,
            metadata=metadata,
        )

    def _extract_semantic_content(self, soup: BeautifulSoup) -> str:
        """Strategy 1: Extract content using semantic HTML and content indicators."""
        candidates = []

        # 1. Semantic HTML5 elements (highest priority)
        for tag in ["main", "article"]:
            elements = soup.find_all(tag)
            for element in elements:
                content = self._clean_text_from_element(element)
                if len(content) > 50:
                    candidates.append((len(content), content))

        # 2. Content-indicating classes and IDs
        content_patterns = [
            r"content",
            r"main-content",
            r"article-content",
            r"post-content",
            r"entry-content",
            r"story",
            r"body-content",
        ]

        for pattern in content_patterns:
            # Check classes
            elements = soup.find_all(class_=re.compile(pattern, re.I))
            # Check IDs
            elements.extend(soup.find_all(id=re.compile(pattern, re.I)))

            for element in elements:
                content = self._clean_text_from_element(element)
                if len(content) > 50:
                    candidates.append((len(content), content))

        # Return the longest valid content
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]

        return ""

    def _extract_content_blocks(self, soup: BeautifulSoup) -> str:
        """Strategy 2: Extract content by analyzing text density in blocks."""
        # Find all container elements
        containers = soup.find_all(["div", "section", "article", "main"])

        scored_containers = []
        for container in containers:
            score = self._score_content_container(container)
            if score > 0:
                scored_containers.append((score, container))

        if scored_containers:
            # Get the highest scoring container
            scored_containers.sort(key=lambda x: x[0], reverse=True)
            best_container = scored_containers[0][1]
            return self._clean_text_from_element(best_container)

        # Last resort: extract from body with heavy filtering
        body = soup.find("body") or soup
        return self._extract_body_text(body)

    def _score_content_container(self, container: Tag) -> float:
        """Score a container based on content quality indicators."""
        if not container:
            return 0

        score = 0
        text = container.get_text(strip=True)

        # Base score: text length
        score += len(text) * 0.1

        # Bonus for paragraphs
        paragraphs = container.find_all("p")
        score += len(paragraphs) * 10

        # Bonus for headings
        headings = container.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        score += len(headings) * 5

        # Penalty for navigation/unwanted elements
        unwanted = container.find_all(["nav", "aside", "footer", "header"])
        score -= len(unwanted) * 20

        # Penalty for too many links (likely navigation)
        links = container.find_all("a")
        link_ratio = len(links) / max(len(text.split()), 1)
        if link_ratio > 0.1:  # More than 10% links
            score *= 0.5

        return max(0, score)

    def _clean_text_from_element(self, element: Tag) -> str:
        """Extract and clean text from an element."""
        if not element:
            return ""

        # Clone element to avoid modifying original
        element_copy = element.__copy__()

        # Remove unwanted elements
        unwanted_tags = [
            "script",
            "style",
            "noscript",
            "iframe",
            "embed",
            "object",
            "nav",
            "aside",
            "footer",
            "header",
            "advertisement",
            "ads",
        ]

        for tag in unwanted_tags:
            for elem in element_copy.find_all(tag):
                elem.decompose()

        # Remove elements with unwanted classes
        unwanted_classes = [
            "advertisement",
            "ads",
            "sidebar",
            "navigation",
            "nav",
            "footer",
            "header",
            "menu",
            "social",
            "share",
            "comment",
        ]

        for class_name in unwanted_classes:
            for elem in element_copy.find_all(class_=re.compile(class_name, re.I)):
                elem.decompose()

        # Extract text with proper spacing
        text = element_copy.get_text(separator=" ", strip=True)

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Check content length limits
        if len(text) > self.config.scraping.max_content_length:
            raise ContentTooLargeError(
                "Content exceeds maximum length limit",
                content_size=len(text),
                size_limit=self.config.scraping.max_content_length,
            )

        return text

    def _extract_body_text(self, body: Tag) -> str:
        """Extract text from body with aggressive filtering."""
        # Remove unwanted elements
        unwanted_tags = [
            "script",
            "style",
            "noscript",
            "iframe",
            "embed",
            "object",
            "nav",
            "aside",
            "footer",
            "header",
            "form",
        ]

        body_copy = body.__copy__()
        for tag in unwanted_tags:
            for elem in body_copy.find_all(tag):
                elem.decompose()

        # Get text from meaningful elements only
        meaningful_elements = body_copy.find_all(
            ["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "article", "section"]
        )

        text_parts = []
        for elem in meaningful_elements:
            text = elem.get_text(strip=True)
            if len(text) > 20:  # Only substantial text
                text_parts.append(text)

        content = " ".join(text_parts)

        # Clean up
        content = re.sub(r"\s+", " ", content).strip()

        # Check content length limits
        if len(content) > self.config.scraping.max_content_length:
            raise ContentTooLargeError(
                "Content exceeds maximum length limit",
                content_size=len(content),
                size_limit=self.config.scraping.max_content_length,
            )

        return content

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title using reliable methods."""
        # 1. Open Graph title
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        # 2. HTML title tag
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            return title_tag.string.strip()

        # 3. First h1 tag
        h1_tag = soup.find("h1")
        if h1_tag:
            return h1_tag.get_text(strip=True)

        return ""

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description."""
        # 1. Open Graph description
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            return og_desc["content"].strip()

        # 2. Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            return meta_desc["content"].strip()

        return ""

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract important links."""
        links = []
        for link in soup.find_all("a", href=True):
            href = link["href"].strip()
            if href.startswith("#") or href.startswith("javascript:"):
                continue

            full_url = urljoin(base_url, href)
            if full_url not in links:
                links.append(full_url)

            if len(links) >= 10:  # Limit number of links
                break

        return links

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict:
        """Extract basic metadata."""
        metadata = {}

        # Language
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            metadata["language"] = html_tag["lang"]

        # Viewport
        viewport = soup.find("meta", attrs={"name": "viewport"})
        if viewport and viewport.get("content"):
            metadata["viewport"] = viewport["content"]

        return metadata


class ResourceManager:
    """Robust resource management for Playwright."""

    def __init__(self, config=None):
        self.config = config or get_default_config()
        self.playwright = None
        self.browser = None
        self.context = None

    @contextmanager
    def browser_session(self):
        """Context manager for browser session with guaranteed cleanup."""
        try:
            self._setup_browser()
            yield self
        finally:
            self._cleanup_browser()

    def _setup_browser(self):
        """Setup browser with proper error handling."""
        try:
            if not self.playwright:
                self.playwright = sync_playwright().start()
                logger.debug("Playwright started")

            if not self.browser:
                self.browser = self.playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-accelerated-2d-canvas",
                        "--no-first-run",
                        "--no-zygote",
                        "--disable-gpu",
                        "--hide-scrollbars",
                        "--mute-audio",
                    ],
                )
                logger.debug("Browser launched")

            if not self.context:
                self.context = self.browser.new_context(
                    user_agent=self.config.scraping.user_agents[0],
                    viewport={"width": 1920, "height": 1080},
                )
                logger.debug("Browser context created")

        except Exception as e:
            logger.error(f"Failed to setup browser: {e}")
            self._cleanup_browser()  # Cleanup partial state
            raise ScrapingError(
                "Failed to initialize browser",
                original_error=e,
                suggestions=[
                    "Check if Playwright is properly installed",
                    "Ensure sufficient system resources are available",
                    "Try restarting the browser service",
                ],
            )

    def _cleanup_browser(self):
        """Cleanup browser resources with specific error handling."""
        errors = []

        # Cleanup context
        if self.context:
            try:
                self.context.close()
                logger.debug("Browser context closed")
            except Exception as e:
                errors.append(f"Context cleanup failed: {e}")
            finally:
                self.context = None

        # Cleanup browser
        if self.browser:
            try:
                self.browser.close()
                logger.debug("Browser closed")
            except Exception as e:
                errors.append(f"Browser cleanup failed: {e}")
            finally:
                self.browser = None

        # Cleanup playwright
        if self.playwright:
            try:
                self.playwright.stop()
                logger.debug("Playwright stopped")
            except Exception as e:
                errors.append(f"Playwright cleanup failed: {e}")
            finally:
                self.playwright = None

        # Log any cleanup errors but don't raise
        if errors:
            logger.warning(f"Cleanup errors: {'; '.join(errors)}")

    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch page HTML with proper error handling."""
        if not self.context:
            raise ScrapingError(
                "Browser not initialized",
                error_code="BROWSER_NOT_INITIALIZED",
                suggestions=[
                    "Use browser_session() context manager",
                    "Ensure proper browser setup before scraping",
                ],
            )

        page = None
        try:
            page = self.context.new_page()

            # Apply rate limiting
            self._apply_rate_limit()

            # Navigate with timeout
            timeout_ms = self.config.scraping.request_timeout * 1000
            page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")

            # Get HTML content
            html = page.content()
            logger.info(f"Successfully fetched {len(html)} characters from {url}")

            return html

        except PlaywrightTimeoutError as e:
            raise ScrapingError(
                f"Timeout while fetching page",
                url=url,
                timeout_duration=self.config.scraping.request_timeout,
                original_error=e,
            )
        except Exception as e:
            raise ErrorHandler.handle_with_context(
                "fetch_page",
                {"url": url},
                e,
                ["Check network connectivity", "Verify URL accessibility"],
            )
        finally:
            if page:
                try:
                    page.close()
                except Exception as e:
                    logger.warning(f"Error closing page: {e}")

    def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        if not hasattr(self, "_last_request_time"):
            self._last_request_time = 0

        elapsed = time.time() - self._last_request_time
        if elapsed < self.config.scraping.request_delay:
            time.sleep(self.config.scraping.request_delay - elapsed)
        self._last_request_time = time.time()


class ImprovedWebScraper:
    """Improved web scraper with simplified extraction and robust resource management."""

    def __init__(self, config=None):
        self.config = config or get_default_config()
        self.extractor = ContentExtractor(config)
        self.resource_manager = ResourceManager(config)

    def scrape(self, url: str) -> Optional[ExtractedContent]:
        """Main scraping method with simplified, reliable extraction."""
        logger.info(f"Starting scrape of: {url}")

        try:
            with self.resource_manager.browser_session():
                # Fetch page content
                html = self.resource_manager.fetch_page(url)
                if not html:
                    logger.warning(f"Failed to fetch content from {url}")
                    return None

                # Parse HTML
                soup = BeautifulSoup(html, "lxml")

                # Extract content using simplified strategies
                content = self.extractor.extract_content(soup, url)

                # Validate content
                if not content.main_content or len(content.main_content.strip()) < 50:
                    raise ExtractionError(
                        "Insufficient content extracted from page",
                        url=url,
                        extraction_stage="content_validation",
                        context={
                            "content_length": (
                                len(content.main_content) if content.main_content else 0
                            )
                        },
                    )

                logger.info(
                    f"Successfully extracted {len(content.main_content)} characters from {url}"
                )
                return content

        except (ScrapingError, ExtractionError, InvalidURLError):
            # Re-raise WebExtract errors as-is
            raise
        except Exception as e:
            # Convert unexpected errors to ScrapingError
            raise ErrorHandler.handle_with_context(
                "scrape",
                {"url": url},
                e,
                ["Check URL accessibility", "Verify network connectivity"],
            )

    def scrape_multiple(self, urls: List[str]) -> List[ExtractedContent]:
        """Scrape multiple URLs efficiently with shared browser session."""
        results = []

        try:
            with self.resource_manager.browser_session():
                for url in urls:
                    try:
                        html = self.resource_manager.fetch_page(url)
                        if html:
                            soup = BeautifulSoup(html, "lxml")
                            content = self.extractor.extract_content(soup, url)
                            if content and len(content.main_content.strip()) >= 50:
                                results.append(content)
                    except Exception as e:
                        logger.error(f"Failed to scrape {url}: {e}")
                        continue

        except Exception as e:
            logger.error(f"Batch scraping failed: {e}")

        return results


# Backward compatibility - replace the old WebScraper class
class WebScraper(ImprovedWebScraper):
    """Backward compatible WebScraper using improved implementation."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Resource cleanup is handled automatically by context managers
        pass
