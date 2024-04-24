import os
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from tqdm import tqdm


# Initialize logging
import logging
from threading import Lock
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


# Configuration for web driver
def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(15)  # Timeout for page load
    return driver


ad_tags = ['IFRAME', 'IMG', 'DIV', 'INS', 'SCRIPT' ,'VIDEO'] 
ad_attributes = [
    'data-ad-format',  # Google AdSense
    'data-ad-layout-key',  # Google AdSense
    'data-ad-client',  # Google AdSense
    'data-ad-slot',  # Google AdSense
    'data-google-query-id',  # Google AdSense
    'data-amazon-targeting',  # Amazon Associates
    'data-aax_size',  # Amazon Associates
    'data-aax_src',  # Amazon Associates
    'data-aax_options',  # Amazon Associates
    'data-aax_pub_id',  # Amazon Associates
    'data-ia-disable-ad',  # Infolinks
    'data-tag-type',  # Infolinks
    'data-ad',  # AOL Advertising
    'data-ad-client',  # AOL Advertising
    'data-ad-slot',  # AOL Advertising
    'data-ad-type',  # AOL Advertising
    'data-ad-layout',  # AOL Advertising
    'data-ad-name',  # AOL Advertising
    'data-bidvertiser',  # BidVertiser
    'data-chitika-contextual-ad',  # Chitika
    'data-revive-zoneid',  # Revive Adserver
    'data-zid',  # Revive Adserver
    'data-zone-id',  # Revive Adserver
    'data-oeu',  # OpenX
    'data-oid',  # OpenX
    'data-zone',  # OpenX
    'data-ad-format', 'data-ad-layout-key', 'data-ad-client', 'data-ad-slot', 'data-google-query-id'
]

def has_ad_attributes(element):
    for attr in ad_attributes:
        if element.get_attribute(attr):
            return True
    return False

# Process ad data from viewport
def mark_and_log_ads_in_viewport(driver):
    ads_data = []
    try:
        for tag in ad_tags:
            elements = driver.find_elements(By.TAG_NAME, tag)
            for element in elements:
                if element.is_displayed() and has_ad_attributes(element):
                    rect = element.rect
                    if rect['width'] > 0 and rect['height'] > 0 and rect['x'] > 0 and rect['y'] > 0:
                        ads_data.append({
                            "url": driver.current_url,
                            "x": rect['x'],
                            "y": rect['y'],
                            "width": rect['width'],
                            "height": rect['height']
                        })
    except StaleElementReferenceException:
        logging.error("Stale element reference encountered.")
    return ads_data

# Process each URL with associated driver
def process_url(url, driver):
    try:
        driver.get(url)
        return mark_and_log_ads_in_viewport(driver)
    except TimeoutException:
        logging.error(f"Timeout while loading {url}")
    except Exception as e:
        logging.error(f"Exception for {url}: {str(e)}")
    return []

# Main function to execute script
def main():
    urls_csv_path = '/Users/kaleemullahqasim/Documents/GitHub/AdIdentifer_Downloader/v0.2/200_request_code.csv'
    save_path = "/Users/kaleemullahqasim/Desktop/Prof Xiu Hai Tao/data/"
    os.makedirs(save_path, exist_ok=True)
    df = pd.read_csv(urls_csv_path)
    urls = df['url'].tolist()
    urls = urls[3000:-1]

    num_drivers = 25
    all_ads_data = []
    progress_bar = tqdm(total=len(urls), desc="Processing URLs", unit="url")
    lock = Lock()


    with ThreadPoolExecutor(max_workers=num_drivers) as executor:
        drivers = [create_driver() for _ in range(num_drivers)]
        future_to_url = {executor.submit(process_url, url, drivers[i % num_drivers]): url for i, url in enumerate(urls)}

        for future in as_completed(future_to_url):
            ads_data = future.result()
            with lock:
                if ads_data:
                    all_ads_data.extend(ads_data)
                progress_bar.update(1)  # Update the progress for each URL processed

    # Save the accumulated data once after all processing is done
    with open(os.path.join(save_path, 'ads_data_3000_1b.json'), 'w') as f:
        json.dump(all_ads_data, f, indent=4)

    # Clean up drivers and close progress bar
    for driver in drivers:
        driver.quit()
    progress_bar.close()

if __name__ == "__main__":
    main()
