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

# Helper functions (will likely need significant changes or replacement)
# def parse_wine_type_from_categories(categories):
#     # ... (keep for now, may need adjustment or removal)
#     return None

# def parse_country_from_data(categories, breadcrumbs):
#     # ... (keep for now, may need adjustment or removal)
#     return None

def scrape_martel_wines():
    """
    Main function to scrape wines from martel.ch using Selenium to handle dynamic content.
    """
    all_wines = []
    print(f"🚀 Starting the scraper for {API_URL} with Selenium...")

    # Setup Chrome options for Selenium
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")  # Run headless (no browser window)
    chrome_options.add_argument("--disable-gpu") # Optional, sometimes helps in headless mode
    chrome_options.add_argument("--window-size=1920,1080") # Optional, set a window size
    chrome_options.add_argument(f"user-agent={HEADERS['User-Agent']}") # Set user agent
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2}) # Disable image loading

    driver = None # Initialize driver to None for finally block
    try:
        # Initialize WebDriver - this will download chromedriver if not present or not up-to-date
        try:
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        except Exception as e:
            print(f"Error initializing WebDriver with ChromeDriverManager: {e}")
            print("Please ensure you have Google Chrome installed.")
            print("If issues persist, you might need to manually download chromedriver and ensure it's in your PATH.")
            return []

        driver.get(API_URL)

        # Wait for the product elements to be loaded
        # We'll wait for at least one element with class 'product-swiper-card'
        # Increased timeout to 30 seconds as dynamic content loading can be slow
        wait_timeout = 30 
        print(f"Waiting up to {wait_timeout} seconds for product elements to appear...")
        try:
            WebDriverWait(driver, wait_timeout).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'product-swiper-card'))
            )
            print("✅ Product elements seem to be loaded.")
        except Exception as e: # Changed from TimeoutException to generic Exception for broader catch
            print(f"⏳ Timed out waiting for product elements after {wait_timeout} seconds, or other error occurred: {e}")
            # Save a screenshot and page source for debugging if timeout occurs
            try:
                driver.save_screenshot("martel_timeout_screenshot.png")
                with open("martel_timeout_page_source.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print("📸 Screenshot and page source saved for debugging timeout: martel_timeout_screenshot.png, martel_timeout_page_source.html")
            except Exception as save_err:
                print(f"Could not save screenshot/page source: {save_err}")
            return [] # Exit if products don't load

        # Optional: Scroll down a bit to trigger any lazy loading if necessary
        # print("Scrolling down slightly...")
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 4);")
        # time.sleep(3) # Wait for any lazy-loaded content after scroll

        page_source = driver.page_source # Get source of the listing page
        soup = BeautifulSoup(page_source, 'html.parser')

        # Try a more specific selector first based on the provided HTML
        product_elements = soup.find_all('div', class_='card product-box product-swiper-card')
        print(f"🔍 Found {len(product_elements)} product elements with class 'card product-box product-swiper-card'.")

        if not product_elements:
            # As a fallback, try just 'product-swiper-card' as it might be more unique
            print("ℹ️ Trying fallback selector 'product-swiper-card'...")
            product_elements = soup.find_all('div', class_='product-swiper-card')
            print(f"🔍 Found {len(product_elements)} product elements with class 'product-swiper-card'.")

        if not product_elements:
            print("⚠️ No product elements found even after Selenium load. Saving HTML for inspection.")
            with open("martel_selenium_page.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            print("💾 Full HTML content (from Selenium) saved to martel_selenium_page.html for manual inspection.")
            return []

        for i, element in enumerate(product_elements): # Added enumerate for limiting during testing
            name = None
            price_val = None
            image_url_val = None
            product_link_val = None
            # Initialize all fields that we expect to populate
            wine_data_entry = {
                "name": None, "type": None, "varietal": None, "vintage": None,
                "region": None, "sub_region": None, # Added
                "country": None, "price": None, "description": None,
                "image_url": None, "product_url": None, "size": None,
                "brandName": None, 
                "food_pairing": None, # Added
                "drinking_window": None, # Added
                "body_type": None, # Added
                "source": "martel.ch"
            }

            # --- Stage 1: Extract data from the product card on the listing page ---
            name_tag = element.find('h2', class_='product-name')
            if name_tag:
                link_tag_in_name = name_tag.find('a')
                if link_tag_in_name:
                    name = link_tag_in_name.text.strip()
                    wine_data_entry["name"] = name
                    href = link_tag_in_name.get('href')
                    if href:
                        product_link_val = urljoin(API_URL, href)
                        wine_data_entry["product_url"] = product_link_val
            
            price_tag = element.find('div', class_='product-price')
            if price_tag and price_tag.find('div'):
                price_text = price_tag.find('div').text.strip()
                try:
                    price_val = float(price_text.replace('CHF', '').replace('\\\'', '').strip())
                    wine_data_entry["price"] = price_val
                except ValueError:
                    print(f"⚠️ Could not parse price from listing: {price_text}")

            image_link_tag = element.find('a', class_='product-image-link')
            if image_link_tag:
                img_tag = image_link_tag.find('img', class_='product-image')
                if img_tag and img_tag.get('src'):
                    image_url_val = urljoin(API_URL, img_tag.get('src'))
                    wine_data_entry["image_url"] = image_url_val
                elif img_tag and img_tag.get('srcset'):
                    srcset = img_tag.get('srcset')
                    image_url_val = urljoin(API_URL, srcset.split(',')[0].strip().split(' ')[0])
                    wine_data_entry["image_url"] = image_url_val
            
            # Revised card parsing for description, producer, size
            temp_producer_card = None
            temp_size_card = None
            raw_description_from_card_p_tags = []

            if name_tag: 
                for p_tag in name_tag.find_next_siblings('p'):
                    p_text = p_tag.text.strip()
                    if not p_text: 
                        continue
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
                        elif not temp_producer_card and p_text and not any(kw in p_text.lower() for kw in ["wein", "wine", "ac", "cru", "cl", "liter", "qualität", "jahrgang"]): # Added more keywords to avoid
                            temp_producer_card = p_text
            
            wine_data_entry["description"] = " | ".join(raw_description_from_card_p_tags)
            if temp_size_card: wine_data_entry["size"] = temp_size_card
            if temp_producer_card: wine_data_entry["brandName"] = temp_producer_card

            # --- Stage 2: Visit product detail page for more info ---
            if product_link_val:
                print(f"\\\\n🔄 Fetching details for: {name} from {product_link_val}")
                try:
                    driver.get(product_link_val)
                    time.sleep(1) # Give page a moment to start loading

                    # --- BEGIN COOKIE HANDLING ---
                    try:
                        print("Attempting to find and click cookie consent button...")
                        # Common texts: "Alle akzeptieren", "Accept all", "Einverstanden", "OK", "Akzeptieren"
                        # This XPath looks for a button that contains one of these texts, case-insensitive.
                        cookie_button_xpath = (
                            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'alle akzeptieren') or "
                            "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all') or "
                            "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'einverstanden') or "
                            "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'akzeptieren') or "
                            "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]"
                        )
                        
                        cookie_consent_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, cookie_button_xpath))
                        )
                        cookie_consent_button.click()
                        print("✅ Clicked cookie consent button.")
                        time.sleep(2) # Wait for banner to disappear
                    except TimeoutException:
                        print("ℹ️ Cookie consent button not found or not clickable within 10 seconds (or already accepted).")
                    except Exception as e_cookie:
                        print(f"⚠️ Error handling cookie consent: {e_cookie}")
                    # --- END COOKIE HANDLING ---

                    # --- Stage 1.5: Initialize wine_data_entry for the current product ---
                    # Moved initialization inside the loop to ensure fresh entry for each wine
                    wine_data_entry = {
                        "name": name, "type": None, "varietal": None, "vintage": None,
                        "region": None, "sub_region": None, "country": None, "price": price_val,
                        "description": " | ".join(raw_description_from_card_p_tags), # Initial desc from card
                        "image_url": image_url_val, "product_url": product_link_val,
                        "size": temp_size_card, "brandName": temp_producer_card, # From card
                        "food_pairing": None, "drinking_window": None, "body_type": None,
                        "source": "martel.ch"
                    }
                    # Attempt to parse vintage from name (fallback, detail page is better)
                    if name and not wine_data_entry["vintage"] and len(name) > 4 and name[-4:].isdigit():
                        try:
                            year = int(name[-4:])
                            if 1800 < year < 2050:
                                wine_data_entry["vintage"] = str(year)
                        except ValueError:
                            pass

                    detail_wait_timeout = 25
                    print(f"Waiting up to {detail_wait_timeout}s for detail page stats table to be visible...")
                    WebDriverWait(driver, detail_wait_timeout).until(
                        EC.visibility_of_element_located((By.ID, 'product-detail-stats-table'))
                    )
                    print("✅ Detail page stats table is visible.")
                    
                    detail_page_source = driver.page_source
                    detail_soup = BeautifulSoup(detail_page_source, 'html.parser')

                    # --- New Parsing Logic for Detail Page ---

                    # Extract Type from h2.product-detail-headline__subtitle
                    type_tag = detail_soup.select_one('h2.product-detail-headline__subtitle')
                    if type_tag:
                        wine_data_entry["type"] = type_tag.text.strip()

                    # Extract Producer (brandName) and Size from div.product-detail-attributes
                    attributes_div = detail_soup.select_one('div.product-detail-attributes')
                    if attributes_div:
                        producer_tag = attributes_div.find('h2')
                        if producer_tag:
                            wine_data_entry["brandName"] = producer_tag.text.strip()
                        
                        # Size is usually in a <p> tag following the <h2> for producer
                        size_tag = producer_tag.find_next_sibling('p') if producer_tag else attributes_div.find('p', string=lambda t: "cl" in t.lower() or t.lower().endswith("l"))
                        if size_tag:
                             wine_data_entry["size"] = size_tag.text.strip()


                    # Extract Description from div.col-md-6.order-md-1 div.product-detail-description
                    # Ensure to pick the correct description, usually in the left column (order-md-1)
                    description_container_main = detail_soup.select_one('div.col-md-6.order-md-1 div.product-detail-description')
                    if description_container_main:
                        # Clone to safely remove h2
                        desc_clone = BeautifulSoup(str(description_container_main), 'html.parser')
                        h2_in_desc = desc_clone.find('h2')
                        if h2_in_desc:
                            h2_in_desc.decompose()
                        description_text = desc_clone.get_text(separator=' ', strip=True)
                        if description_text: # Only update if new description is found
                            wine_data_entry["description"] = description_text
                    else:
                        print("ℹ️ Main description container (div.col-md-6.order-md-1 div.product-detail-description) not found.")


                    # Extract properties from table#product-detail-stats-table
                    icon_to_field_map = {
                        "icon-kellerkarte-rebsorten": "varietal",
                        "icon-kellerkarte-jahrgang": "vintage",
                        "icon-kellerkarte-region": "region",
                        "icon-kellerkarte-subregion": "sub_region",
                        # "icon-kellerkarte-land": "country", # No land icon in provided HTML example
                        "icon-kellerkarte-passt-zu": "food_pairing",
                        "icon-kellerkarte-trinkreife": "drinking_window",
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
                                    
                                    # Clean td text (remove links like "zur Jahrgangstabelle", strip spaces)
                                    for a_tag in td.find_all('a'): # Remove 'a' tags like "zur Jahrgangstabelle"
                                        a_tag.decompose()
                                    value = td.get_text(separator=' ', strip=True).replace('&nbsp;', ' ').strip()
                                    if not value: # Skip if value is empty after cleaning
                                        continue

                                    for icon_class_key, field_name in icon_to_field_map.items():
                                        if any(icon_class_key in cls for cls in icon_classes):
                                            wine_data_entry[field_name] = value
                                            break # Found mapping for this row
                    else:
                        print("ℹ️ Stats table (table#product-detail-stats-table) not found.")

                    # Attempt to parse Country from meta tag if not found in table
                    if not wine_data_entry.get("country"):
                        meta_category_tag = detail_soup.find('meta', itemprop='category')
                        if meta_category_tag and meta_category_tag.get('content'):
                            content_parts = [part.strip() for part in meta_category_tag.get('content').split(',')]
                            # Example: ["Rotwein", "Frankreich", "Bordeaux"]
                            known_countries_list = [
                                "Frankreich", "Italien", "Spanien", "Schweiz", "Deutschland", 
                                "Österreich", "Portugal", "USA", "Argentinien", "Chile", 
                                "Australien", "Neuseeland", "Südafrika"
                            ] # Case-sensitive
                            
                            parsed_type_lower = wine_data_entry.get("type", "").lower()
                            parsed_region_lower = wine_data_entry.get("region", "").lower()

                            for part in content_parts:
                                if part in known_countries_list:
                                    # Avoid assigning if part is clearly type or region (simple check)
                                    if not (parsed_type_lower and part.lower() == parsed_type_lower) and \
                                       not (parsed_region_lower and part.lower() == parsed_region_lower):
                                        wine_data_entry["country"] = part
                                        break
                            
                            # Fallback for "Type, Country, Region" structure if country still not found
                            if not wine_data_entry.get("country") and len(content_parts) == 3:
                                type_match = parsed_type_lower and content_parts[0].lower().startswith(parsed_type_lower)
                                region_match = parsed_region_lower and content_parts[2].lower().startswith(parsed_region_lower)
                                if type_match and region_match and content_parts[1] in known_countries_list:
                                    wine_data_entry["country"] = content_parts[1]
                        else:
                            print("ℹ️ Meta category tag for country parsing not found.")
                    
                    print(f"\\\\n--- Debug Info for Detail Page: {name} ---")
                    # print(f"ℹ️ Extracted properties (props): {props}") # Old props dict removed
                    for key, val in wine_data_entry.items():
                        if key not in ["source", "product_url", "image_url", "price"] and val: # Print newly parsed/updated fields
                             print(f"  {key}: {val}")
                    print("--- End Debug Info ---")
                    
                    print(f"✅ Successfully fetched and parsed details for: {name}")
                    time.sleep(1)

                except TimeoutException as te: # Changed to direct import
                    print(f"⏳ Timeout waiting for detail page elements for {name}. Error: {te.msg}")
                    try:
                        # Sanitize filename
                        safe_name = "".join(c if c.isalnum() else "_" for c in name)
                        screenshot_path = f"martel_detail_timeout_{safe_name[:50]}.png"
                        source_path = f"martel_detail_timeout_source_{safe_name[:50]}.html"
                        driver.save_screenshot(screenshot_path)
                        with open(source_path, "w", encoding="utf-8") as f_err:
                            f_err.write(driver.page_source)
                        print(f"📸 Saved screenshot to {screenshot_path} and source to {source_path} for detail page timeout.")
                    except Exception as save_err:
                        print(f"Could not save screenshot/source on detail page timeout: {save_err}")

                except WebDriverException as wde: # Changed to direct import
                    print(f"⚠️ WebDriverException on detail page for {name}. Message: {wde.msg}")
                    try:
                        safe_name = "".join(c if c.isalnum() else "_" for c in name)
                        source_path = f"martel_detail_webdriver_error_source_{safe_name[:50]}.html"
                        error_page_source = driver.page_source
                        with open(source_path, "w", encoding="utf-8") as f_err:
                            f_err.write(error_page_source)
                        print(f"💾 Saved page source on WebDriverException to {source_path}")
                    except Exception as save_page_err:
                        print(f"Could not save page source on WebDriverException: {save_page_err}")
                
                except Exception as detail_err:
                    print(f"⚠️ Generic error fetching or parsing detail page for {name}: {detail_err}")
                    try:
                        safe_name = "".join(c if c.isalnum() else "_" for c in name)
                        source_path = f"martel_detail_generic_error_source_{safe_name[:50]}.html"
                        error_page_source = driver.page_source
                        with open(source_path, "w", encoding="utf-8") as f_err:
                            f_err.write(error_page_source)
                        print(f"💾 Saved page source on generic error to {source_path}")
                    except Exception as save_page_err:
                        print(f"Could not save page source on generic error: {save_page_err}")

            all_wines.append(wine_data_entry)
            
            # --- Incremental Save ---
            if (i + 1) % 5 == 0 or (i + 1) == len(product_elements):
                print(f"\\\\n💾 Saving progress: {len(all_wines)} out of {len(product_elements)} wines processed.")
                try:
                    with open("martel_wines.json", "w", encoding="utf-8") as f_out:
                        json.dump(all_wines, f_out, ensure_ascii=False, indent=4)
                    print(f"💾 Progress saved to martel_wines.json ({len(all_wines)} wines)")
                except Exception as e_save:
                    print(f"⚠️ Error saving intermediate JSON: {e_save}")
            # --- End Incremental Save ---

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} (This shouldn't happen with Selenium for page load)")
    except Exception as err:
        print(f"An error occurred: {err}")
    finally:
        if driver:
            print("Closing Selenium WebDriver...")
            driver.quit()
            
    # if not all_wines: # If loop is not yet implemented
    #     print("ℹ️ HTML inspection step. No wines parsed yet.")
    #     return []

    print(f"\\n🎉 Scraping complete! Total wines found: {len(all_wines)}")
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