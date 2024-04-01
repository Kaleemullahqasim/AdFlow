import keyword
import os
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
import json
from time import sleep
import string
import requests
from selenium.common.exceptions import StaleElementReferenceException
from ad_servers_list import known_ad_servers
import time
from requests.exceptions import RequestException
import csv 
import concurrent.futures
from ad_servers_list import known_ad_servers
import base64

def read_urls_from_csv(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        return [row[0] for row in reader]

def domain_in_ad_servers(url, ad_servers):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return any(ad_server in domain for ad_server in ad_servers)

def scroll_to_bottom(driver, step_size=100, delay=0.5):
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down by `step_size`
        driver.execute_script(f"window.scrollBy(0, {step_size});")

        # Wait for page to load
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

def find_images_in_canvas(driver, canvas_element):
    # Extracts screenshot from a canvas element
    img_data_url = driver.execute_script("return arguments[0].toDataURL('image/png');", canvas_element)
    return [img_data_url]

def find_images_in_svg(driver, svg_element):
    # Extract images from <svg> elements
    img_urls = []
    img_elements = svg_element.find_elements(By.TAG_NAME, 'image')
    img_urls.extend([img.get_attribute('href') or img.get_attribute('xlink:href') for img in img_elements if img.get_attribute('href') or img.get_attribute('xlink:href')])
    return img_urls


def find_images_in_video(driver, video_element):
    # Extracts the poster image from a video element
    poster_url = video_element.get_attribute('poster')
    return [poster_url] if poster_url else []

def find_images_in_embed_and_object(driver, element, tag_name):
    # Attempt to extract image URLs from embed and object elements
    img_urls = []

    if tag_name.lower() == 'embed':
        # For embed elements, try to extract using src attribute
        src = element.get_attribute('src')
        if src:
            img_urls.append(src)

    elif tag_name.lower() == 'object':
        # For object elements, check for data attribute
        data = element.get_attribute('data')
        if data:
            img_urls.append(data)

        # Additionally, check for nested <img> elements
        nested_imgs = element.find_elements(By.TAG_NAME, 'img')
        for img in nested_imgs:
            img_src = img.get_attribute('src')
            if img_src:
                img_urls.append(img_src)

    return img_urls

def find_images_in_source(driver, source_element):
    # Extracts source URL from source elements
    src_url = source_element.get_attribute('src')
    return [src_url] if src_url else []

def find_background_image(driver, element):
    # Extracts background-image from elements with CSS background
    style = driver.execute_script("return window.getComputedStyle(arguments[0], null).getPropertyValue('background-image');", element)
    if style and 'url(' in style:
        bg_img_url = style.split('url(')[1].split(')')[0].replace('"', '').replace("'", '')
        return [bg_img_url]
    return []



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
        # Re-find the child_element and try again, or handle it in another way
        return False

def download_image(image_url, save_path, is_from_ad_server, image_filename):
    # Determine the subfolder based on the image source
    subfolder = "from_adserver" if is_from_ad_server else "not_from_adserver"
    full_save_path = os.path.join(save_path, subfolder, image_filename)

    os.makedirs(os.path.join(save_path, subfolder), exist_ok=True)

    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(full_save_path, 'wb') as file:
                file.write(response.content)
            print(f"Image successfully downloaded to {full_save_path}")
        else:
            print(f"Failed to download {image_url}: Status code {response.status_code}")
    except requests.RequestException as e:
        print(f"Error downloading {image_url}: {e}")



# Functions for finding images (find_images_in_iframe, find_images_in_div, etc.) remain unchanged

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
        'anuncio', 'publicidad', 'patrocinado', 'Advertisement'
        'ad_hover_href'
    ]
    ad_tags = ['SCRIPT', 'IFRAME', 'DIV', 'IMG', 'INS', 'VIDEO', 'CANVAS', 'EMBED', 'OBJECT', 'SOURCE', 'SVG', 'TRACK']

    for tag in ad_tags:
        elements = driver.find_elements(By.TAG_NAME, tag)
        for element in elements:
            is_ad = False
            for attribute in element.get_property('attributes'):
                keyword_matches = [keyword for keyword in ad_keywords if keyword in attribute['value']]
                if keyword_matches:
                    is_ad = True
                    break

            if is_ad and not is_descendant(element, parent_ad_elements, driver):
                driver.execute_script("arguments[0].style.border='10px solid red'", element)
                parent_ad_elements.append(element)

                if element.is_displayed() and element.size['height'] > 0 and element.size['width'] > 0:
                    rect = element.rect
                    position_data = {
                        "url": driver.current_url,
                        "x": rect['x'],
                        "y": rect['y'],
                        "width": rect['width'],
                        "height": rect['height'],
                        "tag": tag,
                        "keyword": keyword_matches[0] if keyword_matches else None,
                        "image_urls": [],
                    }

                    image_urls = find_images_in_iframe(driver, element) if tag == "IFRAME" else \
                                 find_images_in_div(driver, element) if tag == "DIV" else \
                                 find_images_in_svg(driver, element) if tag == "SVG" else \
                                 find_images_in_embed_and_object(driver, element, tag) if tag in ["EMBED", "OBJECT"] else \
                                 [element.get_attribute('poster')] if tag == "VIDEO" and element.get_attribute('poster') else \
                                 element.get_attribute('srcset').split(", ") if tag == "SOURCE" and element.get_attribute('srcset') else \
                                 [img.get_attribute('src') for img in element.find_elements(By.TAG_NAME, 'img') if img.get_attribute('src')]

                    for i, img_url in enumerate(image_urls):
                        image_filename = f"ad_{len(ads_data)}_{i}.png"
                        is_from_ad_server = domain_in_ad_servers(img_url, known_ad_servers)
                        download_image(img_url, save_path, is_from_ad_server, image_filename)

                    position_data['image_urls'] = image_urls
                    ads_data.append(position_data)

    return ads_data

def process_url(url, base_save_path):
    try:
        driver = webdriver.Chrome()
        url_save_path = os.path.join(base_save_path, urlparse(url).netloc.replace('.', '_'))
        os.makedirs(url_save_path, exist_ok=True)

        driver.get(url)
        time.sleep(5)
        scroll_to_bottom(driver)

        ads_data = mark_and_log_ads(driver, url_save_path)
        with open(os.path.join(url_save_path, 'ad_positions.json'), 'w') as f:
            json.dump(ads_data, f, indent=2)
    except Exception as e:
        print(f"Error Processing {url}: {e}")
    
    finally:
        if 'driver' in locals():
            driver.quit()


def process_batch(urls, base_save_path, max_threads):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(process_url, url, base_save_path) for url in urls]
        for future in concurrent.futures.as_completed(futures):
            future.result()  # Re-raises exceptions from the threads

if __name__ == "__main__":
    csv_file_path = 'urls.csv'  # Path to your CSV file
    base_save_path = '/Users/kaleemullahqasim/Desktop/Prof Xiu Hai Tao/test_with_ad_server/'
    os.makedirs(base_save_path, exist_ok=True)

    urls_to_process = read_urls_from_csv(csv_file_path)
    
    
    
    max_threads = 4
    batch_size = 4

    for i in range(0, len(urls_to_process), batch_size):
        batch_urls = urls_to_process[i:i + batch_size]
        process_batch(batch_urls, base_save_path, max_threads)
        time.sleep(5)