import os
import re
import time
import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from houses.models import House

logger = logging.getLogger(__name__)

VALID_ORIENTATIONS = {"东", "南", "西", "北", "东南", "西南", "东北", "西北"}
VALID_DECORATIONS = {"毛坯", "简装", "精装", "豪装"}
VALID_PROPERTY_TYPES = {"住宅", "公寓", "别墅", "商住", "其他"}

CAPTCHA_KEYWORDS = ["滑块", "slider", "人机验证", "请完成验证"]


class LianjiaSpider:
    """Crawl Xi'an Gaoling District house data from lianjia.com via Selenium.

    Key: lianjia renders listings via client-side JS templates, so we must
    use Selenium's find_elements on the rendered DOM, not parse page_source.
    """

    BASE_URL = "https://xa.lianjia.com/ershoufang/gaoling/pg{page}/"
    DEBUG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "crawl_debug")

    # CSS selectors for the rendered DOM
    LIST_CONTAINER = "ul.sellListContent"
    LIST_ITEM = "ul.sellListContent li.clear"
    POSITION_INFO = ".positionInfo"
    HOUSE_INFO = ".houseInfo"
    TOTAL_PRICE = ".totalPrice"
    UNIT_PRICE = ".unitPrice"

    def __init__(self, max_pages=15, delay=2, headless=True):
        self.max_pages = max_pages
        self.delay = delay
        self.headless = headless
        self.driver = None
        self.stats = {
            "pages_fetched": 0,
            "items_parsed": 0,
            "items_saved": 0,
            "items_skipped": 0,
            "errors": 0,
        }

    def _init_driver(self):
        """Initialize Chrome WebDriver."""
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        )
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--lang=zh-CN")

        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )

    def _wait_for_login(self, timeout=120):
        """Wait for user to complete login."""
        self.stdout_write(
            ">>> LOGIN REQUIRED! <<<\n"
            ">>> Please login (scan QR code or enter credentials) in the browser window. <<<\n"
            f">>> Waiting up to {timeout}s..."
        )
        start = time.time()
        while time.time() - start < timeout:
            if "login" not in self.driver.current_url:
                self.stdout_write("Login successful!")
                return True
            time.sleep(2)
        self.stdout_write("Login timeout. Attempting to continue anyway...")
        return False

    def _wait_for_captcha(self, timeout=120):
        """Wait for user to manually solve captcha."""
        self.stdout_write(
            ">>> CAPTCHA DETECTED! <<<\n"
            ">>> Please solve it in the browser window. <<<\n"
            f">>> Waiting up to {timeout}s..."
        )
        start = time.time()
        while time.time() - start < timeout:
            page_text = self.driver.page_source.lower()
            if not any(kw in page_text for kw in CAPTCHA_KEYWORDS):
                self.stdout_write("Captcha solved! Continuing...")
                return True
            time.sleep(2)
        self.stdout_write("Captcha timeout. Attempting to continue anyway...")
        return False

    def _save_debug_html(self, page_num):
        """Save rendered page HTML for debugging."""
        os.makedirs(self.DEBUG_DIR, exist_ok=True)
        path = os.path.join(self.DEBUG_DIR, f"page_{page_num}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)
        self.stdout_write(f"  Debug HTML saved to {path}")

    def _wait_for_listings(self, timeout=15):
        """Wait for the listing container to render in the DOM."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.LIST_CONTAINER))
            )
            # Extra wait for items to render
            time.sleep(2)
            return True
        except Exception:
            return False

    def run(self):
        """Main entry: open browser, handle login, then crawl pages."""
        self._init_driver()

        try:
            self.stdout_write("Opening lianjia...")
            self.driver.get("https://xa.lianjia.com/ershoufang/gaoling/")
            time.sleep(3)

            if "login" in self.driver.current_url:
                self._wait_for_login(timeout=120)

            # Wait for first page to render
            if not self._wait_for_listings(timeout=15):
                # Maybe captcha?
                page_text = self.driver.page_source.lower()
                if any(kw in page_text for kw in CAPTCHA_KEYWORDS):
                    self._wait_for_captcha(timeout=120)

            for page in range(1, self.max_pages + 1):
                self.stdout_write(f"Fetching page {page}...")
                url = self.BASE_URL.format(page=page)
                self.driver.get(url)
                time.sleep(2)

                if "login" in self.driver.current_url:
                    self.stdout_write("Redirected to login, waiting for re-login...")
                    self._wait_for_login(timeout=120)
                    self.driver.get(url)
                    time.sleep(3)

                # Wait for JS-rendered listings to appear
                listings_ready = self._wait_for_listings(timeout=15)

                if not listings_ready:
                    page_text = self.driver.page_source.lower()
                    if any(kw in page_text for kw in CAPTCHA_KEYWORDS):
                        self._wait_for_captcha(timeout=120)
                        listings_ready = self._wait_for_listings(timeout=15)

                if not listings_ready:
                    self._save_debug_html(page)
                    self.stdout_write(
                        f"  No listings rendered on page {page}. "
                        f"Check crawl_debug/page_{page}.html"
                    )
                    if page == 1:
                        self.stdout_write("  First page empty, stopping.")
                        break
                    break

                items = self._parse_rendered_page()

                if not items:
                    self._save_debug_html(page)
                    self.stdout_write(
                        f"  Listings found but 0 items parsed on page {page}. "
                        f"Check crawl_debug/page_{page}.html"
                    )
                    if page == 1:
                        break
                    break

                for item in items:
                    self.save_to_db(item)

                self.stats["pages_fetched"] += 1
                self.stdout_write(
                    f"  Page {page}: {len(items)} items, "
                    f"saved={self.stats['items_saved']}, "
                    f"skipped={self.stats['items_skipped']}"
                )

                if page < self.max_pages:
                    time.sleep(self.delay)

        finally:
            if self.driver:
                self.driver.quit()

        return self.stats

    def _parse_rendered_page(self):
        """Parse listings from the rendered DOM using Selenium find_elements."""
        try:
            li_elements = self.driver.find_elements(
                By.CSS_SELECTOR, self.LIST_ITEM
            )
        except Exception:
            return []

        if not li_elements:
            # Try alternative selectors
            for alt in ["li.LOGVIEWDATA", "li.clear", ".sellListContent li"]:
                try:
                    li_elements = self.driver.find_elements(By.CSS_SELECTOR, alt)
                    if li_elements:
                        break
                except Exception:
                    continue

        items = []
        for li in li_elements:
            try:
                item = self._parse_house_element(li)
                if item:
                    items.append(item)
            except Exception as e:
                logger.warning(f"Failed to parse item: {e}")
                self.stats["errors"] += 1

        return items

    def _parse_house_element(self, li):
        """Parse a single house <li> element from rendered DOM."""
        item = {}

        # Position info (community name, address)
        try:
            pos_el = li.find_element(By.CSS_SELECTOR, self.POSITION_INFO)
            links = pos_el.find_elements(By.TAG_NAME, "a")
            if links:
                community = links[0].text.strip()
                item["name"] = community
                item["district"] = community
            item["address"] = pos_el.text.strip()
        except Exception:
            pass

        # House info (rooms, area, orientation, decoration, floor, year)
        try:
            info_el = li.find_element(By.CSS_SELECTOR, self.HOUSE_INFO)
            info_text = info_el.text.strip()
            self._parse_house_info(info_text, item)
        except Exception:
            pass

        # Total price
        try:
            price_el = li.find_element(By.CSS_SELECTOR, self.TOTAL_PRICE)
            price_text = price_el.text.strip()
            price_match = re.search(r"([\d.]+)", price_text)
            if price_match:
                item["price"] = float(price_match.group(1)) * 10000
        except Exception:
            pass

        # Unit price
        try:
            unit_el = li.find_element(By.CSS_SELECTOR, self.UNIT_PRICE)
            unit_text = unit_el.text.strip()
            unit_match = re.search(r"([\d.]+)", unit_text)
            if unit_match:
                item["price_per_sqm"] = float(unit_match.group(1))
        except Exception:
            pass

        required = ["name", "district", "area", "rooms", "year", "price"]
        if not all(item.get(k) for k in required):
            return None

        item.setdefault("halls", 1)
        item.setdefault("bathrooms", 1)
        item.setdefault("floor", 1)
        item.setdefault("total_floors", 6)
        item.setdefault("orientation", "南")
        item.setdefault("decoration", "精装")
        item.setdefault("property_type", "住宅")
        item.setdefault("address", "")
        item.setdefault("lat", None)
        item.setdefault("lng", None)

        return item

    def _parse_house_info(self, info_text, item):
        """Parse houseInfo string like '3室2厅 | 89.23平米 | 南 | 精装 | 中楼层/共18层 | 2015年建'"""
        parts = [p.strip() for p in info_text.split("|")]

        for part in parts:
            room_match = re.match(r"(\d+)室(\d+)厅(?: (\d+)卫)?", part)
            if room_match:
                item["rooms"] = int(room_match.group(1))
                item["halls"] = int(room_match.group(2))
                item["bathrooms"] = int(room_match.group(3) or 1)
                continue

            area_match = re.search(r"([\d.]+)平米", part)
            if area_match:
                item["area"] = float(area_match.group(1))
                continue

            orientation = part.strip()
            if orientation in VALID_ORIENTATIONS:
                item["orientation"] = orientation
                continue

            decoration = part.strip()
            if decoration in VALID_DECORATIONS:
                item["decoration"] = decoration
                continue

            floor_match = re.search(r"共(\d+)层", part)
            if floor_match:
                item["total_floors"] = int(floor_match.group(1))
                tf = item["total_floors"]
                if "低楼层" in part:
                    item["floor"] = max(1, tf // 3)
                elif "中楼层" in part:
                    item["floor"] = tf // 2
                elif "高楼层" in part:
                    item["floor"] = min(tf, tf * 2 // 3 + 1)
                else:
                    item["floor"] = tf // 2
                continue

            year_match = re.search(r"(\d{4})年", part)
            if year_match:
                item["year"] = int(year_match.group(1))
                continue

    def save_to_db(self, item):
        """Save parsed item to database with dedup."""
        self.stats["items_parsed"] += 1
        try:
            _, created = House.objects.get_or_create(
                name=item["name"],
                area=item["area"],
                floor=item["floor"],
                price=item["price"],
                defaults={
                    "address": item.get("address", ""),
                    "district": item["district"],
                    "property_type": item.get("property_type", "住宅"),
                    "rooms": item["rooms"],
                    "halls": item.get("halls", 1),
                    "bathrooms": item.get("bathrooms", 1),
                    "total_floors": item.get("total_floors", 6),
                    "year": item["year"],
                    "orientation": item.get("orientation", "南"),
                    "decoration": item.get("decoration", "精装"),
                    "lat": item.get("lat"),
                    "lng": item.get("lng"),
                    "status": "available",
                },
            )
            if created:
                self.stats["items_saved"] += 1
            else:
                self.stats["items_skipped"] += 1
        except Exception as e:
            logger.error(f"Failed to save {item.get('name')}: {e}")
            self.stats["errors"] += 1

    def stdout_write(self, msg):
        """Override in management command to use self.stdout."""
        print(msg)
