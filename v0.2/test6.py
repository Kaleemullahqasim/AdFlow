import os
import json
import concurrent.futures
from typing import List
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import time
from typing import List, Dict, Union
import pandas as pd




# Define ad-related keywords and tags
ad_keywords = [
    ' ad ', 'ads', 'advert', 'advertisement', 'sponsored',
    'banner', 'promoted', 'promotion', 'doubleclick',
    'affiliates', 'placements', 'taboola', 'outbrain',
    'monetization', 'syndication', 'ppc', 'cpm', 'cpc',
    'interstitial', 'preroll', 'postroll', 'midroll',
    'media.net', 'AdSense', 'revcontent', 'buysellads',
    'popunder', 'pop-up', 'pop-over', 'skyscraper',
    'sidebar', 'leaderboard', 'sticky', 'newsletter',
    '广告', '推广', '赞助',
    'anuncio', 'publicidad', 'patrocinado',
    'ad_hover_href'
]

ad_tags = ['SCRIPT', 'IFRAME', 'DIV', 'IMG', 'INS', 'VIDEO', 'CANVAS', 'EMBED', 'OBJECT', 'SOURCE', 'SVG', 'TRACK']

def process_url(url, driver):
    """
    Process a single URL to find ad positions, with retry logic for resilience.
    
    Args:
    url (str): URL to be processed.
    driver (webdriver.Chrome): Selenium WebDriver instance.
    
    Returns:
    list: A list of dictionaries, each containing data about an ad found.
    """
    ads_data = []

    try:
        driver.get(url)
        time.sleep(5)  # Allow time for the page and ads to load

        for tag in ad_tags:
            elements = driver.find_elements(By.TAG_NAME, tag)
            for element in elements:
                # Check if any of the element's attributes contain ad keywords
                if any(keyword in element.get_attribute('outerHTML') for keyword in ad_keywords):
                    # Check if this is a 'parent' ad element
                    if not any(parent.tag_name == tag for parent in element.find_elements(By.XPATH, './/..')):
                        rect = element.rect
                        ads_data.append({
                            "url": url,
                            "tag": tag,
                            "position": {"x": rect['x'], "y": rect['y'], "width": rect['width'], "height": rect['height']}
                        })
    except (TimeoutException, StaleElementReferenceException):
        print(f"An error occurred while processing {url}. Retrying...")
        return process_url(url, driver)  # Simple retry mechanism
    
    return ads_data

def main(urls_to_process, save_path):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        # Use dictionary to hold future objects to correlate them with their URL
        future_to_url = {executor.submit(process_url, url, webdriver.Chrome(options=options)): url for url in urls_to_process}
        
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                ads_data = future.result()
                # Save data immediately after processing each URL to minimize data loss
                if ads_data:  # Check if there is any ad data collected
                    filename = os.path.join(save_path, f"{urlparse(url).netloc}_ads.json")
                    with open(filename, 'w') as f:
                        json.dump(ads_data, f, indent=4)
                        print(f"Data for {url} saved successfully.")
            except Exception as exc:
                print(f"Error processing URL {url}: {exc}")

if __name__ == "__main__":
    urls_to_process = pd.read_csv('/Users/kaleemullahqasim/Documents/GitHub/AdIdentifer_Downloader/v0.2/200_only_ad.csv')['url'].tolist()
    # only for testing
    urls_to_process = urls_to_process[:100]


    save_path = '/Users/kaleemullahqasim/Documents/GitHub/AdIdentifer_Downloader/v0.2/'  # Update with the actual path
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    main(urls_to_process, save_path)