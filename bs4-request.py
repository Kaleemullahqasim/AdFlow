import requests
from bs4 import BeautifulSoup
import os

def parse_easylist(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    css_selectors = []

    for line in lines:
        # Ignore comments, empty lines, and unsupported pseudo-classes
        if line.startswith('!') or not line.strip() or ':-abp-' in line:
            continue

        # CSS selectors
        if '##' in line:
            css_selectors.append(line.split('##')[1].strip())

    return css_selectors


def download_image(url, save_path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
    except Exception as e:
        print(f"Error downloading image: {e}")

def fetch_and_save_ad_images(url, css_selectors, save_directory):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        for i, pattern in enumerate(css_selectors):
            for element in soup.select(pattern):
                img_src = element.get('src')
                if img_src and img_src.startswith(('http', 'https')):
                    filename = f"ad_{i}.png"
                    save_path = os.path.join(save_directory, filename)
                    download_image(img_src, save_path)
    except Exception as e:
        print(f"Error processing page: {e}")

# Main Execution
easylist_path = 'easylist.txt'
css_selectors = parse_easylist(easylist_path)

url = 'https://www.espncricinfo.com/'
save_directory = '/Users/kaleemullahqasim/Desktop/Prof Xiu Hai Tao/data/'
os.makedirs(save_directory, exist_ok=True)

fetch_and_save_ad_images(url, css_selectors, save_directory)
