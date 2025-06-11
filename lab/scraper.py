import requests
import json
# import time # Not used currently
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService # For managing chromedriver
from webdriver_manager.chrome import ChromeDriverManager # For automatically downloading/managing chromedriver
from selenium.common.exceptions import TimeoutException, WebDriverException # Import exceptions
import time

# New API endpoint for Martel's wine page
API_URL = "https://www.martel.ch/wein/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.4 Safari/605.1.15",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Connection": "keep-alive",
}

# Define character sets and target text for XPath translation
upper_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ"
lower_chars = "abcdefghijklmnopqrstuvwxyzäöü"
target_text_mehr = "mehr anzeigen"

# Helper functions (will likely need significant changes or replacement)
# def parse_wine_type_from_categories(categories):
#     # ... (keep for now, may need adjustment or removal)
#     return None

# def parse_country_from_data(categories, breadcrumbs):
#     # ... (keep for now, may need adjustment or removal)
#     return None

def scrape_martel_wines():
    """
    Main function to scrape wines from martel.ch using Selenium to handle dynamic content,
    including clicking "Mehr anzeigen" to load all wines.
    """
    all_wines = []
    processed_product_urls = set() # To keep track of URLs already scraped
    print(f"🚀 Starting the scraper for {API_URL} with Selenium, aiming for all wines...")

    # Setup Chrome options for Selenium
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(f"user-agent={HEADERS['User-Agent']}")
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})

    driver = None
    try:
        try:
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        except Exception as e:
            print(f"Error initializing WebDriver with ChromeDriverManager: {e}")
            print("Please ensure you have Google Chrome installed.")
            print("If issues persist, you might need to manually download chromedriver and ensure it's in your PATH.")
            return []

        driver.get(API_URL)
        print(f"Opened {API_URL}")

        # --- Initial Cookie Handling on Main Page ---
        try:
            print("Attempting to find and click cookie consent button on main page...")
            cookie_button_xpath_main = (
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'alle akzeptieren') or "
                "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all') or "
                "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'einverstanden') or "
                "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'akzeptieren') or "
                "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]"
            )
            cookie_consent_button_main = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, cookie_button_xpath_main))
            )
            cookie_consent_button_main.click()
            print("✅ Clicked cookie consent button on main page.")
            time.sleep(2) # Wait for banner to disappear
        except TimeoutException:
            print("ℹ️ Cookie consent button not found on main page or already accepted.")
        except Exception as e_cookie_main:
            print(f"⚠️ Error handling cookie consent on main page: {e_cookie_main}")
        # --- End Initial Cookie Handling ---

        page_iteration = 1
        max_wines_approx = 2500 # Safety break, site mentions ~2380 wines

        while len(all_wines) < max_wines_approx:
            print(f"\\n🔄 --- Load Iteration {page_iteration} ---")
            
            # Wait for product elements to be present/stable after initial load or click
            try:
                print(f"Waiting up to 30s for product cards to be present on load {page_iteration}...")
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'product-swiper-card'))
                )
                print("✅ Product cards seem to be present. Giving 3s for JS rendering...")
                time.sleep(3) # Give a bit more time for JS to render everything
            except TimeoutException:
                print(f"⏳ Timed out waiting for product cards on load {page_iteration}. Assuming no more products or error.")
                break

            current_page_source = driver.page_source
            soup = BeautifulSoup(current_page_source, 'html.parser')
            
            product_elements_on_view = soup.find_all('div', class_='card product-box product-swiper-card')
            if not product_elements_on_view:
                # Fallback selector
                product_elements_on_view = soup.find_all('div', class_='product-swiper-card')

            print(f"🔍 Found {len(product_elements_on_view)} product elements in current view. Total unique wines processed so far: {len(all_wines)}")

            new_wines_scraped_this_iteration = 0
            
            # --- START: MODIFICATION FOR TESTING (replaces the for loop below) ---
            # This block is for testing the "Mehr anzeigen" button functionality by skipping detailed scraping.
            # Set to False and uncomment the original loop below to revert to full scraping.
            test_scroll_only_mode = False
            if test_scroll_only_mode:
                if product_elements_on_view:
                    print(f"  [TESTING MODE] Found {len(product_elements_on_view)} product elements. Skipping detail scraping and actual data processing.")
                    # For testing, consider all visible elements as "new" for this iteration's count.
                    new_wines_scraped_this_iteration = len(product_elements_on_view)
                    
                    # Add placeholders to all_wines to simulate progress for the main loop's counter (max_wines_approx)
                    # and for logging purposes. processed_product_urls is not used in this mode.
                    for _ in range(len(product_elements_on_view)):
                        if len(all_wines) < max_wines_approx: # Respect the overall limit
                            all_wines.append("dummy_wine_placeholder_for_testing")
                    print(f"  [TESTING MODE] all_wines list now contains {len(all_wines)} placeholder entries.")
                else:
                    # If no elements are found in the current view.
                    new_wines_scraped_this_iteration = 0
                # The original 'for' loop that processes each wine individually is skipped in this mode.
            else:
                # --- Original scraping loop (uncomment this block and set test_scroll_only_mode = False to use) ---
                for i_card, element in enumerate(product_elements_on_view):
                    name_from_card = "Unknown Wine"
                    product_link_val = None
                    
                    name_tag_card = element.find('h2', class_='product-name')
                    if name_tag_card:
                        link_tag_in_name = name_tag_card.find('a')
                        if link_tag_in_name:
                            name_from_card = link_tag_in_name.text.strip()
                            href = link_tag_in_name.get('href')
                            if href:
                                product_link_val = urljoin(API_URL, href)
                
                    if not product_link_val:
                        # print(f"Card {i_card+1}: Could not extract product link. Skipping.")
                        continue
                
                    if product_link_val in processed_product_urls:
                        # print(f"Card {i_card+1}: Wine {name_from_card} ({product_link_val}) already processed. Skipping.")
                        continue
                    
                    # New wine found
                    new_wines_scraped_this_iteration += 1 # Increment for actual new wines
                    current_wine_count = len(all_wines) + 1
                    print(f"  -> Processing NEW wine #{current_wine_count}: {name_from_card} ({product_link_val})")
                
                    wine_data_entry = {
                        "name": name_from_card, "type": None, "varietal": None, "vintage": None,
                        "region": None, "sub_region": None, "country": None, "price": None, 
                        "description": None, "image_url": None, "product_url": product_link_val, 
                        "size": None, "brandName": None, "food_pairing": None, 
                        "drinking_window": None, "body_type": None, "source": "martel.ch"
                    }
                
                    # --- Stage 1: Extract data from the product card (element) ---
                    price_tag = element.find('div', class_='product-price')
                    if price_tag and price_tag.find('div'):
                        price_text = price_tag.find('div').text.strip()
                        try:
                            wine_data_entry["price"] = float(price_text.replace('CHF', '').replace('\\\'', '').strip())
                        except ValueError:
                            print(f"    ⚠️ Could not parse price from listing for {name_from_card}: {price_text}")
                
                    image_link_tag = element.find('a', class_='product-image-link')
                    if image_link_tag:
                        img_tag = image_link_tag.find('img', class_='product-image')
                        if img_tag and img_tag.get('src'):
                            wine_data_entry["image_url"] = urljoin(API_URL, img_tag.get('src'))
                        elif img_tag and img_tag.get('srcset'):
                            srcset = img_tag.get('srcset')
                            wine_data_entry["image_url"] = urljoin(API_URL, srcset.split(',')[0].strip().split(' ')[0])
                    
                    temp_producer_card = None
                    temp_size_card = None
                    raw_description_from_card_p_tags = []
                    if name_tag_card: 
                        for p_tag in name_tag_card.find_next_siblings('p'):
                            p_text = p_tag.text.strip()
                            if not p_text: continue
                            raw_description_from_card_p_tags.append(p_text)
                            if "|" in p_text:
                                parts = [part.strip() for part in p_text.split("|")]
                                if len(parts) == 3:
                                    potential_size = parts[2]
                                    if "cl" in potential_size.lower() or potential_size.lower().endswith("l"):
                                        if not temp_size_card: temp_size_card = potential_size
                                        if not temp_producer_card: temp_producer_card = parts[1]
                                elif len(parts) == 2:
                                    part0_is_size = "cl" in parts[0].lower() or parts[0].lower().endswith("l")
                                    part1_is_size = "cl" in parts[1].lower() or parts[1].lower().endswith("l")
                                    if part1_is_size and not temp_size_card:
                                        temp_size_card = parts[1]
                                        if not temp_producer_card: temp_producer_card = parts[0]
                                    elif part0_is_size and not temp_size_card:
                                        temp_size_card = parts[0]
                                        if not temp_producer_card: temp_producer_card = parts[1]
                                    elif not temp_producer_card: 
                                        temp_producer_card = parts[0] 
                            else: 
                                if ("cl" in p_text.lower() or p_text.lower().endswith("l")) and not temp_size_card:
                                    temp_size_card = p_text
                                elif not temp_producer_card and p_text and not any(kw in p_text.lower() for kw in ["wein", "wine", "ac", "cru", "cl", "liter", "qualität", "jahrgang"]):
                                    temp_producer_card = p_text
                            
                    wine_data_entry["description"] = " | ".join(raw_description_from_card_p_tags) # Initial desc from card
                    if temp_size_card: wine_data_entry["size"] = temp_size_card
                    if temp_producer_card: wine_data_entry["brandName"] = temp_producer_card
                    
                    # --- Stage 2: Visit product detail page for more info ---
                    if product_link_val:
                        print(f"    🔄 Fetching details for: {name_from_card}")
                        current_detail_page_url = "" # Initialize to be safe
                        try:
                            driver.get(product_link_val)
                            current_detail_page_url = driver.current_url # Capture URL after get
                            time.sleep(0.5) # Brief pause for page to start loading
                
                            # --- BEGIN COOKIE HANDLING ON DETAIL PAGE ---
                            try:
                                # print("    Attempting to find and click cookie consent button on detail page...")
                                cookie_button_xpath_detail = (
                                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'alle akzeptieren') or "
                                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all') or "
                                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'einverstanden') or "
                                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'akzeptieren') or "
                                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]"
                                )
                                cookie_consent_button_detail = WebDriverWait(driver, 7).until( # Shorter timeout for detail cookie
                                    EC.element_to_be_clickable((By.XPATH, cookie_button_xpath_detail))
                                )
                                cookie_consent_button_detail.click()
                                print("    ✅ Clicked cookie consent button on detail page.")
                                time.sleep(1) # Wait for banner to disappear
                            except TimeoutException:
                                print("    ℹ️ Cookie consent button not found on detail page (or already accepted/not present).")
                            except Exception as e_cookie_detail:
                                print(f"    ⚠️ Error handling cookie consent on detail page: {e_cookie_detail}")
                            # --- END COOKIE HANDLING ON DETAIL PAGE ---
                
                            # Attempt to parse vintage from name (fallback, detail page is better)
                            current_name_for_vintage = wine_data_entry["name"]
                            if current_name_for_vintage and not wine_data_entry["vintage"] and len(current_name_for_vintage) > 4 and current_name_for_vintage[-4:].isdigit():
                                try:
                                    year = int(current_name_for_vintage[-4:])
                                    if 1800 < year < 2050:
                                        wine_data_entry["vintage"] = str(year)
                                except ValueError:
                                    pass
                            
                            detail_wait_timeout = 25
                            # print(f"    Waiting up to {detail_wait_timeout}s for detail page stats table...")
                            WebDriverWait(driver, detail_wait_timeout).until(
                                EC.visibility_of_element_located((By.ID, 'product-detail-stats-table'))
                            )
                            # print("    ✅ Detail page stats table is visible.")
                            
                            detail_page_source = driver.page_source
                            detail_soup = BeautifulSoup(detail_page_source, 'html.parser')
                
                            # --- Detail Page Parsing Logic (copied from original script) ---
                            type_tag = detail_soup.select_one('h2.product-detail-headline__subtitle')
                            if type_tag:
                                wine_data_entry["type"] = type_tag.text.strip()
                
                            attributes_div = detail_soup.select_one('div.product-detail-attributes')
                            if attributes_div:
                                producer_tag_detail = attributes_div.find('h2')
                                if producer_tag_detail:
                                    wine_data_entry["brandName"] = producer_tag_detail.text.strip() # Update brandName from detail
                                
                                size_tag_detail = producer_tag_detail.find_next_sibling('p') if producer_tag_detail else attributes_div.find('p', string=lambda t: t and ("cl" in t.lower() or t.lower().endswith("l")))
                                if size_tag_detail:
                                     wine_data_entry["size"] = size_tag_detail.text.strip() # Update size from detail
                
                            description_container_main = detail_soup.select_one('div.col-md-6.order-md-1 div.product-detail-description')
                            if description_container_main:
                                desc_clone = BeautifulSoup(str(description_container_main), 'html.parser')
                                h2_in_desc = desc_clone.find('h2')
                                if h2_in_desc: h2_in_desc.decompose()
                                description_text = desc_clone.get_text(separator=' ', strip=True)
                                if description_text:
                                    wine_data_entry["description"] = description_text # Update description from detail
                            # else:
                                # print("    ℹ️ Main description container not found on detail page.")
                
                            icon_to_field_map = {
                                "icon-kellerkarte-rebsorten": "varietal", "icon-kellerkarte-jahrgang": "vintage",
                                "icon-kellerkarte-region": "region", "icon-kellerkarte-subregion": "sub_region",
                                "icon-kellerkarte-passt-zu": "food_pairing", "icon-kellerkarte-trinkreife": "drinking_window",
                                "icon-kellerkarte-koerper": "body_type"
                            }
                            stats_table = detail_soup.find('table', id='product-detail-stats-table')
                            if stats_table:
                                for row in stats_table.find_all('tr'):
                                    th = row.find('th')
                                    td = row.find('td')
                                    if th and td:
                                        icon_span = th.find('span', class_=lambda x: x and "icon-kellerkarte-" in x)
                                        if icon_span:
                                            icon_classes = icon_span.get('class', [])
                                            for a_tag_td in td.find_all('a'): a_tag_td.decompose()
                                            value = td.get_text(separator=' ', strip=True).replace('&nbsp;', ' ').strip()
                                            if not value: continue
                                            for icon_class_key, field_name in icon_to_field_map.items():
                                                if any(icon_class_key in cls for cls in icon_classes):
                                                    wine_data_entry[field_name] = value
                                                    break
                            # else:
                                # print("    ℹ️ Stats table not found on detail page.")
                
                            if not wine_data_entry.get("country"):
                                meta_category_tag = detail_soup.find('meta', itemprop='category')
                                if meta_category_tag and meta_category_tag.get('content'):
                                    content_parts = [part.strip() for part in meta_category_tag.get('content').split(',')]
                                    known_countries_list = ["Frankreich", "Italien", "Spanien", "Schweiz", "Deutschland", "Österreich", "Portugal", "USA", "Argentinien", "Chile", "Australien", "Neuseeland", "Südafrika"]
                                    parsed_type_lower = wine_data_entry.get("type", "").lower() if wine_data_entry.get("type") else ""
                                    parsed_region_lower = wine_data_entry.get("region", "").lower() if wine_data_entry.get("region") else ""
                                    for part in content_parts:
                                        if part in known_countries_list:
                                            if not (parsed_type_lower and part.lower() == parsed_type_lower) and \
                                               not (parsed_region_lower and part.lower() == parsed_region_lower):
                                                wine_data_entry["country"] = part
                                                break
                                    if not wine_data_entry.get("country") and len(content_parts) == 3:
                                        type_match = parsed_type_lower and content_parts[0].lower().startswith(parsed_type_lower)
                                        region_match = parsed_region_lower and content_parts[2].lower().startswith(parsed_region_lower)
                                        if type_match and region_match and content_parts[1] in known_countries_list:
                                            wine_data_entry["country"] = content_parts[1]
                                # else:
                                    # print("    ℹ️ Meta category tag for country parsing not found.")
                            
                            # print(f"    --- Debug Info for Detail Page: {wine_data_entry['name']} ---")
                            # for key, val in wine_data_entry.items():
                            #     if val and key not in ["source", "product_url", "image_url", "price"]:
                            #          print(f"      {key}: {val}")
                            # print("    --- End Debug Info ---")
                            print(f"    ✅ Successfully fetched and parsed details for: {wine_data_entry['name']}")
                            time.sleep(0.5) # Small pause
                
                        except TimeoutException as te_detail:
                            print(f"    ⏳ Timeout waiting for detail page elements for {name_from_card}. Error: {te_detail.msg}")
                            try:
                                safe_name_detail = "".join(c if c.isalnum() else "_" for c in name_from_card)
                                driver.save_screenshot(f"martel_detail_timeout_{safe_name_detail[:50]}.png")
                                with open(f"martel_detail_timeout_source_{safe_name_detail[:50]}.html", "w", encoding="utf-8") as f_err_detail:
                                    f_err_detail.write(driver.page_source)
                                print(f"    📸 Saved screenshot and source for detail page timeout.")
                            except Exception as save_err_detail:
                                print(f"    Could not save screenshot/source on detail page timeout: {save_err_detail}")
                        except WebDriverException as wde_detail:
                            print(f"    ⚠️ WebDriverException on detail page for {name_from_card}. Message: {wde_detail.msg}")
                            try:
                                safe_name = "".join(c if c.isalnum() else "_" for c in name_from_card)
                                source_path = f"martel_detail_webdriver_error_source_{safe_name[:50]}.html"
                                error_page_source = driver.page_source
                                with open(source_path, "w", encoding="utf-8") as f_err:
                                    f_err.write(error_page_source)
                                print(f"💾 Saved page source on WebDriverException to {source_path}")
                            except Exception as save_page_err:
                                print(f"Could not save page source on WebDriverException: {save_page_err}")
                        
                        except Exception as detail_err:
                            print(f"⚠️ Generic error fetching or parsing detail page for {name_from_card}: {detail_err}")
                            try:
                                safe_name = "".join(c if c.isalnum() else "_" for c in name_from_card)
                                source_path = f"martel_detail_generic_error_source_{safe_name[:50]}.html"
                                error_page_source = driver.page_source
                                with open(source_path, "w", encoding="utf-8") as f_err:
                                    f_err.write(error_page_source)
                                print(f"💾 Saved page source on generic error to {source_path}")
                            except Exception as save_page_err:
                                print(f"Could not save page source on generic error: {save_page_err}")
                        finally:
                            # IMPORTANT: Navigate back to the listing page
                            print(f"    ↩️ Navigating back from detail page of {name_from_card} (URL was: {current_detail_page_url})...")
                            if not current_detail_page_url: # Should have been set by driver.get()
                                print("    ⚠️ current_detail_page_url was not set before driver.back(). This is unexpected.")
                            
                            driver.back()
                            
                            try:
                                # 1. Wait for URL to change from the detail page URL (if it was successfully captured)
                                if current_detail_page_url and driver.current_url == current_detail_page_url: # Only wait if URL hasn't changed yet
                                    print(f"    Waiting up to 10s for URL to change from {current_detail_page_url}...")
                                    WebDriverWait(driver, 10).until(
                                        EC.not_(EC.url_to_be(current_detail_page_url))
                                    )
                                    print(f"    ✅ URL changed. Current URL: {driver.current_url}")
                                elif not current_detail_page_url:
                                    print(f"    ℹ️ Skipping URL change check as detail page URL wasn't captured. Current URL: {driver.current_url}")
                                else: # URL already changed
                                    print(f"    ✅ URL already different from detail page. Current URL: {driver.current_url}")
                
                                # 2. Now wait for a clear indicator of the listing page
                                print(f"    Waiting up to 20s for listing page elements (e.g., product card) to reappear. Current URL: {driver.current_url}")
                                WebDriverWait(driver, 20).until( 
                                    EC.presence_of_element_located((By.CLASS_NAME, 'product-swiper-card'))
                                )
                                print(f"    ✅ Successfully navigated back. Listing page elements detected. Current URL: {driver.current_url}")
                                time.sleep(1.5) # Pause for JS rendering on listing page
                            
                            except TimeoutException:
                                print(f"    ❌ CRITICAL: Failed to confirm navigation back to listing page from detail page {current_detail_page_url}.")
                                print(f"    Current URL after attempting back navigation: {driver.current_url}")
                                print(f"    This could be due to URL not changing or listing page elements not appearing.")
                                print(f"    The script will likely fail to find 'Mehr anzeigen' button next.")
                                try:
                                    safe_name_back_fail = "".join(c if c.isalnum() else "_" for c in name_from_card) if name_from_card else "UnknownWine"
                                    error_filename_base = f"martel_back_nav_FAIL_{safe_name_back_fail[:50]}"
                                    driver.save_screenshot(f"{error_filename_base}.png")
                                    with open(f"{error_filename_base}.html", "w", encoding="utf-8") as f_err_back:
                                        f_err_back.write(driver.page_source)
                                    print(f"    📸 Saved screenshot and source for back navigation failure: {error_filename_base}.png / {error_filename_base}.html")
                                except Exception as save_err_back:
                                    print(f"    Could not save screenshot/source on back navigation failure: {save_err_back}")
                                # The script will proceed, but likely fail at "Mehr anzeigen", which should break the main loop.
                
                        all_wines.append(wine_data_entry)
                        processed_product_urls.add(product_link_val)
                        
                        # Incremental Save (was inside the original for loop)
                        if len(all_wines) % 20 == 0: 
                            print(f"\\n💾 Saving progress: {len(all_wines)} wines processed.")
                            try:
                                with open("martel_wines.json", "w", encoding="utf-8") as f_out:
                                    json.dump(all_wines, f_out, indent=2, ensure_ascii=False)
                                print(f"💾 Progress saved to martel_wines.json ({len(all_wines)} wines)")
                            except Exception as e_save:
                                print(f"⚠️ Error saving progress: {e_save}")
                # End of the for loop: for i_card, element in enumerate(product_elements_on_view):
            # The 'else' block for 'test_scroll_only_mode = False' (which handles the main scraping) now correctly
            # concludes after processing all items in product_elements_on_view.
            # The logic for break conditions and clicking "Mehr anzeigen" is handled further down,
            # outside this if/else structure, applying to both test_scroll_only_mode True and False.

            # --- END: MODIFICATION FOR TESTING ---
            
            if new_wines_scraped_this_iteration == 0 and page_iteration > 1:
                print("ℹ️ No new unique wines found in this iteration after a 'Mehr anzeigen' click. Assuming end of list.")
                break
            if not product_elements_on_view and page_iteration == 1 : # No products on first load
                 print("⚠️ No product elements found on initial page load. Exiting.")
                 break
                
                
            # --- Try to click "Mehr anzeigen" ---
            try:
                print("Looking for 'Mehr anzeigen' button...")
                # More robust XPath, looking for button or link, case-insensitive text, and not disabled
                load_more_button_xpath = (
                    f"//button[not(@disabled) and contains(translate(normalize-space(.), '{upper_chars}', '{lower_chars}'), '{target_text_mehr}')] | "
                    f"//a[not(contains(@style, 'display:none')) and contains(translate(normalize-space(.), '{upper_chars}', '{lower_chars}'), '{target_text_mehr}')]"
                )
                
                load_more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, load_more_button_xpath))
                )
                
                print("✅ Found 'Mehr anzeigen' button. Scrolling and clicking...")
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center', inline: 'center'});", load_more_button)
                time.sleep(0.5) # Wait for scroll
                # driver.execute_script("arguments[0].click();", load_more_button) # JS click as an alternative
                load_more_button.click() # Standard click
                
                print("🖱️ Clicked 'Mehr anzeigen'. Waiting 5s for new content to load...")
                page_iteration += 1
                time.sleep(5) # Wait for new products to load. WebDriverWait at loop start will also help.
                
            except TimeoutException:
                print("ℹ️ 'Mehr anzeigen' button not found, not clickable, or timed out. Assuming all wines are loaded.")
                break # Exit the while loop
            except Exception as e_click:
                print(f"⚠️ Error clicking 'Mehr anzeigen' button: {e_click}")
                try:
                    driver.save_screenshot(f"martel_click_error_iter_{page_iteration}.png")
                    print(f"📸 Screenshot saved: martel_click_error_iter_{page_iteration}.png")
                except Exception as e_ss:
                    print(f"Could not save screenshot on click error: {e_ss}")
                break
        
        print(f"\\n🎉 Scraping loop finished. Total unique wines scraped: {len(all_wines)}")

    except requests.exceptions.HTTPError as http_err: # Should not occur with Selenium for page load
        print(f"HTTP error occurred: {http_err}")
    except WebDriverException as wde_main:
        print(f"A WebDriverException occurred in the main scraping process: {wde_main.msg}")
        try:
            driver.save_screenshot("martel_main_webdriver_error.png")
            with open("martel_main_webdriver_error_source.html", "w", encoding="utf-8") as f_wde_err:
                f_wde_err.write(driver.page_source)
            print("📸 Saved screenshot and source for main WebDriverException.")
        except: pass
    except Exception as err:
        print(f"An overall error occurred: {err}")
        try:
            driver.save_screenshot("martel_main_generic_error.png")
            print("📸 Saved screenshot for main generic error.")
        except: pass
    finally:
        if driver:
            print("Closing Selenium WebDriver...")
            driver.quit()
            
        if all_wines:
            print(f"\\n💾 Final save: {len(all_wines)} wines to martel_wines.json.")
            try:
                with open("martel_wines.json", "w", encoding="utf-8") as f_out_final:
                    json.dump(all_wines, f_out_final, indent=2, ensure_ascii=False)
                print(f"💾 All {len(all_wines)} wine data saved to 'lab/martel_wines.json'")
            except Exception as e_final_save:
                print(f"⚠️ Error during final save: {e_final_save}")
        elif not processed_product_urls: # Check if any processing happened at all
             print("ℹ️ No wines were processed or added to the list.")


    return all_wines

# --- Main execution block ---
if __name__ == "__main__":
    wines_data = scrape_martel_wines() # scrape_martel_wines now handles saving
    
    if wines_data:
        print(f"\\\\n--- Final Wine Data (First Wine, from memory) after scraping {len(wines_data)} wines ---")
        if wines_data: # Ensure list is not empty before accessing index 0
            print(json.dumps(wines_data[0], indent=2, ensure_ascii=False))
        # The file martel_wines.json should already be up-to-date by the incremental save.
        print(f"💾 All {len(wines_data)} wine data should be saved in 'lab/martel_wines.json'")
    else:
        print("ℹ️ No wines were scraped or an error occurred (or scraper is in inspection mode).")