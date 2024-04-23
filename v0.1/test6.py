import os
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import json
from time import sleep
import string
import time
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException



# def scroll_incrementally(driver, increments=10):
#     """Scroll the page incrementally to load ads more naturally."""
#     total_height = driver.execute_script("return document.body.scrollHeight")
#     for i in range(1, increments + 1):
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight * %s / %s);" % (i, increments))
#         sleep(2)  # Adjust sleep time as needed

def sanitize_filename(filename):
    """Sanitize the filename by removing invalid characters and ensuring it ends with .png"""
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    cleaned_filename = ''.join(c for c in filename if c in valid_chars)
    if not cleaned_filename.lower().endswith('.png'):
        cleaned_filename += '.png'
    return cleaned_filename


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
    

def mark_and_log_ads_in_viewport(driver, save_path):
    ads_data = []
    parent_ad_elements = []  # Keep track of parent ad elements

    for tag in ad_tags:
        elements = driver.find_elements(By.TAG_NAME, tag)
        for element in elements:
            try:
                for attribute in element.get_property('attributes'):
                    keyword_matches = [keyword for keyword in ad_keywords if keyword in attribute['value']]
                    if keyword_matches and element.is_displayed():
                        original_style = driver.execute_script("var element = arguments[0]; var originalStyle = element.getAttribute('style'); element.style.border='10px solid red'; return originalStyle;", element)
                        parent_ad_elements.append(element)

                        rect = element.rect
                        position_data = {
                            "url": driver.current_url,
                            "x": rect['x'],
                            "y": rect['y'],
                            "width": rect['width'],
                            "height": rect['height'],
                            "keywords": keyword_matches,
                            "tag": tag
                        }
                        ads_data.append(position_data)

                        # Remove the red border before taking the screenshot
                        driver.execute_script("arguments[0].style.border='none'", element)
                        screenshot_filename = sanitize_filename(f"{urlparse(driver.current_url).netloc}_{tag}_{int(time.time())}.png")
                        element.screenshot(os.path.join(save_path, screenshot_filename))
                        # Reapply the original style after taking the screenshot
                        driver.execute_script("arguments[0].setAttribute('style', arguments[1])", element, original_style)
                        break  # No need to check other attributes if one matches
            except StaleElementReferenceException:
                # Skip the current element if it becomes stale
                continue

    return ads_data

def scroll_and_capture_ads(driver, save_path):
    all_ads_data = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # Scroll down by one viewport height
        driver.execute_script("window.scrollBy(0, window.innerHeight);")
        sleep(2)  # Wait for the page to load after scrolling

        # Mark ads in the current viewport and log them
        ads_data = mark_and_log_ads_in_viewport(driver, save_path)
        all_ads_data.extend(ads_data)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  # Break if we've reached the bottom
        last_height = new_height

    return all_ads_data

# Initialize the WebDriver with headless option
options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)
save_path = '/Users/kaleemullahqasim/Desktop/Prof Xiu Hai Tao/data/'
os.makedirs(save_path, exist_ok=True)

# Process a list of URLs
urls_to_process = ['https://tweaklibrary.com/image-downloader-extensions-for-chrome/#google_vignette']  # Replace with your URLs
for url in urls_to_process:
    driver.get(url)
    sleep(5)  # Wait for initial page load
    all_ads_data = scroll_and_capture_ads(driver, save_path)

# Save the ad positions to a JSON file
with open('test.json', 'w') as f:
    json.dump(all_ads_data, f, indent=2)

driver.quit()