import asyncio
from pyppeteer import launch

async def main():
    browser = await launch(headless=True)
    page = await browser.newPage()
    # Wait for the network to be idle after navigating to the page
    await page.goto('https://tweaklibrary.com/image-downloader-extensions-for-chrome/#google_vignette', waitUntil='networkidle0')
    # Set the viewport to a standard size to ensure visibility calculations are consistent
    await page.setViewport({'width': 1920, 'height': 1080})
    # Scroll the page to trigger any lazy-loaded elements
    await page.evaluate('() => window.scrollBy(0, window.innerHeight)')

    ad_attributes = [
    'data-ad-format',  # Google AdSense
    'data-ad-layout-key',  # Google AdSense
    'data-ad-client',  # Google AdSense
    'data-ad-slot',  # Google AdSense
    'data-google-query-id',  # Google AdSense
    'data-amazon-targeting',  # Amazon Associates
    'data-aax_size',  # Amazon Associates
    'data-aax_src',  # Amazon Associates
    'data-aax_options',  # Amazon Associates
    'data-aax_pub_id',  # Amazon Associates
    'data-ia-disable-ad',  # Infolinks
    'data-tag-type',  # Infolinks
    'data-ad',  # AOL Advertising
    'data-ad-client',  # AOL Advertising
    'data-ad-slot',  # AOL Advertising
    'data-ad-type',  # AOL Advertising
    'data-ad-layout',  # AOL Advertising
    'data-ad-name',  # AOL Advertising
    'data-bidvertiser',  # BidVertiser
    'data-chitika-contextual-ad',  # Chitika
    'data-revive-zoneid',  # Revive Adserver
    'data-zid',  # Revive Adserver
    'data-zone-id',  # Revive Adserver
    'data-oeu',  # OpenX
    'data-oid',  # OpenX
    'data-zone',  # OpenX
    'data-ad-format', 'data-ad-layout-key', 'data-ad-client', 'data-ad-slot', 'data-google-query-id'
]

    processed_elements = set()
    ads_data = []
    for attr in ad_attributes:
        selector = f'[{attr}]'
        elements = await page.querySelectorAll(selector)
        for element in elements:
            # Check visibility with computed styles to ensure the element is actually displayable
            is_visible = await page.evaluate('''(element) => {
                const style = window.getComputedStyle(element);
                return style && style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0' &&
                       parseFloat(style.height) > 0 && parseFloat(style.width) > 0;
            }''', element)
            if not is_visible:
                continue

            outer_html = await page.evaluate('(element) => element.outerHTML', element)
            if outer_html in processed_elements:
                continue
            processed_elements.add(outer_html)

            # Retrieve text, href, and image source from the ad element
            text = await page.evaluate('(element) => element.innerText', element)
            href = await page.evaluate('(element) => element.getAttribute("href")', element)
            img_src = await page.evaluate('''(element) => {
                    const img = element.querySelector("img");
                    return img ? img.src : "";
                }''', element)


            ads_data.append({
                "attribute": attr,
                "text": text,
                "href": href,
                "img_src": img_src
            })

    # Print the detected ad information
    if ads_data:
        for ad in ads_data:
            print(f"Ad detected: {ad}")
    else:
        print("No ads detected.")

    # Close the browser after completion
    await browser.close()

asyncio.run(main())
