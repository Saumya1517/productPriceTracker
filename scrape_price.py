#!/usr/bin/env python
import os
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ine_scraper.settings')
import django
django.setup()

from scraper.management.commands.scrape_price import scrape_single_product_price

def main():
    if len(sys.argv) < 2:
        print("Usage: python scrape_price.py <product_id> [--headful]")
        print("Example: python scrape_price.py 002")
        sys.exit(1)

    product_id = sys.argv[1].strip()
    headless = '--headful' not in sys.argv

    print(f"=== Scraping Price for Product ID: {product_id} ===")
    try:
        price = scrape_single_product_price(product_id, headless=headless)
        print(f"\n[SUCCESS] Price {price} stored in PostgreSQL database for product {product_id}!")
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
