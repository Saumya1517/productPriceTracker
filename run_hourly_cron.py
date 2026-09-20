#!/usr/bin/env python
import os
import sys
import time
import schedule

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ine_scraper.settings')
import django
django.setup()

from django.core.management import call_command
from django.utils import timezone

def job(headful=True):
    mode_str = "HEADED" if headful else "HEADLESS"
    print(f"\n[CRON TRIGGER - {mode_str}] Running check_all_tracked_prices at {timezone.localtime().strftime('%Y-%m-%d %H:%M:%S')} IST...")
    try:
        call_command('check_all_tracked_prices', headful=headful)
    except Exception as e:
        print(f"[CRON ERROR] Failed: {e}")

def main():
    headful = '--headless' not in sys.argv
    mode_str = "HEADED" if headful else "HEADLESS"
    print(f"=== Tracked Products Price Checker Daemon Started ({mode_str} Mode) ===")
    print("Scheduled to run every 15 minutes. Press Ctrl+C to stop.")
    
    # Run once immediately on start
    job(headful=headful)

    # Schedule every 15 minutes
    schedule.every(15).minutes.do(lambda: job(headful=headful))

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == '__main__':
    main()
