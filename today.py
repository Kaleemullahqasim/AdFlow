import os
import csv
import json
import time
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import concurrent.futures
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import logging

logging.basicConfig(filename='ad_processing.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_urls_from_csv(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        return [row[0] for row in reader]


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

def find_images_in_canvas(driver, canvas_element):
    # Attempt to get the canvas content as a data URL
    img_data_url = driver.execute_script("return arguments[0].toDataURL('image/png');", canvas_element)
    return [img_data_url] if img_data_url else []



def extract_image_urls_from_element(driver, element, tag):
    if tag == "IFRAME":
        return find_images_in_iframe(driver, element)
    elif tag == "DIV":
        return find_images_in_div(driver, element)
    elif tag == "SVG":
        return find_images_in_svg(driver, element)
    elif tag in ["EMBED", "OBJECT"]:
        return find_images_in_embed_and_object(driver, element, tag)
    elif tag == "CANVAS":
        return find_images_in_canvas(driver, element)  # Assuming you have a method to handle canvas
    elif tag == "VIDEO":
        poster_url = element.get_attribute('poster')
        return [poster_url] if poster_url else []
    elif tag == "SOURCE":
        srcset_urls = element.get_attribute('srcset')
        return srcset_urls.split(", ") if srcset_urls else []
    else:
        return [img.get_attribute('src') for img in element.find_elements(By.TAG_NAME, 'img') if img.get_attribute('src')]

def find_images_in_iframe(driver, iframe_element):
    driver.switch_to.frame(iframe_element)
    img_elements = iframe_element.find_elements(By.TAG_NAME, 'img')
    img_urls = [img.get_attribute('src') for img in img_elements if img.get_attribute('src')]
    driver.switch_to.default_content()
    return img_urls

def find_images_in_div(driver, div_element):
    img_urls = []
    img_elements = div_element.find_elements(By.TAG_NAME, 'img')
    img_urls.extend([img.get_attribute('src') for img in img_elements if img.get_attribute('src')])
    style = div_element.get_attribute('style')
    if style and 'background-image' in style:
        bg_url = style.split('url(')[1].split(')')[0].replace('"', '').replace("'", '').strip()
        if bg_url:
            img_urls.append(bg_url)
    return img_urls

def find_images_in_svg(driver, svg_element):
    img_elements = svg_element.find_elements(By.TAG_NAME, 'image')
    img_urls = [img.get_attribute('href') or img.get_attribute('xlink:href') for img in img_elements if img.get_attribute('href') or img.get_attribute('xlink:href')]
    return img_urls

def find_images_in_embed_and_object(driver, element, tag_name):
    img_urls = []
    if tag_name.lower() == 'embed':
        src = element.get_attribute('src')
        if src:
            img_urls.append(src)
    elif tag_name.lower() == 'object':
        data = element.get_attribute('data')
        if data:
            img_urls.append(data)
        nested_imgs = element.find_elements(By.TAG_NAME, 'img')
        img_urls.extend([img.get_attribute('src') for img in nested_imgs if img.get_attribute('src')])
    return img_urls



def mark_and_log_ads(driver, save_path):
    ads_data = []
    parent_ad_elements = []
    total_ads = 0

    for tag in ad_tags:
        elements = driver.find_elements(By.TAG_NAME, tag)
        for element in elements:
            for attribute in element.get_property('attributes'):
                keyword_matches = [keyword for keyword in ad_keywords if keyword in attribute['value']]
                if keyword_matches:
                    if not is_descendant(element, parent_ad_elements):
                        parent_ad_elements.append(element)
                        rect = element.rect
                        # check the conditions of ads position if they are above 5 then we will save the image
                        if rect['x'] > 10 and rect['y'] > 10 and rect['width'] > 10 and rect['height'] > 10:
                            total_ads += 1
                            ad_info = {
                            "url": driver.current_url,
                            "x": rect['x'],
                            "y": rect['y'],
                            "width": rect['width'],
                            "height": rect['height'],
                            "keywords": keyword_matches,
                            "tag": tag
                            }

                            # Check for image URL in the ad element
                            img_urls = extract_image_urls_from_element(driver, element, tag)
                            ad_info['image_urls'] = img_urls
                            ads_data.append(ad_info)


    return ads_data, total_ads

def process_url(url, base_save_path, all_ads_summary):
    driver = None
    try:
        options = Options()
        options.add_argument('--headless')  
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        ads_data, total_ads = mark_and_log_ads(driver, base_save_path)
        ads_summary = {
            'url': url,
            'total_ads': total_ads,
            'ads': ads_data
        }

        # Save individual URL data
        url_specific_json_path = os.path.join(base_save_path, urlparse(url).netloc + '.json')
        with open(url_specific_json_path, 'w') as f:
            json.dump(ads_summary, f, indent=2)

        # Append data to all ads summary
        all_ads_summary.append(ads_summary)

        logging.info(f"Processed URL: {url} with {total_ads} ads")

    except (NoSuchElementException, TimeoutException) as e:
        logging.error(f"Element not found or page load timeout for {url}: {e}")
    except WebDriverException as e:
        logging.error(f"WebDriver error for {url}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error for {url}: {e}")
    finally:
        if driver:
            driver.quit()


def process_batch(urls, base_save_path, max_threads, all_ads_summary):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(process_url, url, base_save_path, all_ads_summary) for url in urls]
        for future in concurrent.futures.as_completed(futures):
            future.result()

def main():
    csv_file_path = 'urls.csv'
    base_save_path = '/Users/kaleemullahqasim/Desktop/Prof Xiu Hai Tao/data'
    os.makedirs(base_save_path, exist_ok=True)

    urls_to_process = read_urls_from_csv(csv_file_path)
    all_ads_summary = []  # List to store data of all URLs

    max_threads = 15
    batch_size = 10

    for i in range(0, len(urls_to_process), batch_size):
        batch_urls = urls_to_process[i:i + batch_size]
        process_batch(batch_urls, base_save_path, max_threads, all_ads_summary)
        time.sleep(3)

    # Save parent JSON with data from all URLs
    parent_json_path = os.path.join(base_save_path, 'all_ads_summary.json')
    with open(parent_json_path, 'w') as f:
        json.dump(all_ads_summary, f, indent=2)

    logging.info("All URLs processed")

if __name__ == "__main__":
    main()