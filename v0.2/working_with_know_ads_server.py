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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException
from requests.exceptions import RequestException
import csv
import concurrent.futures
from ad_servers_list import known_ad_servers
from selenium.common.exceptions import WebDriverException
from tqdm import tqdm  # Import tqdm


def domain_in_ad_servers(url, ad_servers):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return any(ad_server in domain for ad_server in ad_servers)



def scroll_to_bottom(driver, pages=3):
    import time
    # Get the height of the window (viewport)
    viewport_height = driver.execute_script("return window.innerHeight;")
    # Scroll down three times the viewport height
    for _ in range(pages):
        # Scroll by one viewport height
        driver.execute_script(f"window.scrollBy(0, {viewport_height});")
        # Wait for 1 second to allow the page to load more content
        time.sleep(1)

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
        ' ad ', ' ads', ' ads ', 'advert', 'advertisement', 'sponsored',
        'banner', 'promoted', 'promotion', 'doubleclick',
        'affiliates', 'placements', 'taboola', 'outbrain',
        'monetization', 'syndication', 'ppc', 'cpm', 'cpc',
        'interstitial', 'preroll', 'postroll', 'midroll',
        'media.net', 'AdSense', 'revcontent', 'buysellads',
        'popunder', 'pop-up', 'pop-over', 'skyscraper',
        'sidebar', 'leaderboard', 'sticky', 'newsletter',
        'ad_hover_href'
    ]

    ad_tags = ['SCRIPT', 'IFRAME', 'DIV', 'IMG', 'INS', 'VIDEO']

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

                # Check if ad is from a known ad server
                if is_ad:
                    image_urls = [img.get_attribute('src') for img in element.find_elements(By.TAG_NAME, 'img') if img.get_attribute('src')]
                    ad_server_image_urls = [img_url for img_url in image_urls if domain_in_ad_servers(img_url, known_ad_servers)]
                    
                    if ad_server_image_urls and not is_descendant(element, parent_ad_elements, driver):
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
                                "keyword": keyword_matches,
                                "image_urls": ad_server_image_urls
                            }
                            ads_data.append(position_data)
                            # Downloading and logging only ad server images
                            for img_url in ad_server_image_urls:
                                image_filename = sanitize_filename(f"ad_{urlparse(img_url).netloc}_{len(ads_data)}_{tag}.png")
                                full_save_path = os.path.join(save_path, image_filename)
                                download_image(img_url, full_save_path)
            except StaleElementReferenceException:
                print("Element no longer in the DOM, skipping")
                continue

    # Save the ad positions to a JSON file only if there are ads from known ad servers
    if ads_data:
        with open(os.path.join(save_path, 'ad_positions.json'), 'w') as f:
            json.dump(ads_data, f, indent=2)

    return ads_data

def process_url(url, base_save_path):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    try:
        if not url or not urlparse(url).scheme:
            raise ValueError(f"Invalid URL: {url}")
        print(f"Processing URL: {url}")
        url_save_path = os.path.join(base_save_path, urlparse(url).netloc.replace('.', '_'))
        os.makedirs(url_save_path, exist_ok=True)
        driver.get(url)
        # Use WebDriverWait to ensure the initial page is loaded
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        # Scroll down 3 pages
        scroll_to_bottom(driver, 3)
        ads_data = mark_and_log_ads(driver, url_save_path)
        if ads_data:
            with open(os.path.join(url_save_path, 'ad_positions.json'), 'w') as f:
                json.dump(ads_data, f, indent=2)
    except WebDriverException as e:
        print(f"WebDriver error with URL {url}: {str(e)}")
    except Exception as e:
        print(f"Error processing URL {url}: {str(e)}")
    finally:
        driver.quit()
    print(f"Completed URL: {url}")

    return


def read_urls_from_csv(file_path):
    urls = []
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in tqdm(reader, desc="Reading URLs"):
            urls.append(row[0])
    return urls

def process_batch(urls, base_save_path, max_threads):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = []
        for url in urls:
            futures.append(executor.submit(process_url, url, base_save_path))
        
        # Track the progress of futures completion using tqdm
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing URLs"):
            future.result()  # This re-raises exceptions from the threads



if __name__ == "__main__":
    csv_file_path = '/Users/kaleemullahqasim/Documents/GitHub/AdIdentifer_Downloader/v0.2/200_of_all_URLs.csv'
    urls_to_process = read_urls_from_csv(csv_file_path)
    urls_to_process = urls_to_process[:200]

    base_save_path = '/Users/kaleemullahqasim/Desktop/Prof Xiu Hai Tao/data'
    os.makedirs(base_save_path, exist_ok=True)

    max_threads = 20
    batch_size = 10

    for i in tqdm(range(0, len(urls_to_process), batch_size), desc="Batch Progress"):
        batch_urls = urls_to_process[i:i + batch_size]
        process_batch(batch_urls, base_save_path, max_threads)
        time.sleep(2)
