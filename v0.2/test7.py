import os
import json
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import threading
import traceback
from collections import deque

lock = threading.Lock()

ad_tags = ['IFRAME', 'IMG', 'DIV', 'INS']  # Tags that are more likely to be ads
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
]
def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--no-sandbox')
    return webdriver.Chrome(options=options)

def has_ad_attributes(element):
    for attr in ad_attributes:
        if element.get_attribute(attr):
            return True
    return False

def mark_and_log_ads_in_viewport(driver):
    ads_data = deque()
    for tag in ad_tags:
        elements = driver.find_elements(By.TAG_NAME, tag)
        for element in elements:
            try:
                if element.is_displayed() and has_ad_attributes(element):
                    rect = element.rect
                    if rect['width'] > 10 and rect['height'] > 15 and rect['x'] > 10 and rect['y'] > 10:
                        ads_data.append({
                            "url": driver.current_url,
                            "x": rect['x'],
                            "y": rect['y'],
                            "width": rect['width'],
                            "height": rect['height']
                        })
            except StaleElementReferenceException:
                continue
    return ads_data
def process_url(url, save_path, all_ads_data, driver):
    try:
        driver.get(url)
        ads_data = mark_and_log_ads_in_viewport(driver)
        all_ads_data.extend(ads_data)
        if len(all_ads_data) >= 100:
            with open(os.path.join(save_path, 'ads_data.json'), 'w') as f:
                json.dump(list(all_ads_data), f, indent=2)
            all_ads_data.clear()
    except Exception as e:
        print(f"Error processing URL {url}: {e}")
        print(traceback.format_exc())


def main():
    save_path = "/Users/kaleemullahqasim/Desktop/Prof Xiu Hai Tao/data/"
    os.makedirs(save_path, exist_ok=True)
    df = pd.read_csv('/Users/kaleemullahqasim/Documents/GitHub/AdIdentifer_Downloader/v0.2/200_request_code.csv')
    urls = df['url'].tolist()
    urls = urls[:1000]
    all_ads_data = deque()

    driver = create_driver()
    for url in tqdm(urls, total=len(urls)):
        process_url(url, save_path, all_ads_data, driver)
    driver.quit()

if __name__ == "__main__":
    main()