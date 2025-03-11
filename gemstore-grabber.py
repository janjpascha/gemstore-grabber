import requests
import re
import datetime
import json
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()
file_handler = logging.FileHandler('log.txt')
logger.addHandler(file_handler)

def get_catalog_js_url():
    """Get catalog URL from gemstore page."""
    url = "https://gemstore-live.ncplatform.net/?buildid=999999999999999999999"
    response = requests.get(url)
    response.raise_for_status()
    
    match = re.search(r'https://\S+catalog\S+\.js', response.text)
    if match:
        return match.group(0)
    else:
        raise ValueError("No catalog .js file found in the page")

def get_js_content(js_url):
    """Get content of the catalog file."""
    response = requests.get(js_url)
    response.raise_for_status()
    return response.text

def save_as_json(content):
    """Save content as JSON file and compare with previous file if exists."""
    content = content.replace('// automatically generated', '').replace('var gemstoreCatalog =', '')
    json_content = json.loads(content)
    
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"{current_date}.json"
    with open(filename, 'w') as file:
        json.dump(json_content, file, indent=4)
    logger.info(f"Content saved as {filename}")
    
    previous_filename = get_previous_filename(filename)
    
    if previous_filename:
        compare_with_previous(json_content, previous_filename)
    else:
        logger.info("No previous file found.")

def get_previous_filename(current_filename):
    """Get the previous JSON filename."""
    files = [f for f in os.listdir('.') if f.endswith('.json') and f != current_filename]
    if files:
        files.sort(reverse=True)
        return files[0]
    return None

def compare_with_previous(current_content, previous_filename):
    """Compare current content with previous content and log new additions."""
    with open(previous_filename, 'r') as file:
        previous_content = json.load(file)
    
    new_additions = {k: v for k, v in current_content.items() if k not in previous_content}
    if new_additions:
        logger.info("New additions:")
        for key, value in new_additions.items():
            log_new_addition(value)
    else:
        logger.info("No new additions found.")

def log_new_addition(item):
    """Log details of a new addition."""
    name = item.get('name', 'N/A')
    image_hash = item.get('imageHash', 'N/A')
    category_lifespans = item.get('categoryLifespans', {})
    lifespan_start_raw = 'N/A'
    if category_lifespans:
        first_key = next(iter(category_lifespans))
        if category_lifespans[first_key]:
            lifespan_start_raw = category_lifespans[first_key][0].get('start', 'N/A')
    lifespan_start = lifespan_start_raw.split('T')[0] if lifespan_start_raw != 'N/A' else 'N/A'
    image_url = f"https://services.staticwars.com/gw2/img/content/{image_hash}_splash.jpg"
    logger.info(f"**{lifespan_start}**: [{name}]({image_url})") # Markdown format for Discord

if __name__ == "__main__":
    try:
        catalog_js_url = get_catalog_js_url()
        js_content = get_js_content(catalog_js_url)
        save_as_json(js_content)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
