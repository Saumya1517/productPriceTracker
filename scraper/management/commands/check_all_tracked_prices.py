import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from scraper.models import TrackedProduct
from scraper.management.commands.scrape_price import scrape_single_product_price

class Command(BaseCommand):
    help = "Iterate through all products in TrackedProduct database table and scrape latest price into price_history."

    def add_arguments(self, parser):
        parser.add_argument(
            '--headful',
            action='store_true',
            help='Run browser in headful mode'
        )
        parser.add_argument(
            '--delay',
            type=int,
            default=2,
            help='Delay in seconds between scraping each tracked product (default: 2s)'
        )

    def handle(self, *args, **options):
        headless = not options['headful']
        delay = options['delay']

        start_time = timezone.localtime()
        self.stdout.write(self.style.SUCCESS(
            f"=== [BATCH CRON] Starting Price Check for All Tracked Products at {start_time.strftime('%Y-%m-%d %H:%M:%S')} IST ==="
        ))

        tracked_items = list(TrackedProduct.objects.select_related('product').all())
        total = len(tracked_items)

        if total == 0:
            self.stdout.write(self.style.WARNING("No tracked products found in the database. Add products to tracking first."))
            return

        self.stdout.write(f"Found {total} tracked product(s) to check.\n")

        success_count = 0
        failed_count = 0

        for idx, item in enumerate(tracked_items, start=1):
            product = item.product
            pid = product.product_id
            title = product.product_title

            self.stdout.write(self.style.NOTICE(f"[{idx}/{total}] Checking price for Product {pid} - {title}..."))
            try:
                price = scrape_single_product_price(pid, headless=headless, logger=self)
                self.stdout.write(self.style.SUCCESS(f"  -> Recorded Price: Rs. {price} for Product {pid}\n"))
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  -> Failed to check price for Product {pid}: {e}\n"))
                failed_count += 1

            if idx < total and delay > 0:
                time.sleep(delay)

        end_time = timezone.localtime()
        self.stdout.write(self.style.SUCCESS(
            f"=== [BATCH CRON] Completed at {end_time.strftime('%Y-%m-%d %H:%M:%S')} IST | Success: {success_count} | Failed: {failed_count} ==="
        ))
