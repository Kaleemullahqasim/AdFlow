import os
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
import json
import string
import time 
from ad_servers_list import known_ad_servers
import csv 
import os
import threading
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


BATCH_SIZE = 10
THREAD_COUNT = 15

def sanitize_filename(filename):
    """Sanitize the filename by removing invalid characters and ensuring it ends with .png"""
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    cleaned_filename = ''.join(c for c in filename if c in valid_chars)
    if not cleaned_filename.lower().endswith('.png'):
        cleaned_filename += '.png'
    return cleaned_filename

def is_known_ad_server(url):
    for ad_server in known_ad_servers:
        if ad_server in url:
            return True
    return False


ad_keywords = [
        ' ad ', 'ads', 'advert', 'advertisement', 'sponsored',
        'banner', 'promoted', 'promotion', 'doubleclick',
        'affiliates', 'placements', 'outbrain',
        'monetization', 'syndication', 'ppc', 'cpm', 'cpc',
        'interstitial', 'preroll', 'postroll', 'midroll',
        'media.net', 'AdSense', 'revcontent', 'buysellads',
        'popunder', 'pop-up', 'pop-over', 'skyscraper',
        'sidebar', 'leaderboard', 'newsletter',
        '广告', '推广', '赞助',
        'anuncio', 'publicidad', 'patrocinado',
        'ad_hover_href'
    ]
ad_tags = ['SCRIPT', 'IFRAME', 'DIV', 'IMG', 'INS', 'VIDEO', 'CANVAS', 'EMBED', 'OBJECT', 'SOURCE', 'SVG', 'TRACK',]

def is_descendant(child_element, parent_elements):
    for parent_element in parent_elements:
        if child_element.is_displayed() and parent_element.is_displayed():
            if (child_element.location['x'] >= parent_element.location['x'] and
                child_element.location['y'] >= parent_element.location['y'] and
                child_element.location['x'] + child_element.size['width'] <= parent_element.location['x'] + parent_element.size['width'] and
                child_element.location['y'] + child_element.size['height'] <= parent_element.location['y'] + parent_element.size['height']):
                return True
    return False

def mark_and_log_ads(driver, save_path):
    ads_data = []
    parent_ad_elements = []  # List to keep track of parent ad elements

    for tag in ad_tags:
        elements = driver.find_elements(By.TAG_NAME, tag)
        for element in elements:
            for attribute in element.get_property('attributes'):
                keyword_matches = [keyword for keyword in ad_keywords if keyword in attribute['value']]
                if keyword_matches:
                    if not is_descendant(element, parent_ad_elements):
                        # Highlight the ad
                        driver.execute_script("arguments[0].style.border='10px solid red'", element)
                        parent_ad_elements.append(element)

                        # Get and log the ad's position
                        rect = element.rect
                        if rect['x'] > 0 and rect['y'] > 0 and rect['width'] > 20 and rect['height'] > 20:
                            position_data = {
                                "url": driver.current_url,
                                "x": rect['x'],
                                "y": rect['y'],
                                "width": rect['width'],
                                "height": rect['height'],
                                "keywords": keyword_matches,
                                "child-tag": tag,
                 
                                
                                "parent": {
                                    "parent-tag": element.find_element(By.XPATH, './ancestor::*[1]').tag_name,
                                    "id": element.find_element(By.XPATH, './ancestor::*[1]').get_attribute('id'),
                                    "class": element.find_element(By.XPATH, './ancestor::*[1]').get_attribute('class'),
                                    "is_displayed": element.find_element(By.XPATH, './ancestor::*[1]').is_displayed(),
                                    #if there is a ad which is not photo but text can we extract the text from it
                                    "text": element.find_element(By.XPATH, './ancestor::*[1]').text,
                                },

                            },
                            ads_data.append(position_data)
                        break  # No need to check other attributes if one matches
    return ads_data



def read_urls_from_csv(file_path):
    # Function to read URLs from a CSV file and return them as a list
    urls = []
    with open(file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            urls.append(row[0])  # Assuming URL is in the first column
    return urls


def process_url_batch(url_batch, batch_id, save_path):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        ads_data = []
        json_file_path = os.path.join(save_path, 'ad_positions.json')  # Define json_file_path variable

        for url in url_batch:
            driver.get(url)
            time.sleep(5)  # Wait for page load
            batch_ads_data = mark_and_log_ads(driver, save_path)
            ads_data.extend(batch_ads_data)

            # Save to JSON after processing each URL
            with open(json_file_path, 'w') as f:
                json.dump(ads_data, f, indent=2)

        return ads_data
    except Exception as e:
        print(f"Error processing batch {batch_id}: {e}")
        return []
    finally:
        if driver:
            driver.quit()
def main():
    urls = read_urls_from_csv('urls.csv')
    save_path = '/Users/kaleemullahqasim/Desktop/Prof Xiu Hai Tao/data/20231118'
    os.makedirs(save_path, exist_ok=True)
    json_file_path = os.path.join(save_path, 'ad_positions.json')

    url_batches = [urls[i:i + BATCH_SIZE] for i in range(0, len(urls), BATCH_SIZE)]

    threads = []
    all_ads_data = []

    def thread_function(batch, batch_id):
        ads_data = process_url_batch(batch, batch_id, save_path)
        all_ads_data.extend(ads_data)

    for i, batch in enumerate(url_batches):
        thread = threading.Thread(target=thread_function, args=(batch, i))
        print(f"Starting thread {i}")
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    with open('ad_positions-11.json', 'w') as f:
        json.dump(all_ads_data, f, indent=2)

if __name__ == "__main__":
    main()