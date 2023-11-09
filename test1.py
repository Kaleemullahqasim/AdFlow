import logging
import requests
from bs4 import BeautifulSoup
from seleniumwire import webdriver
from selenium.common.exceptions import WebDriverException
from adblockparser import AdblockRules
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load Adblock rules
def load_rules(path_to_easylist):
    try:
        with open(path_to_easylist, 'r', encoding='utf-8') as f:
            raw_rules = f.readlines()
        return AdblockRules(raw_rules)
    except Exception as e:
        logging.error(f"Failed to load adblock rules: {e}")
        return None

# Initialize WebDriver
def initialize_webdriver():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        return driver
    except WebDriverException as e:
        logging.error(f"WebDriver initialization error: {e}")
        return None

def process_website(driver, engine, url, path_to_ads_folder, path_to_non_ads_folder):
    try:
        driver.get(url)
        logging.info(f"Processing page: {url}")
        has_ads = False

        # Check network requests for ad images
        for request in driver.requests:
            if request.response:
                status_code = request.response.status_code
                content_type = request.response.headers.get('Content-Type', '')
                if 'image' in content_type and status_code == 200:
                    image_url = request.url
                    if engine.should_block(image_url):
                        has_ads = True
                        logging.info(f"Ad image detected: {image_url}")
                        save_image(image_url, path_to_ads_folder)
                else:
                    logging.info(f"Non-image or non-content response detected, skipping URL: {request.url}")

        if not has_ads:
            logging.info(f"No ad images found on {url}, skipping.")
            return

        # Continue processing for non-ad images
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        images = soup.find_all('img')
        logging.info(f"Found {len(images)} image(s) on the page.")

        for image in images:
            src = image.get('src')
            if not src:
                logging.info(f"Image tag without src found, skipping.")
                continue
            image_url = urljoin(driver.current_url, src)

            # We already processed ad images from network requests, now save non-ad images
            if not engine.should_block(image_url):
                logging.info(f"Processing non-ad image: {image_url}")
                save_image(image_url, path_to_non_ads_folder)

    except WebDriverException as e:
        logging.error(f"Error processing website {url}: {e}")
    except Exception as e:
        logging.error(f"An error occurred while processing the page: {url}, error: {e}")



# Save an image from URL to the specified folder
def save_image(image_url, folder_path):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            image_name = image_url.split('/')[-1]
            image_path = f"{folder_path}/{image_name}"
            with open(image_path, 'wb') as file:
                file.write(response.content)
            logging.info(f"Image saved to {image_path}")
        else:
            logging.error(f"Image at {image_url} could not be downloaded. Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error during image download: {e}")

# Define paths
easylist_path = 'easylist.txt'
ads_folder_path = '/Users/kaleemullahqasim/Desktop/Prof Xiu Hai Tao/ads/'
non_ads_folder_path = '/Users/kaleemullahqasim/Desktop/Prof Xiu Hai Tao/non-ads/'

# Main execution
if __name__ == "__main__":
    rules_engine = load_rules(easylist_path)
    if rules_engine:
        web_driver = initialize_webdriver()
        if web_driver:
            try:
                # List of websites to process
                websites_to_process = ['http://fllwrs.com/']

                for website in websites_to_process:
                    process_website(web_driver, rules_engine, website, ads_folder_path, non_ads_folder_path)

            except Exception as e:
                logging.error(f"Unexpected error: {e}")
            finally:
                web_driver.quit()
                logging.info("WebDriver quit successfully.")
