import os
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
import json
from time import sleep
import string
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd
import time 
import concurrent.futures
import os
import json
import pandas as pd
import concurrent.futures
from tqdm import tqdm


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


ad_tags = ['SCRIPT', 'IFRAME', 'DIV', 'IMG', 'INS', 'VIDEO', 'CANVAS', 'EMBED', 'OBJECT', 'SOURCE', 'SVG', 'TRACK',]


def is_descendant(driver, child_element, parent_elements):
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
        # Re-fetch the child element and retry the check
        updated_child_element = driver.find_element(child_element.tag_name, child_element.id)
        return is_descendant(driver, updated_child_element, parent_elements)
    
def mark_and_log_ads_in_viewport(driver):
    ads_data = []
    saved_ads_identifiers = set()  # To track unique ads
    parent_ad_elements = []  # To track parent ad elements

    for tag in ad_tags:
        elements = driver.find_elements(By.TAG_NAME, tag)
        for element in elements:
            try:
                # Ensure the element meets the basic display and position criteria
                if element.is_displayed():
                    rect = element.rect
                    if rect['x'] > 10 and rect['y'] > 10:
                        for attribute in element.get_property('attributes'):
                            keyword_matches = [keyword for keyword in ad_keywords if keyword in attribute['value']]
                            if keyword_matches:
                                # Create a unique identifier for the ad
                                ad_identifier = f"{rect['x']}_{rect['y']}_{rect['width']}_{rect['height']}_{tag}"
                                if ad_identifier not in saved_ads_identifiers:
                                    position_data = {
                                        "url": driver.current_url,
                                        "x": rect['x'],
                                        "y": rect['y'],
                                        "width": rect['width'],
                                        "height": rect['height'],
                                        "keywords": keyword_matches,
                                        "tag": tag
                                    }

                                    # Check if this ad is a child of a saved parent ad
                                    is_child_of_saved_parent = False
                                    for parent_element in parent_ad_elements:
                                        if element in parent_element.find_elements(By.XPATH, ".//*"):
                                            is_child_of_saved_parent = True
                                            break

                                    if not is_child_of_saved_parent:
                                        ads_data.append(position_data)
                                        saved_ads_identifiers.add(ad_identifier)
                                        parent_ad_elements.append(element)
            except StaleElementReferenceException:
                continue

    return ads_data


# def mark_and_log_ads_in_viewport(driver, save_path):
#     ads_data = []
#     parent_ad_elements = []  # Keep track of parent ad elements

#     for tag in ad_tags:
#         elements = driver.find_elements(By.TAG_NAME, tag)
#         for element in elements:
#             try:
#                 for attribute in element.get_property('attributes'):
#                     keyword_matches = [keyword for keyword in ad_keywords if keyword in attribute['value']]
#                     if keyword_matches and element.is_displayed():
#                         original_style = driver.execute_script("var element = arguments[0]; var originalStyle = element.getAttribute('style'); element.style.border='10px solid red'; return originalStyle;", element)
#                         parent_ad_elements.append(element)

#                         rect = element.rect
#                         position_data = {
#                             "url": driver.current_url,
#                             "x": rect['x'],
#                             "y": rect['y'],
#                             "width": rect['width'],
#                             "height": rect['height'],
#                             "keywords": keyword_matches,
#                             "tag": tag
#                         }
#                         ads_data.append(position_data)

#                         driver.execute_script("arguments[0].setAttribute('style', arguments[1])", element, original_style)
#                         break  
#             except StaleElementReferenceException:
#                 continue

#     return ads_data

# def scroll_and_capture_ads(driver, url):
#     """
#     Modified function to accept a URL and use a WebDriver instance to scroll through
#     the page and capture ads data.
#     """
#     driver.get(url)
#     sleep(5)  # Wait for the initial page to load
#     all_ads_data = []
#     last_height = driver.execute_script("return document.body.scrollHeight")
#     while True:
#         driver.execute_script("window.scrollBy(0, window.innerHeight);")
#         sleep(2)  # Wait for the page to load after scrolling
#         ads_data = mark_and_log_ads_in_viewport(driver, url)  # Pass URL instead of save_path
#         all_ads_data.extend(ads_data)
#         new_height = driver.execute_script("return document.body.scrollHeight")
#         if new_height == last_height:
#             break  # Break if we've reached the bottom
#         last_height = new_height
#     return all_ads_data


def scroll_and_capture_ads(driver, url):
    driver.get(url)
    sleep(5)  # Wait for the initial page to load
    all_ads_data = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollBy(0, window.innerHeight);")
        sleep(2)  # Wait for the page to load after scrolling
        ads_data = mark_and_log_ads_in_viewport(driver)  # Adjusted to pass only 'driver'
        all_ads_data.extend(ads_data)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  # Break if we've reached the bottom
        last_height = new_height
    return all_ads_data





def process_url(url):
    """
    Processes a single URL for ad data collection using a headless WebDriver instance.
    """
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    with webdriver.Chrome(options=options) as driver:
        ad_data = scroll_and_capture_ads(driver, url)
        return ad_data

# def main(urls_to_process, save_path):
#     """
#     Processes a list of URLs concurrently using multithreading and saves the collected ad data.
#     """
#     os.makedirs(save_path, exist_ok=True)
#     all_ads_data = []
    
#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         # Map the process_url function over the URLs to process them concurrently
#         future_to_url = [executor.submit(process_url, url) for url in urls_to_process]
#         for future in concurrent.futures.as_completed(future_to_url):
#             try:
#                 ad_data = future.result()
#                 all_ads_data.extend(ad_data)
#             except Exception as exc:
#                 print(f'An exception occurred: {exc}')
    
#     # Save the aggregated data from all URLs after processing
#     if all_ads_data:
#         with open(os.path.join(save_path, 'ad_positions.json'), 'w') as f:
#             json.dump(all_ads_data, f, indent=2)
#     else:
#         print("No ad data was collected.")

# if __name__ == '__main__':
#     urls_csv_path = '/Users/kaleemullahqasim/Documents/GitHub/AdIdentifer_Downloader/v0.2/200_only_ad.csv'
#     urls_to_process = pd.read_csv(urls_csv_path)['url'].tolist()[:30] 
#     save_path = '/Users/kaleemullahqasim/Desktop/Prof Xiu Hai Tao/data/'
#     main(urls_to_process, save_path)


def main(urls_to_process, save_path):
    """
    Processes a list of URLs concurrently using multithreading and saves the collected ad data.
    """
    os.makedirs(save_path, exist_ok=True)
    all_ads_data = []
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Create a list of futures for concurrent processing
        futures = [executor.submit(process_url, url) for url in urls_to_process]

        # Initialize tqdm for progress tracking
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing URLs"):
            try:
                ad_data = future.result()
                all_ads_data.extend(ad_data)
            except Exception as exc:
                print(f'An exception occurred: {exc}')
    
    # Save the aggregated data from all URLs after processing
    if all_ads_data:
        with open(os.path.join(save_path, 'ad_positions.json'), 'w') as f:
            json.dump(all_ads_data, f, indent=2)
    else:
        print("No ad data was collected.")

if __name__ == '__main__':
    urls_csv_path = '/Users/kaleemullahqasim/Documents/GitHub/AdIdentifer_Downloader/v0.2/200_only_ad.csv'
    urls_to_process = pd.read_csv(urls_csv_path)['url'].tolist()  
    save_path = '/Users/kaleemullahqasim/Desktop/Prof Xiu Hai Tao/data/'
    main(urls_to_process, save_path)