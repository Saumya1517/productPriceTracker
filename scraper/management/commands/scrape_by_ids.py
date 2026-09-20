import os
import time
from django.core.management.base import BaseCommand
from playwright.sync_api import sync_playwright
from scraper.models import Product

PRODUCT_IDS = [
    "002", "005", "007", "015", "016", "029", "034", "041", "042", "043",
    "045", "050", "052", "057", "058", "060", "069", "071", "085", "087",
    "088", "090", "096", "099", "100", "108", "113", "114", "126", "127",
    "131", "138", "141", "143", "146", "149", "150", "151", "152", "154",
    "160", "168", "169", "175", "176", "180", "187", "188", "190", "191",
    "196", "197", "209", "212", "222", "228", "229", "233", "236", "237",
    "255", "259", "261", "262", "272", "283", "284", "286", "306", "308",
    "312", "313", "321", "323", "330", "333", "336", "337", "338", "341",
    "344", "346", "347", "355", "357", "361", "362", "366", "372", "373",
    "381", "385", "387", "388", "389", "398", "399", "401", "404", "408",
    "410", "411", "412", "413", "417", "418", "420", "422", "426", "428",
    "429", "430", "432", "435", "436", "437", "438", "439", "441", "444",
    "447", "449", "452", "454", "459", "460", "466", "470", "473", "478",
    "481", "482", "489", "493", "495", "500", "503", "506", "508", "510",
    "513", "519", "521", "527", "529", "532", "534", "537", "538", "539",
    "544", "547", "553", "554", "561", "563", "570", "574", "576", "578",
    "590", "592", "593", "594", "598", "600", "602", "604", "612", "614",
    "625", "630", "631", "635", "639", "642", "643", "649", "651", "653",
    "654", "656", "661", "667", "668", "675", "677", "679", "680", "684",
    "685", "687", "692", "694", "697", "699", "703", "707", "717", "718",
    "719", "720", "724", "725", "726", "728", "735", "737", "743", "746",
    "748", "749", "754", "755", "770", "774", "775", "776", "779", "780",
    "788", "790", "793", "806", "810", "829", "840", "843", "855", "863",
    "864", "865", "881", "891", "894", "900", "906", "907", "908", "912",
    "916", "917", "921", "926", "939", "944", "949", "950", "954", "956",
    "964", "966", "970", "976", "977", "978", "981", "982", "985", "986",
    "997"
]

class Command(BaseCommand):
    help = "Scrape product titles from https://demo.inelabteamdev.com/product/{product_id} by given list of IDs"

    def add_arguments(self, parser):
        parser.add_argument(
            '--headful',
            action='store_true',
            help='Run browser in headful mode'
        )

    def handle(self, *args, **options):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        headless = not options['headful']

        # Deduplicate product IDs while preserving list order
        unique_ids = list(dict.fromkeys(PRODUCT_IDS))
        total_items = len(unique_ids)

        self.stdout.write(self.style.SUCCESS(f"Starting scraper for {total_items} target product IDs..."))

        results = []
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
                self.stdout.write(self.style.ERROR("Could not launch browser."))
                return

            context = browser.new_context()
            page = context.new_page()

            for i, product_id in enumerate(unique_ids, start=1):
                url = f"https://demo.inelabteamdev.com/product/{product_id}"
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    try:
                        page.wait_for_selector("h1", timeout=5000)
                    except Exception:
                        time.sleep(1)

                    h1_el = page.query_selector("h1")
                    product_title = h1_el.inner_text().strip() if h1_el else "Unknown Title"

                    # Save / update in database
                    product, created = Product.objects.update_or_create(
                        product_id=product_id,
                        defaults={'product_title': product_title}
                    )
                    status = "CREATED" if created else "UPDATED"
                    self.stdout.write(f"[{i}/{total_items}] ID: {product_id} -> Title: {product_title} ({status})")
                    results.append((product_id, product_title))

                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"[{i}/{total_items}] Failed for ID {product_id} ({url}): {e}"))

            browser.close()

        self.stdout.write(self.style.SUCCESS(f"\nSuccessfully scraped {len(results)}/{total_items} products."))
