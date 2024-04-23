from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException
from requests.exceptions import RequestException
import os
import time
import csv
import json
import concurrent.futures
from tqdm import tqdm

# Assuming this list is provided elsewhere in your project
from ad_servers_list import known_ad_servers
import string

def domain_in_ad_servers(url, ad_servers):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return any(ad_server in domain for ad_server in ad_servers)

def sanitize_filename(filename):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    cleaned_filename = ''.join(c for c in filename if c in valid_chars)
    if not cleaned_filename.lower().endswith('.png'):
        cleaned_filename += '.png'
    return cleaned_filename

def mark_and_log_ads(driver, save_path):
    ads_data = []
    ad_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'ad') or contains(@src, 'ad')]") 

    for element in ad_elements:
        try:
            if domain_in_ad_servers(element.get_attribute('src'), known_ad_servers):
                ads_data.append({
                    'url': element.get_attribute('src'),
                    'x': element.location['x'],
                    'y': element.location['y'],
                    'width': element.size['width'],
                    'height': element.size['height']
                })
        except StaleElementReferenceException:
            continue

    # Always save data to a JSON file
    with open(os.path.join(save_path, 'ad_positions.json'), 'w') as file:
        json.dump(ads_data, file, indent=2)

def process_url(url, base_save_path):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'body')))
        url_save_path = os.path.join(base_save_path, urlparse(url).netloc.replace('.', '_'))
        os.makedirs(url_save_path, exist_ok=True)
        mark_and_log_ads(driver, url_save_path)
    finally:
        driver.quit()

def read_urls_from_csv(file_path):
    urls = []
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            urls.append(row[0])
    return urls

def main():
    csv_file_path = '/Users/kaleemullahqasim/Documents/GitHub/AdIdentifer_Downloader/v0.2/200_of_all_URLs.csv'
    base_save_path = '/Users/kaleemullahqasim/Documents/GitHub/AdIdentifer_Downloader/v0.2/'
    os.makedirs(base_save_path, exist_ok=True)
    
    urls_to_process = read_urls_from_csv(csv_file_path)
    urls_to_process = urls_to_process[:20]
    max_threads = 10
    with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
        futures = [executor.submit(process_url, url, base_save_path) for url in urls_to_process]
        for future in concurrent.futures.as_completed(futures):
            future.result()  # Handle exceptions here if needed

if __name__ == "__main__":
    main()
