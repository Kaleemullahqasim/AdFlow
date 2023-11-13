import os
import time
import csv
import concurrent.futures
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
from requests.exceptions import RequestException
from ad_servers_list import known_ad_servers  

def domain_in_ad_servers(url, ad_servers):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return any(ad_server in domain for ad_server in ad_servers)

def scroll_to_bottom(driver, step_size=100, delay=0.5):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script(f"window.scrollBy(0, {step_size});")
        time.sleep(delay)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def download_image(image_url, save_path, is_ad, max_retries=5):
    folder = "ads" if is_ad else "non-ads"
    save_path = os.path.join(save_path, folder)

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    file_name = image_url.split('/')[-1]
    file_path = os.path.join(save_path, file_name)

    for attempt in range(max_retries):
        try:
            response = requests.get(image_url)
            if response.status_code == 200:
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                return
        except RequestException as e:
            print(f"Request exception occurred (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(1)
    print(f"Failed to download image after {max_retries} retries")

def find_and_save_images(driver, url_save_path):
    img_elements = driver.find_elements(By.TAG_NAME, 'img')
    for img in img_elements:
        img_url = img.get_attribute('src')
        if img_url:
            is_ad = domain_in_ad_servers(img_url, known_ad_servers)
            download_image(img_url, url_save_path, is_ad)

def process_url(url, base_save_path):
    driver = webdriver.Chrome()
    url_save_path = os.path.join(base_save_path, urlparse(url).netloc.replace('.', '_'))
    os.makedirs(url_save_path, exist_ok=True)
    driver.get(url)
    time.sleep(5)
    scroll_to_bottom(driver)
    find_and_save_images(driver, url_save_path)
    driver.quit()

def read_urls_from_csv(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        return [row[0] for row in reader]

def process_batch(urls, base_save_path, max_threads):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(process_url, url, base_save_path) for url in urls]
        for future in concurrent.futures.as_completed(futures):
            future.result()

if __name__ == "__main__":
    csv_file_path = 'urls.csv'
    urls_to_process = read_urls_from_csv(csv_file_path)
    base_save_path = '/Users/kaleemullahqasim/Desktop/Prof Xiu Hai Tao/data/'  # Replace with your actual path
    os.makedirs(base_save_path, exist_ok=True)
    max_threads = 3
    batch_size = 3

    for i in range(0, len(urls_to_process), batch_size):
        batch_urls = urls_to_process[i:i + batch_size]
        process_batch(batch_urls, base_save_path, max_threads)
        time.sleep(2)
