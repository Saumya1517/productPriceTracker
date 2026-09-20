from django.core.management.base import BaseCommand
from scraper.management.commands.scrape_price import scrape_single_product_price

class Command(BaseCommand):
    help = "Trigger checkprice event for a product to scrape its price and record price history."

    def add_arguments(self, parser):
        parser.add_argument(
            'product_id',
            type=str,
            help='Product ID to check price for (e.g. 002)'
        )
        parser.add_argument(
            '--headful',
            action='store_true',
            help='Run browser in headful mode (visible browser UI)'
        )

    def handle(self, *args, **options):
        product_id = options['product_id'].strip()
        headless = not options['headful']

        self.stdout.write(self.style.SUCCESS(f"Triggering checkprice event for Product ID: {product_id}"))
        try:
            price = scrape_single_product_price(product_id, headless=headless, logger=self)
            self.stdout.write(self.style.SUCCESS(f"\n[SUCCESS] Price {price} fetched & recorded in price_history for product {product_id}!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n[ERROR] checkprice event failed for product {product_id}: {e}"))
