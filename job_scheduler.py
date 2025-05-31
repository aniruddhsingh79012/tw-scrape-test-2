import schedule
import time
import os

def scrape_and_store():
    print("Running scraping job...")
    os.system("python /home/im/Downloads/twitter/twscrape/scrape_and_store.py")

# Run every 5 minutes
schedule.every(1).minutes.do(scrape_and_store)

while True:
    schedule.run_pending()
    time.sleep(1)
