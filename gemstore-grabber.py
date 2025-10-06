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

# Get catalog URL from gemstore page.
def get_catalog_js_url():
    url = "https://gemstore-live.ncplatform.net/?buildid=999999999999999999999" # massive buildid to grab most recent gemstore page
    response = requests.get(url)
    response.raise_for_status()
    
    match = re.search(r'https://\S+catalog\S+\.js', response.text)
    if match:
        return match.group(0)
    else:
        raise ValueError("No catalog file found in the page") # unlikely to happen

# Get content of the catalog file.
def get_js_content(js_url):
    response = requests.get(js_url)
    response.raise_for_status()
    return response.text

# Save content as JSON file and compare with previous file if exists.
def save_as_json(content):
    content = content.replace('// automatically generated', '').replace('var gemstoreCatalog =', '') # remove non-JSON parts
    json_content = json.loads(content)
    
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    folder_path = 'catalog'
    os.makedirs(folder_path, exist_ok=True)
    filename = os.path.join(folder_path, f"{current_date}.json")
    
    with open(filename, 'w') as file:
        json.dump(json_content, file, indent=4)
    logger.info(f"Content saved as {filename}")
    
    previous_filename = get_previous_filename(filename)
    
    if previous_filename:
        compare_with_previous(json_content, previous_filename)
    else:
        logger.info("No previous file found")

# Get the previous JSON filename.
def get_previous_filename(current_filename):
    folder_path = os.path.dirname(current_filename)
    files = [f for f in os.listdir(folder_path) if f.endswith('.json') and f != os.path.basename(current_filename)]
    if files:
        files.sort(reverse=True)
        return os.path.join(folder_path, files[0])
    return None

# Get the date from an item for sorting purposes.
def get_item_date(item):
    category_lifespans = item.get('categoryLifespans', {})
    if category_lifespans:
        first_key = next(iter(category_lifespans))
        if category_lifespans[first_key]:
            lifespan_start_raw = category_lifespans[first_key][0].get('start', 'N/A')
            if lifespan_start_raw != 'N/A':
                date_part = lifespan_start_raw.split('T')[0]
                try:
                    return datetime.datetime.strptime(date_part, '%Y-%m-%d')
                except ValueError:
                    pass
    # Return a very old date for items without valid dates so they appear first
    return datetime.datetime(1900, 1, 1)

# Compare current content with previous content and log new additions.
def compare_with_previous(current_content, previous_filename):
    with open(previous_filename, 'r') as file:
        previous_content = json.load(file)
    
    new_additions = {k: v for k, v in current_content.items() if k not in previous_content}
    if new_additions:
        logger.info("New additions:")
        # Sort new additions by date before logging
        sorted_additions = sorted(new_additions.items(), key=lambda item: get_item_date(item[1]))
        for key, value in sorted_additions:
            log_new_addition(value)
    else:
        logger.info("No new additions found")

# Log details of a new addition.
def log_new_addition(item):
    name = item.get('name', 'N/A')

    image_hash = item.get('imageHash', 'N/A')
    image_url = f"https://services.staticwars.com/gw2/img/content/{image_hash}_splash.jpg"

    category_lifespans = item.get('categoryLifespans', {})
    lifespan_start_raw = 'N/A'
    if category_lifespans:
        first_key = next(iter(category_lifespans))
        if category_lifespans[first_key]:
            lifespan_start_raw = category_lifespans[first_key][0].get('start', 'N/A')
    lifespan_start = lifespan_start_raw.split('T')[0] if lifespan_start_raw != 'N/A' else 'N/A'

    logger.info(f"**{lifespan_start}**: [{name}]({image_url})") # Markdown format for Discord



if __name__ == "__main__":
    try:
        catalog_js_url = get_catalog_js_url()
        js_content = get_js_content(catalog_js_url)
        save_as_json(js_content)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
