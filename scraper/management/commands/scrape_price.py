import os
import time
from django.core.management.base import BaseCommand
from playwright.sync_api import sync_playwright
from scraper.models import Product

def scrape_single_product_price(product_id: str, headless: bool = True, max_retries: int = 5, logger=None):
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    def log(msg, style_func=None):
        if logger:
            if style_func:
                logger.stdout.write(style_func(msg))
            else:
                logger.stdout.write(msg)
        else:
            print(msg)

    target_url = f"https://demo.inelabteamdev.com/product/{product_id}"
    last_error = None

    for attempt in range(1, max_retries + 1):
        log(f"\n[Attempt {attempt}/{max_retries}] Opening product page: {target_url}")

        with sync_playwright() as p:
            browser = None
            for launch_opts in [
                {'headless': headless},
                {'headless': headless, 'channel': 'msedge'},
                {'headless': headless, 'channel': 'chrome'},
            ]:
                try:
                    browser = p.chromium.launch(**launch_opts)
                    break
                except Exception:
                    continue

            if not browser:
                raise RuntimeError("Could not launch Playwright browser.")

            context = browser.new_context()
            page = context.new_page()

            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

                # Dismiss cookie banner if present
                try:
                    cookie_btn = page.query_selector('button[aria-label="Accept cookies"]')
                    if cookie_btn:
                        cookie_btn.click()
                except Exception:
                    pass

                # 1. Find Reveal Price button
                button_selector = 'button[aria-label="Reveal price"]'
                page.wait_for_selector(button_selector, timeout=15000)
                btn = page.query_selector(button_selector)

                if not btn:
                    raise ValueError("Reveal Price button not found on page.")

                # 2. Simulate human mouse interaction on price card if button is disabled
                if btn.get_attribute('disabled') is not None:
                    price_block = page.query_selector('.price-block')
                    if price_block:
                        box = price_block.bounding_box()
                        if box:
                            for x_off in range(0, int(box['width']), 15):
                                page.mouse.move(box['x'] + x_off, box['y'] + 10)
                                time.sleep(0.04)

                # Wait until disabled attribute is removed from this button
                page.wait_for_selector('button[aria-label="Reveal price"]:not([disabled])', timeout=20000)

                # 3. Click the button.btn.btn-primary once it becomes enabled
                enabled_btn = page.query_selector('button[aria-label="Reveal price"]:not([disabled])')
                enabled_btn.click(force=True)

                # 4. Find the price container: .price-main
                page.wait_for_selector(".price-main", timeout=15000)
                price_main = page.query_selector(".price-main")

                if not price_main:
                    raise ValueError(".price-main container not found after clicking.")

                # Inside .price-main, select the first div
                first_div = price_main.query_selector("div")
                if not first_div:
                    raise ValueError("First div inside .price-main not found.")

                # Inside that first div, select all span elements
                spans = first_div.query_selector_all("span")

                # Read text of each span, keep only spans containing digits 0-9
                extracted_digits = []
                for s in spans:
                    text = s.inner_text().strip()
                    if text.isdigit():
                        extracted_digits.append(text)
                    else:
                        digits = [c for c in text if c.isdigit()]
                        if digits:
                            extracted_digits.extend(digits)

                # Join remaining digits together
                joined_value = "".join(extracted_digits)

                if not joined_value:
                    raise ValueError(f"No numeric price digits found for product {product_id}")

                # Convert joined value to integer
                price_integer = int(joined_value)

                # Also fetch h1 title if available
                h1_el = page.query_selector("h1")
                page_title = h1_el.inner_text().strip() if h1_el else ""

                defaults = {'price': price_integer}
                if page_title:
                    defaults['product_title'] = page_title

                # Store that integer as product price in scraper_product table
                product, created = Product.objects.update_or_create(
                    product_id=product_id,
                    defaults=defaults
                )

                action = "Created" if created else "Updated"
                log(f"[SUCCESS] {action} Product {product_id} with Price: {price_integer}")
                # Exit immediately when successfully fetched
                return price_integer

            except Exception as e:
                last_error = e
                log(f"[Attempt {attempt}/{max_retries} Failed] {e}")
                if attempt < max_retries:
                    log(f"Retrying in 2 seconds (Attempt {attempt+1}/{max_retries})...")
                    time.sleep(2)
            finally:
                browser.close()

    # If all 5 retries fail
    raise RuntimeError(f"Failed to scrape price for product {product_id} after {max_retries} attempts. Last error: {last_error}")


class Command(BaseCommand):
    help = "Scrape and store price for a product_id by revealing price on https://demo.inelabteamdev.com/product/{product_id}"

    def add_arguments(self, parser):
        parser.add_argument(
            'product_id',
            type=str,
            help='Product ID to scrape price for (e.g. 002)'
        )
        parser.add_argument(
            '--headful',
            action='store_true',
            help='Run browser in visible mode'
        )

    def handle(self, *args, **options):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        product_id = options['product_id'].strip()
        headless = not options['headful']

        self.stdout.write(self.style.SUCCESS(f"Starting Price Scraper for Product ID: {product_id}"))

        try:
            price = scrape_single_product_price(product_id, headless=headless, logger=self)
            self.stdout.write(self.style.SUCCESS(f"\nSUCCESS! Stored Price: {price} for product {product_id} in scraper_product table."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nFailed to scrape price for product {product_id}: {e}"))
