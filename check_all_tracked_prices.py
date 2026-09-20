#!/usr/bin/env python
import os
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ine_scraper.settings')
import django
django.setup()

from django.core.management import call_command

def main():
    headful = '--headful' in sys.argv
    call_command('check_all_tracked_prices', headful=headful)

if __name__ == '__main__':
    main()
