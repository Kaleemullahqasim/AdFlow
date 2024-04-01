from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
import os 

# Initialize the WebDriver
driver = webdriver.Chrome()

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
ad_tags = ['SCRIPT', 'IFRAME', 'DIV', 'IMG', 'INS', 'VIDEO', 'CANVAS', 'EMBED', 'OBJECT', 'SOURCE', 'SVG', 'TRACK',]

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
                    if rect['x'] > 5 and rect['y'] > 5 and rect['width'] > 5 and rect['height'] > 5:
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



# Process a list of URLs
urls_to_process = ['https://www.espncricinfo.com/']  # Your list of URLs
all_ads_data = []

for url in urls_to_process:
    driver.get(url)
    sleep(5)  # Wait for the page to load and ads to appear
    ads_data = mark_and_log_ads(driver)
    all_ads_data.extend(ads_data)

# Save the ad positions to a JSON file
with open('ad_positions.json', 'w') as f:
    json.dump(all_ads_data, f, indent=2)

driver.quit()