from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep
import json
import threading
import os

# Define the adKeywords and adTags
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
ad_tags = [
        'SCRIPT', 'IFRAME', 'DIV', 'IMG', 'INS', 'VIDEO', 'CANVAS', 'EMBED', 'OBJECT', 'SOURCE', 'SVG', 'TRACK',
    ]

# Initialize Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode

# Function to mark ads and log their positions
def mark_and_log_ads(driver):
    ads_data = []
    for tag in ad_tags:
        elements = driver.find_elements(By.TAG_NAME, tag)
        for element in elements:
            for attribute in element.get_property('attributes'):
                keyword_matches = [keyword for keyword in ad_keywords if keyword in attribute['value']]
                if keyword_matches:
                    # Highlight the ad
                    driver.execute_script("arguments[0].style.border='10px solid red'", element)
                    # Get and log the ad's position
                    rect = element.rect
                    if rect['x'] > 0 and rect['y'] > 0 and rect['width'] > 0 and rect['height'] > 0:
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
                        # Take a screenshot of the ad
                        element.screenshot(f"{driver.current_url}_{tag}.png")
                    break  # No need to check other attributes if one matches
    return ads_data

# Function to handle each URL
def process_url(url):
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    sleep(5)  # Wait for the page to load and ads to appear
    ads_data = mark_and_log_ads(driver)
    # Save non-ad images
    images = driver.find_elements(By.TAG_NAME, 'img')
    non_ads_images = [img for img in images if '10px solid red' not in img.get_attribute('style')]
    for img in non_ads_images:
        src = img.get_attribute('src')
        if src:
            # Download the image
            driver.get(src)
            driver.save_screenshot(f"non_ads_{os.path.basename(src)}")
            driver.get(url)  # Go back to the original page after downloading
    driver.quit()
    return ads_data

# Multithreading to process multiple URLs
def threaded_process(urls):
    threads = []
    all_ads_data = []

    for url in urls:
        thread = threading.Thread(target=lambda q, arg1: q.append(process_url(arg1)), args=(all_ads_data, url))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    # Save the ad positions to a JSON file
    with open('ad_positions.json', 'w') as f:
        json.dump(all_ads_data, f, indent=2)

# List of URLs to process
urls_to_process = ['https://www.espncricinfo.com/' , 'https://www.speedtest.net/']

# Start the multithreaded processing
threaded_process(urls_to_process)
