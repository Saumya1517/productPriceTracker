import os
import sys
import time
import threading
from django.utils import timezone

_scheduler_started = False
_lock = threading.Lock()

def _run_scheduler():
    import schedule
    from django.core.management import call_command

    def job():
        print(f"\n[AUTO-CRON TRIGGER] Running check_all_tracked_prices at {timezone.localtime().strftime('%Y-%m-%d %H:%M:%S')} IST...")
        try:
            call_command('check_all_tracked_prices')
        except Exception as e:
            print(f"[AUTO-CRON ERROR] Failed: {e}")

    # Initial delay so web server completes boot and opens socket
    time.sleep(10)
    job()

    # Schedule recurring job every 15 minutes
    schedule.every(15).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(30)

def start_background_scheduler():
    global _scheduler_started
    with _lock:
        if _scheduler_started:
            return

        cmd = " ".join(sys.argv)
        # Skip scheduler during migrations, static compilation, or direct scraper CLI tools
        if any(ignored in cmd for ignored in [
            'migrate', 'makemigrations', 'collectstatic', 'check',
            'checkprice', 'scrape_price', 'check_all_tracked_prices'
        ]):
            return

        # For django dev server (runserver), ensure it only runs once in the reloaded process
        if 'runserver' in cmd and os.environ.get('RUN_MAIN') != 'true':
            return

        _scheduler_started = True
        thread = threading.Thread(target=_run_scheduler, daemon=True, name="PriceScraperAutoCronThread")
        thread.start()
        print(">>> [INE TRACKER] 15-Minute Background Price Scraper daemon thread started automatically!")
