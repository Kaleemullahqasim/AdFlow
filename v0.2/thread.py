from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
import json
from time import sleep
from urllib.parse import urlparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import string
import requests
from selenium.common.exceptions import StaleElementReferenceException
from requests.exceptions import RequestException
# import threading
import csv
import concurrent.futures
from ad_servers_list import known_ad_servers

def domain_in_ad_servers(url, ad_servers):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return any(ad_server in domain for ad_server in ad_servers)


def read_urls_from_csv(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        return [row[0] for row in reader]


def scroll_to_bottom(driver, step_size=100, delay=0.5):
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        
        driver.execute_script(f"window.scrollBy(0, {step_size});")
        sleep(delay)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def sanitize_filename(filename):
    """Sanitize the filename by removing invalid characters and ensuring it ends with .png"""
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    cleaned_filename = ''.join(c for c in filename if c in valid_chars)
    if not cleaned_filename.lower().endswith('.png'):
        cleaned_filename += '.png'
    return cleaned_filename

def find_images_in_iframe(driver, iframe_element):
    """Find image URLs in an iframe."""
    driver.switch_to.frame(iframe_element)
    img_elements = driver.find_elements(By.TAG_NAME, 'img')
    img_urls = [img.get_attribute('src') for img in img_elements if img.get_attribute('src')]
    driver.switch_to.default_content()  # Switch back to the main document
    return img_urls

def find_images_in_div(driver, div_element):
    """Find image URLs in a div element."""
    img_urls = []

    # Extract URLs from <img> elements within the div
    img_elements = div_element.find_elements(By.TAG_NAME, 'img')
    img_urls.extend([img.get_attribute('src') for img in img_elements if img.get_attribute('src')])

    # Extract URL from CSS background-image
    style = driver.execute_script(
        "return window.getComputedStyle(arguments[0], null).getPropertyValue('background-image');", 
        div_element
    )
    if style and 'url(' in style:
        bg_img_url = style.split('url(')[1].split(')')[0].replace('"', '').replace("'", '')
        img_urls.append(bg_img_url)

    return img_urls


def is_descendant(child_element, parent_elements, driver):
    try:
        for parent_element in parent_elements:
            if child_element.is_displayed() and parent_element.is_displayed():
                if (child_element.location['x'] >= parent_element.location['x'] and
                    child_element.location['y'] >= parent_element.location['y'] and
                    child_element.location['x'] + child_element.size['width'] <= parent_element.location['x'] + parent_element.size['width'] and
                    child_element.location['y'] + child_element.size['height'] <= parent_element.location['y'] + parent_element.size['height']):
                    return True
        return False
    except StaleElementReferenceException:
        return False



def download_image(image_url, save_path, max_retries=5):
    if not domain_in_ad_servers(image_url, known_ad_servers):
        print(f"Skipping non-ad image: {image_url}")
        return
    for attempt in range(max_retries):
        try:
            response = requests.get(image_url)
            if response.status_code == 200:
                with open(save_path, 'wb') as file:
                    file.write(response.content)
                print(f"Image successfully downloaded to {save_path}")
                return
        except RequestException as e:
            print(f"Request exception occurred (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(1)  # Delay before retrying
    else:
        print(f"Failed to download image after {max_retries} retries")




def mark_and_log_ads(driver, save_path):
    ads_data = []
    parent_ad_elements = []
    ad_keywords = [
        ' ad ', ' ads', ' ads ' 'advert', 'advertisement', 'sponsored',
        'banner', 'promoted', 'promotion', 'doubleclick',
        'affiliates', 'placements', 'taboola', 'outbrain',
        'monetization', 'syndication', 'ppc', 'cpm', 'cpc',
        'interstitial', 'preroll', 'postroll', 'midroll',
        'media.net', 'AdSense', 'revcontent', 'buysellads',
        'popunder', 'pop-up', 'pop-over', 'skyscraper',
        ' sidebar', 'leaderboard', 'sticky', 'newsletter',
        '广告', '推广', '赞助',
        'anuncio', 'publicidad', 'patrocinado',
        'ad_hover_href'
    ]

    ad_tags = ['SCRIPT', 'IFRAME', 'DIV', 'IMG', 'INS', 'VIDEO', 'CANVAS', 'EMBED', 'OBJECT', 'SOURCE', 'SVG', 'TRACK']

    for tag in ad_tags:
        elements = driver.find_elements(By.TAG_NAME, tag)
        for element in elements:
            try:
                is_ad = False
                # Check attributes and text to identify ads
                for attribute in element.get_property('attributes'):
                    keyword_matches = [keyword for keyword in ad_keywords if keyword in attribute['value']]
                    if keyword_matches:
                        is_ad = True
                        break

                if is_ad and not is_descendant(element, parent_ad_elements, driver):
                # Highlight the ad
                    driver.execute_script("arguments[0].style.border='10px solid red'", element)
                    parent_ad_elements.append(element)
                # Check if element is visible and has size
                if element.is_displayed() and element.size['height'] > 0 and element.size['width'] > 0:
                    rect = element.rect
                    position_data = {
                        "url": driver.current_url,
                        "x": rect['x'],
                        "y": rect['y'],
                        "width": rect['width'],
                        "height": rect['height'],
                        "tag": tag,
                        "keyword": keyword_matches,
                        "image_urls": []
                    }

                    # Extracting image URLs
                    if tag == "IFRAME":
                        image_urls = find_images_in_iframe(driver, element)
                    elif tag == "DIV":
                        image_urls = find_images_in_div(driver, element)
                    else:
                        image_urls = [img.get_attribute('src') for img in element.find_elements(By.TAG_NAME, 'img') if img.get_attribute('src')]

                    for i, img_url in enumerate(image_urls):
                        image_filename = f"ad_{urlparse}_{len(ads_data)}_{element}_{tag}.png"
                        full_save_path = os.path.join(save_path, image_filename)
                        download_image(img_url, full_save_path)

                    position_data['image_urls'] = image_urls
                    ads_data.append(position_data)
            except:
                print("Element no longer in the DOM, skipping")
                continue


    return ads_data


def process_url(url, base_save_path):
    driver = webdriver.Chrome()

    # Create a unique save path for each URL
    url_save_path = os.path.join(base_save_path, urlparse(url).netloc.replace('.', '_'))
    os.makedirs(url_save_path, exist_ok=True)

    # Navigate to the URL
    driver.get(url)
    time.sleep(5)
    scroll_to_bottom(driver)

    # Process ads
    ads_data = mark_and_log_ads(driver, url_save_path)

    # Save the ad positions to a JSON file
    with open(os.path.join(url_save_path, 'ad_positions.json'), 'w') as f:
        json.dump(ads_data, f, indent=2)

    driver.quit()

def process_batch(urls, base_save_path, max_threads):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(process_url, url, base_save_path) for url in urls]

        # Wait for all threads in the batch to complete
        for future in concurrent.futures.as_completed(futures):
            future.result()  # This re-raises exceptions from the threads


if __name__ == "__main__":

    csv_file_path = '/Users/kaleemullahqasim/Documents/GitHub/AdIdentifer_Downloader/v0.2/200_only_ad.csv'
    # Read URLs from the CSV file
    urls_to_process = read_urls_from_csv(csv_file_path)
    # 10 URLs to process for testing
    urls_to_process = urls_to_process[:10]

    # save path
    base_save_path = '/Users/kaleemullahqasim/Desktop/Prof Xiu Hai Tao/data'
    os.makedirs(base_save_path, exist_ok=True)

    max_threads = 1

    batch_size = 1
    for i in range(0, len(urls_to_process), batch_size):
        batch_urls = urls_to_process[i:i + batch_size]
        process_batch(batch_urls, base_save_path, max_threads)
        time.sleep(2)
