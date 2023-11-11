import os
import time
import json
import string
import threading
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
import concurrent.futures

def sanitize_filename(filename):
    """Sanitize the filename by removing invalid characters and ensuring it ends with .png."""
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    cleaned_filename = ''.join(c for c in filename if c in valid_chars)
    if not cleaned_filename.lower().endswith('.png'):
        cleaned_filename += '.png'
    return cleaned_filename

def take_screenshot(element, file_path):
    """Take a screenshot of a given element."""
    try:
        if element.is_displayed() and element.size['height'] > 0 and element.size['width'] > 0:
            element.screenshot(file_path)
    except Exception as e:
        print(f"Error taking screenshot: {e}")

def process_pattern(driver, pattern, save_path, ads_data_list, lock):
    """Process a given pattern from EasyList."""
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, pattern)
        for element in elements:
            if element.is_displayed():
                rect = element.rect
                position_data = {
                    "url": driver.current_url,
                    "x": rect['x'],
                    "y": rect['y'],
                    "width": rect['width'],
                    "height": rect['height'],
                    "pattern": pattern
                }
                screenshot_filename = sanitize_filename(f"{urlparse(driver.current_url).netloc}_{pattern}_{int(time.time())}.png")
                take_screenshot(element, os.path.join(save_path, screenshot_filename))

                with lock:
                    ads_data_list.append(position_data)
    except StaleElementReferenceException:
        pass

def scroll_and_capture_ads(driver, save_path, patterns, max_threads=10):
    """Scroll through the webpage and capture ads, using a thread pool."""
    all_ads_data = []
    lock = threading.Lock()
    last_height = driver.execute_script("return document.body.scrollHeight")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        while True:
            driver.execute_script("window.scrollBy(0, window.innerHeight);")
            time.sleep(1)

            futures = []
            for pattern in patterns:
                futures.append(executor.submit(process_pattern, driver, pattern, save_path, all_ads_data, lock))

            # Wait for all threads in the pool to complete
            for future in concurrent.futures.as_completed(futures):
                future.result()  # This will re-raise any exception caught in the thread

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    return all_ads_data

def parse_easylist(file_path):
    """Parse patterns from EasyList."""
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    css_selectors = []

    for line in lines:
        if line.startswith('!') or not line.strip():
            continue
        if '##' in line:
            css_selectors.append(line.split('##')[1].strip())

    return css_selectors

# Main Execution
driver = webdriver.Chrome()
save_path = '/Users/kaleemullahqasim/Desktop/Prof Xiu Hai Tao/data/'
os.makedirs(save_path, exist_ok=True)

easylist_path = 'easylist.txt'
css_selectors = parse_easylist(easylist_path)

urls_to_process = ['https://tweaklibrary.com/image-downloader-extensions-for-chrome/#google_vignette']
for url in urls_to_process:
    driver.get(url)
    time.sleep(5)
    all_ads_data = scroll_and_capture_ads(driver, save_path, css_selectors)

with open('ad_positions.json', 'w') as f:
    json.dump(all_ads_data, f, indent=2)

driver.quit()
