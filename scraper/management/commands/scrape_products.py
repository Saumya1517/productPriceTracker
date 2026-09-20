import time
from django.core.management.base import BaseCommand
from playwright.sync_api import sync_playwright
from scraper.models import Product

class Command(BaseCommand):
    help = "Scrape products from https://demo.inelabteamdev.com/?page={page_no} and save to PostgreSQL"

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-page',
            type=int,
            default=1,
            help='Page number to start scraping from (default: 1)'
        )
        parser.add_argument(
            '--max-pages',
            type=int,
            default=None,
            help='Maximum number of pages to scrape (optional)'
        )
        parser.add_argument(
            '--headful',
            action='store_true',
            help='Run browser in headful mode (visible browser window)'
        )

    def handle(self, *args, **options):
        import os
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

        start_page = options['start_page']
        max_pages = options['max_pages']
        headless = not options['headful']

        self.stdout.write(self.style.SUCCESS("Starting Playwright product scraper..."))

        page_no = start_page
        total_scraped = 0
        consecutive_empty_pages = 0
        max_consecutive_empty = 2

        with sync_playwright() as p:
            browser = None
            # Try default Chromium, then system msedge, then system chrome
            for launch_opts in [
                {'headless': headless},
                {'headless': headless, 'channel': 'msedge'},
                {'headless': headless, 'channel': 'chrome'},
            ]:
                try:
                    browser = p.chromium.launch(**launch_opts)
                    channel_name = launch_opts.get('channel', 'bundled chromium')
                    self.stdout.write(self.style.SUCCESS(f"Successfully launched browser: {channel_name}"))
                    break
                except Exception as e:
                    continue

            if not browser:
                self.stdout.write(self.style.ERROR("Could not launch any browser (bundled chromium, msedge, or chrome)."))
                return

            context = browser.new_context()
            page = context.new_page()

            while True:
                if max_pages and (page_no - start_page + 1) > max_pages:
                    self.stdout.write(self.style.WARNING(f"Reached max pages limit ({max_pages}). Stopping."))
                    break

                target_url = f"https://demo.inelabteamdev.com/?page={page_no}"
                self.stdout.write(f"\nNavigating to Page {page_no}: {target_url}")

                try:
                    page.goto(target_url, wait_until="networkidle", timeout=30000)
                    
                    # Wait for selector or small delay for React rendering
                    try:
                        page.wait_for_selector("div.tile-body, div.title-body", timeout=5000)
                    except Exception:
                        time.sleep(2)

                    containers = page.query_selector_all("div.tile-body, div.title-body")
                    
                    if not containers:
                        self.stdout.write(self.style.WARNING(f"No product items found on page {page_no}."))
                        consecutive_empty_pages += 1
                        if consecutive_empty_pages >= max_consecutive_empty:
                            self.stdout.write(self.style.SUCCESS(f"Finished scraping: hit {consecutive_empty_pages} consecutive empty pages."))
                            break
                        page_no += 1
                        continue

                    # Reset consecutive empty counter on finding products
                    consecutive_empty_pages = 0
                    page_saved_count = 0

                    for idx, container in enumerate(containers, start=1):
                        title_el = container.query_selector("h3.tile-name, h3.title-name")
                        sku_el = container.query_selector("p.tile-sku, p.title-sku")

                        product_title = title_el.inner_text().strip() if title_el else "Unknown Product"
                        raw_sku = sku_el.inner_text().strip() if sku_el else ""
                        
                        # Extract p.title-sku last three characters (trimmed)
                        trimmed_sku = raw_sku.strip()
                        product_id = trimmed_sku[-3:].strip() if len(trimmed_sku) >= 3 else trimmed_sku

                        if not product_id:
                            self.stdout.write(self.style.WARNING(f"  Item {idx}: Empty product_id, skipping."))
                            continue

                        # Save to PostgreSQL DB
                        product, created = Product.objects.update_or_create(
                            product_id=product_id,
                            defaults={
                                'product_title': product_title,
                                'raw_sku': raw_sku,
                            }
                        )

                        action_str = "CREATED" if created else "UPDATED"
                        self.stdout.write(f"  [{action_str}] ID: {product_id} | Title: {product_title} | (Raw SKU: {raw_sku})")
                        page_saved_count += 1
                        total_scraped += 1

                    self.stdout.write(self.style.SUCCESS(f"Page {page_no} complete. Saved/Updated {page_saved_count} products."))
                    page_no += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error scraping page {page_no}: {e}"))
                    break

            browser.close()

        self.stdout.write(self.style.SUCCESS(f"\nScraping session completed. Total products processed: {total_scraped}"))
