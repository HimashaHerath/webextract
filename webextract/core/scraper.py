"""Web scraping functionality using Playwright with improved content detection."""

import logging
import re
import time
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, NavigableString, Tag
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from ..config.settings import settings
from .models import ExtractedContent

logger = logging.getLogger(__name__)


class WebScraper:
    """Modern web scraper with intelligent content detection."""

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
        """Setup Playwright browser with optimized settings."""
        if not self._playwright:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins",
                    "--disable-site-isolation-trials",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-blink-features=AutomationControlled",
                ],
            )

            # Create context with stealth settings
            self._context = self._browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=settings.USER_AGENTS[0],
                java_script_enabled=True,
                accept_downloads=False,
                ignore_https_errors=True,
                locale="en-US",
            )

            # Add stealth JavaScript
            self._context.add_init_script(
                """
                // Override navigator properties
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Add chrome object
                window.chrome = { runtime: {} };
                
                // Fix permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """
            )

    def _cleanup_browser(self):
        """Cleanup browser resources."""
        for obj in [self._context, self._browser, self._playwright]:
            if obj:
                try:
                    obj.close() if hasattr(obj, "close") else obj.stop()
                except Exception:
                    pass

        self._context = self._browser = self._playwright = None

    def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < settings.REQUEST_DELAY:
            time.sleep(settings.REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()

    def scrape(self, url: str) -> Optional[ExtractedContent]:
        """Main scraping method with intelligent extraction."""
        logger.info(f"Starting scrape of: {url}")

        try:
            # Fetch the page
            html = self._fetch_page_content(url)
            if not html:
                return None

            # Parse and extract
            soup = BeautifulSoup(html, "lxml")

            # Clean the HTML
            self._remove_unwanted_elements(soup)

            # Extract components
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            main_content = self._extract_main_content(soup)

            if not main_content or len(main_content.strip()) < 50:
                logger.warning(f"Insufficient content extracted from {url}")
                # Try alternative extraction
                main_content = self._fallback_content_extraction(soup)

            links = self._extract_important_links(soup, url)
            metadata = self._extract_metadata(soup)

            return ExtractedContent(
                title=title,
                description=description,
                main_content=main_content,
                links=links,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Scraping failed for {url}: {e}")
            return None

    def _fetch_page_content(self, url: str) -> Optional[str]:
        """Fetch page content with retries and error handling."""
        self._apply_rate_limit()

        if not self._browser:
            self._setup_browser()

        page = None
        for attempt in range(settings.RETRY_ATTEMPTS):
            try:
                page = self._context.new_page()

                # Configure page
                page.set_extra_http_headers(
                    {
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Cache-Control": "no-cache",
                        "Pragma": "no-cache",
                    }
                )

                # Navigate with appropriate timeout
                timeout = settings.REQUEST_TIMEOUT * 1000
                response = page.goto(
                    url, wait_until="domcontentloaded", timeout=timeout
                )

                if not response:
                    logger.warning(f"No response from {url}")
                    continue

                # Check status
                if response.status >= 400:
                    logger.warning(f"HTTP {response.status} for {url}")
                    if response.status == 429:  # Rate limited
                        time.sleep(settings.RETRY_DELAY * (attempt + 1))
                        continue
                    elif response.status >= 500:  # Server error
                        if attempt < settings.RETRY_ATTEMPTS - 1:
                            time.sleep(settings.RETRY_DELAY)
                            continue
                    else:  # Client error
                        return None

                # Wait for content to load
                try:
                    # Wait for body to have content
                    page.wait_for_function(
                        "document.body && document.body.innerText.length > 100",
                        timeout=5000,
                    )
                except:
                    # Fallback wait
                    page.wait_for_timeout(2000)

                # Get content
                content = page.content()

                if len(content) > 100:
                    logger.info(f"Successfully fetched {len(content)} bytes from {url}")
                    return content

            except PlaywrightTimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
                if attempt < settings.RETRY_ATTEMPTS - 1:
                    time.sleep(settings.RETRY_DELAY)

            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                if attempt < settings.RETRY_ATTEMPTS - 1:
                    time.sleep(settings.RETRY_DELAY)

            finally:
                if page:
                    try:
                        page.close()
                    except:
                        pass

        return None

    def _remove_unwanted_elements(self, soup: BeautifulSoup):
        """Remove unwanted elements from the page."""
        # Remove script and style elements
        for element in soup.find_all(["script", "style", "noscript"]):
            element.decompose()

        # Remove common non-content elements
        unwanted_selectors = [
            "nav",
            "header",
            "footer",
            "aside",
            ".nav",
            ".navigation",
            ".header",
            ".footer",
            ".menu",
            ".sidebar",
            ".advertisement",
            ".ads",
            ".popup",
            ".modal",
            ".cookie-notice",
            ".banner",
            "#nav",
            "#navigation",
            "#header",
            "#footer",
            "#menu",
            "#sidebar",
            "#advertisement",
            "#ads",
            '[role="navigation"]',
            '[role="banner"]',
            '[aria-label="advertisement"]',
        ]

        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title using multiple strategies."""
        # Try standard title tag
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            return title_tag.string.strip()

        # Try Open Graph title
        og_title = soup.find("meta", {"property": "og:title"})
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        # Try Twitter title
        twitter_title = soup.find("meta", {"name": "twitter:title"})
        if twitter_title and twitter_title.get("content"):
            return twitter_title["content"].strip()

        # Try H1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page description."""
        # Meta description
        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc and meta_desc.get("content"):
            return meta_desc["content"].strip()

        # OG description
        og_desc = soup.find("meta", {"property": "og:description"})
        if og_desc and og_desc.get("content"):
            return og_desc["content"].strip()

        # Twitter description
        twitter_desc = soup.find("meta", {"name": "twitter:description"})
        if twitter_desc and twitter_desc.get("content"):
            return twitter_desc["content"].strip()

        return None

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content using multiple strategies."""
        # Strategy 1: Look for semantic HTML5 elements
        for tag in ["main", "article"]:
            elements = soup.find_all(tag)
            if elements:
                # Get the largest one
                largest = max(elements, key=lambda x: len(x.get_text(strip=True)))
                content = self._extract_text_from_element(largest)
                if len(content) > 100:
                    return content

        # Strategy 2: Look for content-indicating classes/IDs
        content_indicators = [
            "content",
            "main-content",
            "article-content",
            "post-content",
            "entry-content",
            "story-content",
            "body-content",
            "text-content",
            "page-content",
            "blog-content",
            "news-content",
        ]

        for indicator in content_indicators:
            # Try class
            elements = soup.find_all(class_=re.compile(indicator, re.I))
            if not elements:
                # Try ID
                element = soup.find(id=re.compile(indicator, re.I))
                if element:
                    elements = [element]

            if elements:
                largest = max(elements, key=lambda x: len(x.get_text(strip=True)))
                content = self._extract_text_from_element(largest)
                if len(content) > 100:
                    return content

        # Strategy 3: Find the element with the most paragraph tags
        all_containers = soup.find_all(["div", "section", "article"])
        if all_containers:

            def paragraph_score(element):
                paragraphs = element.find_all("p")
                return sum(len(p.get_text(strip=True)) for p in paragraphs)

            best_container = max(all_containers, key=paragraph_score)
            content = self._extract_text_from_element(best_container)
            if len(content) > 100:
                return content

        # Strategy 4: Fallback to body
        return self._fallback_content_extraction(soup)

    def _extract_text_from_element(self, element: Tag) -> str:
        """Extract clean text from an element."""
        if not element:
            return ""

        # Clone the element to avoid modifying the original
        element_copy = element

        # Remove any remaining unwanted elements within
        for tag in ["script", "style", "nav", "aside"]:
            for unwanted in element_copy.find_all(tag):
                unwanted.decompose()

        # Extract text with proper spacing
        text_parts = []
        for elem in element_copy.descendants:
            if isinstance(elem, NavigableString):
                text = elem.strip()
                if text:
                    text_parts.append(text)
            elif elem.name in [
                "p",
                "div",
                "section",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "li",
                "br",
            ]:
                text_parts.append("\n")

        # Join and clean
        text = " ".join(text_parts)
        text = re.sub(r"\n\s*\n+", "\n\n", text)  # Multiple newlines to double
        text = re.sub(r" +", " ", text)  # Multiple spaces to single
        text = text.strip()

        # Limit length
        if len(text) > settings.MAX_CONTENT_LENGTH:
            text = text[: settings.MAX_CONTENT_LENGTH] + "..."

        return text

    def _fallback_content_extraction(self, soup: BeautifulSoup) -> str:
        """Fallback content extraction when specific strategies fail."""
        # Get all text from body
        body = soup.find("body") or soup

        # Remove any remaining unwanted elements
        for tag in ["script", "style", "nav", "header", "footer"]:
            for elem in body.find_all(tag):
                elem.decompose()

        # Get all paragraphs and significant text elements
        text_elements = body.find_all(
            ["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "td", "blockquote"]
        )

        text_parts = []
        for elem in text_elements:
            text = elem.get_text(strip=True)
            if len(text) > 20:  # Only include substantial text
                text_parts.append(text)

        content = "\n".join(text_parts)

        # If still too short, get all text
        if len(content) < 100:
            content = body.get_text(separator=" ", strip=True)

        # Clean and limit
        content = re.sub(r"\s+", " ", content).strip()
        if len(content) > settings.MAX_CONTENT_LENGTH:
            content = content[: settings.MAX_CONTENT_LENGTH] + "..."

        return content

    def _extract_important_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract important links from the page."""
        links = []
        seen_urls = set()

        # Find all links
        for link in soup.find_all("a", href=True):
            href = link.get("href", "").strip()
            if not href:
                continue

            # Make absolute
            absolute_url = urljoin(base_url, href)

            # Skip if already seen
            if absolute_url in seen_urls:
                continue

            # Validate link
            if self._is_important_link(absolute_url, link):
                links.append(absolute_url)
                seen_urls.add(absolute_url)

                if len(links) >= 20:  # Limit number of links
                    break

        return links

    def _is_important_link(self, url: str, link_element: Tag) -> bool:
        """Determine if a link is important enough to include."""
        # Skip non-HTTP URLs
        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            return False

        # Skip media files and documents
        skip_extensions = {
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
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".zip",
            ".rar",
            ".tar",
            ".gz",
            ".exe",
            ".dmg",
        }

        url_lower = url.lower()
        for ext in skip_extensions:
            if url_lower.endswith(ext):
                return False

        # Skip common utility links
        skip_patterns = [
            "/login",
            "/signin",
            "/signup",
            "/register",
            "/logout",
            "/signout",
            "/password",
            "/forgot",
            "/terms",
            "/privacy",
            "/cookie",
            "/legal",
            "javascript:",
            "mailto:",
            "tel:",
            "#",
        ]

        for pattern in skip_patterns:
            if pattern in url_lower:
                return False

        # Prefer links with meaningful text
        link_text = link_element.get_text(strip=True)
        if link_text and len(link_text) > 3:
            return True

        # Check for important rel attributes
        rel = link_element.get("rel", [])
        if isinstance(rel, str):
            rel = [rel]

        important_rels = {"author", "canonical", "next", "prev"}
        if any(r in important_rels for r in rel):
            return True

        return False

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract comprehensive metadata."""
        metadata = {}

        # Standard meta tags
        meta_mappings = {
            "author": "author",
            "keywords": "keywords",
            "viewport": "viewport",
            "robots": "robots",
            "generator": "generator",
            "published_time": "published_time",
            "modified_time": "modified_time",
        }

        for name, key in meta_mappings.items():
            meta = soup.find("meta", {"name": name})
            if meta and meta.get("content"):
                metadata[key] = meta["content"]

        # Open Graph tags
        for og_tag in soup.find_all("meta", {"property": re.compile(r"^og:")}):
            if og_tag.get("content"):
                prop_name = og_tag["property"].replace("og:", "og_")
                metadata[prop_name] = og_tag["content"]

        # Twitter Card tags
        for twitter_tag in soup.find_all("meta", {"name": re.compile(r"^twitter:")}):
            if twitter_tag.get("content"):
                name = twitter_tag["name"].replace("twitter:", "twitter_")
                metadata[name] = twitter_tag["content"]

        # Schema.org JSON-LD
        json_ld = soup.find("script", {"type": "application/ld+json"})
        if json_ld and json_ld.string:
            try:
                import json

                schema_data = json.loads(json_ld.string)
                metadata["schema_org"] = schema_data
            except:
                pass

        # Canonical URL
        canonical = soup.find("link", {"rel": "canonical"})
        if canonical and canonical.get("href"):
            metadata["canonical_url"] = canonical["href"]

        return metadata
