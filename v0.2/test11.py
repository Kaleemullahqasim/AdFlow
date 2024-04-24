# import asyncio
# from pyppeteer import launch

# async def main():
#     browser = await launch(headless=True)
#     page = await browser.newPage()
#     # Ensure the page is fully loaded
#     await page.goto('https://tweaklibrary.com/image-downloader-extensions-for-chrome/#google_vignette', waitUntil='networkidle0')
#     # Set the viewport to simulate a typical desktop browsing environment
#     await page.setViewport({'width': 1920, 'height': 1080})
    
#     # Scroll the page to trigger lazy loading elements, if any
#     await page.evaluate('() => window.scrollBy(0, window.innerHeight)')

#     ad_attributes = [
#     'data-ad-format',  # Google AdSense
#     'data-ad-layout-key',  # Google AdSense
#     'data-ad-client',  # Google AdSense
#     'data-ad-slot',  # Google AdSense
#     'data-google-query-id',  # Google AdSense
#     'data-amazon-targeting',  # Amazon Associates
#     'data-aax_size',  # Amazon Associates
#     'data-aax_src',  # Amazon Associates
#     'data-aax_options',  # Amazon Associates
#     'data-aax_pub_id',  # Amazon Associates
#     'data-ia-disable-ad',  # Infolinks
#     'data-tag-type',  # Infolinks
#     'data-ad',  # AOL Advertising
#     'data-ad-client',  # AOL Advertising
#     'data-ad-slot',  # AOL Advertising
#     'data-ad-type',  # AOL Advertising
#     'data-ad-layout',  # AOL Advertising
#     'data-ad-name',  # AOL Advertising
#     'data-bidvertiser',  # BidVertiser
#     'data-chitika-contextual-ad',  # Chitika
#     'data-revive-zoneid',  # Revive Adserver
#     'data-zid',  # Revive Adserver
#     'data-zone-id',  # Revive Adserver
#     'data-oeu',  # OpenX
#     'data-oid',  # OpenX
#     'data-zone',  # OpenX
#     'data-ad-format', 'data-ad-layout-key', 'data-ad-client', 'data-ad-slot', 'data-google-query-id'
# ]

#     processed_elements = set()
#     ads_data = []
#     for attr in ad_attributes:
#         selector = f'[{attr}]'
#         elements = await page.querySelectorAll(selector)
#         for element in elements:
#             # Check if the element is actually displayed using computed styles
#             is_visible = await page.evaluate('''(element) => {
#                 const style = window.getComputedStyle(element);
#                 return style.display !== 'none' && style.visibility !== 'hidden' && parseFloat(style.opacity) > 0 &&
#                        parseFloat(style.height) > 0 && parseFloat(style.width) > 0;
#             }''', element)
#             if not is_visible:
#                 continue

#             # Check if the element has been processed already to avoid duplicates
#             outer_html = await page.evaluate('(element) => element.outerHTML', element)
#             if outer_html in processed_elements:
#                 continue
#             processed_elements.add(outer_html)

#             # Extract useful information from the element
#             text = await page.evaluate('(element) => element.innerText', element)
#             href = await page.evaluate('(element) => element.getAttribute("href")', element)
#             img_src = await page.evaluate('''(element) => {
#                 const img = element.querySelector("img");
#                 return img ? img.src : "";
#             }''', element)

#             ads_data.append({
#                 "attribute": attr,
#                 "text": text,
#                 "href": href,
#                 "img_src": img_src
#             })

#     if ads_data:
#         for ad in ads_data:
#             print(f"Ad detected: {ad}")
#     else:
#         print("No ads detected.")

#     # Close the browser after completion
#     await browser.close()

# asyncio.run(main())


# import asyncio
# from pyppeteer import launch

# async def main():
#     browser = await launch(headless=True)
#     page = await browser.newPage()
#     await page.goto('https://tweaklibrary.com/image-downloader-extensions-for-chrome/#google_vignette', waitUntil='networkidle0')
#     await page.setViewport({'width': 1280, 'height': 800})

#     # Scroll through the page to ensure all lazy-loaded ads are triggered
#     last_height = await page.evaluate('document.body.scrollHeight')
#     while True:
#         # Scroll down to the bottom of the page
#         await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
#         # Wait for new content to load, if any
#         await asyncio.sleep(2)
#         # Calculate the new scroll height and compare with the last scroll height
#         new_height = await page.evaluate('document.body.scrollHeight')
#         if new_height == last_height:
#             break
#         last_height = new_height

#     ad_attributes = [
#     'data-ad-format',  # Google AdSense
#     'data-ad-layout-key',  # Google AdSense
#     'data-ad-client',  # Google AdSense
#     'data-ad-slot',  # Google AdSense
#     'data-google-query-id',  # Google AdSense
#     'data-amazon-targeting',  # Amazon Associates
#     'data-aax_size',  # Amazon Associates
#     'data-aax_src',  # Amazon Associates
#     'data-aax_options',  # Amazon Associates
#     'data-aax_pub_id',  # Amazon Associates
#     'data-ia-disable-ad',  # Infolinks
#     'data-tag-type',  # Infolinks
#     'data-ad',  # AOL Advertising
#     'data-ad-client',  # AOL Advertising
#     'data-ad-slot',  # AOL Advertising
#     'data-ad-type',  # AOL Advertising
#     'data-ad-layout',  # AOL Advertising
#     'data-ad-name',  # AOL Advertising
#     'data-bidvertiser',  # BidVertiser
#     'data-chitika-contextual-ad',  # Chitika
#     'data-revive-zoneid',  # Revive Adserver
#     'data-zid',  # Revive Adserver
#     'data-zone-id',  # Revive Adserver
#     'data-oeu',  # OpenX
#     'data-oid',  # OpenX
#     'data-zone',  # OpenX
#     'data-ad-format', 'data-ad-layout-key', 'data-ad-client', 'data-ad-slot', 'data-google-query-id'
# ]

#     processed_elements = set()
#     ads_data = []
#     for attr in ad_attributes:
#         selector = f'[{attr}]'
#         elements = await page.querySelectorAll(selector)
#         for element in elements:
#             # Verify element is visible
#             is_visible = await page.evaluate('''(element) => {
#                 const style = window.getComputedStyle(element);
#                 return style.display !== 'none' && style.visibility !== 'hidden' && parseFloat(style.opacity) > 0 &&
#                        parseFloat(style.height) > 0 && parseFloat(style.width) > 0;
#             }''', element)
#             if not is_visible:
#                 continue

#             outer_html = await page.evaluate('(element) => element.outerHTML', element)
#             if outer_html in processed_elements:
#                 continue
#             processed_elements.add(outer_html)

#             text = await page.evaluate('(element) => element.innerText', element)
#             href = await page.evaluate('(element) => element.getAttribute("href")', element)
            # img_src = await page.evaluate('''(element) => {
            #     const img = element.querySelector("img");
            #     return img ? img.src : "";
            # }''', element)

#             ads_data.append({
#                 "attribute": attr,
#                 "text": text,
#                 "href": href,
#                 "img_src": img_src
#             })

#     if ads_data:
#         for ad in ads_data:
#             print(f"Ad detected: {ad}")
#     else:
#         print("No ads detected.")

#     await browser.close()

# asyncio.run(main())


import asyncio
from pyppeteer import launch

async def intercept_request(request):
    if 'advertisement' in request.url or '/ads/' in request.url:
        print(f"Ad-related request: {request.url}")
    await request.continue_()

async def main():
    browser = await launch(headless=True)
    page = await browser.newPage()
    await page.setRequestInterception(True)
    page.on('request', intercept_request)

    await page.goto('https://tweaklibrary.com/image-downloader-extensions-for-chrome/#google_vignette', waitUntil='networkidle0')
    await page.setViewport({'width': 1280, 'height': 800})

    await page.evaluate('window.scrollBy(0, document.body.scrollHeight)')
    await asyncio.sleep(2)  # Wait for lazy-loaded elements

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
    ads_data = []

    for attr in ad_attributes:
        selector = f'[{attr}]'
        elements = await page.querySelectorAll(selector)
        for element in elements:
            is_visible = await page.evaluate('''(element) => {
                const style = window.getComputedStyle(element);
                return style.display !== 'none' && style.visibility !== 'hidden' && parseFloat(style.opacity) > 0;
            }''', element)
            if not is_visible:
                continue

            # Checking for iframes within ad elements
            iframe = await element.querySelector('iframe')
            if iframe:
                iframe_src = await page.evaluate('(iframe) => iframe.src', iframe)
                print(f"Iframe source detected: {iframe_src}")

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

    if ads_data:
        for ad in ads_data:
            print(f"Ad detected: {ad}")
    else:
        print("No ads detected.")

    await browser.close()

asyncio.run(main())
