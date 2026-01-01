#!/usr/bin/env python3
"""
Scheduled Runner for Gmail Invoice Scanner
Runs the scanner on a schedule and sends notifications.

This can be used instead of cron for more control.
"""

import schedule
import time
import logging
from datetime import datetime
from scanner import main as run_scanner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/invoice-scanner.log')
    ]
)
logger = logging.getLogger(__name__)


def scheduled_scan():
    """Run the scanner and log results."""
    logger.info("=" * 60)
    logger.info(f"SCHEDULED SCAN STARTING - {datetime.now()}")
    logger.info("=" * 60)
    
    try:
        results = run_scanner()
        
        if results['invoices_found'] > 0:
            logger.info(f"🎉 Found {results['invoices_found']} new invoices!")
            # You could add email/SMS notification here
        else:
            logger.info("No new invoices found in this scan.")
            
    except Exception as e:
        logger.error(f"Scan failed with error: {e}")
        # You could add error notification here


def main():
    """Main scheduler loop."""
    logger.info("Starting Gmail Invoice Scanner Scheduler")
    logger.info("Unit 574 - VIN: 3AKJHHDR7KSKE1598")
    logger.info("Scans will run every 4 hours")
    
    # Run immediately on start
    scheduled_scan()
    
    # Schedule future runs
    schedule.every(4).hours.do(scheduled_scan)
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    main()

