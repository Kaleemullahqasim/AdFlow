import os
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
import json
from time import sleep
import string
import time 
from urllib.parse import urlparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import string


def scroll_to_bottom(driver):
    """Scroll to the bottom of the page."""
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # Wait for the page to load completely
    sleep(5)

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
    parent_ad_elements = []

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

                        if element.is_displayed() and element.size['height'] > 0 and element.size['width'] > 0:
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

                            # Extracting image URLs from img tags
                            img_elements = element.find_elements(By.TAG_NAME, 'img')
                            img_urls = [img.get_attribute('src') for img in img_elements if img.get_attribute('src')]
                            print(f"Found {len(img_urls)} image URLs in img tags")  # Debug print

                            # Extracting background images
                            bg_image = driver.execute_script(
                                "return window.getComputedStyle(arguments[0], null).backgroundImage.slice(4, -1).replace(/['\"]+/g, '');",
                                element
                            )
                            if bg_image and bg_image != 'none':
                                img_urls.append(bg_image)
                                print(f"Found background image URL: {bg_image}")  # Debug print

                            position_data['image_urls'] = img_urls
                            ads_data.append(position_data)
                        break

    return ads_data



# Initialize the WebDriver
driver = webdriver.Chrome()

# Define your save path
save_path = '/Users/kaleemullahqasim/Desktop/Prof Xiu Hai Tao/data/'  # Replace with your actual path
os.makedirs(save_path, exist_ok=True)  # Create the directory if it does not exist

# Process a list of URLs
urls_to_process = ['https://www.espncricinfo.com/']  # Your list of URLs
all_ads_data = []

for url in urls_to_process:
    driver.get(url)
    sleep(5)  # Wait for initial page load
    scroll_to_bottom(driver)  # Scroll to the end of the page
    ads_data = mark_and_log_ads(driver, save_path)
    all_ads_data.extend(ads_data)

# Save the ad positions to a JSON file
with open('ad_positions.json', 'w') as f:
    json.dump(all_ads_data, f, indent=2)

driver.quit()
