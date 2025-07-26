import subprocess
import sys
import logging
from datetime import datetime
import os

# Import email modules
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# List of required packages
required_packages = [
    'requests',
    'selenium',
    'webdriver-manager', # While webdriver-manager is listed here, the script directly uses a path for chromedriver
    'tqdm',
    'jq' # Added for GitHub Actions chromedriver installation
]

# Function to install missing packages
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install required packages if they are not installed
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f"Package {package} not found, installing...")
        install_package(package)

# Logging configuration
logging.basicConfig(filename='nyt_bestsellers.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Email Configuration ---
# It is highly recommended to set these as environment variables, especially for production/CI environments.
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'LeonCountyPublicLibraryAI@gmail.com') # Default, can be overridden by env var
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', 'peeierzxenuxvacv') # Default, can be overridden by env var
RECEIVER_EMAIL_STR = os.getenv('RECEIVER_EMAILS', 'clarkp@leoncountyfl.gov,SchmickJ@leoncountyfl.gov') # Comma-separated
RECEIVER_EMAIL = [email.strip() for email in RECEIVER_EMAIL_STR.split(',')]
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# --- CatKey Export Configuration ---
output_dir = "catkey_exports"

def export_all_catkeys_to_single_file(data, filename="All_CatKeys.txt"):
    """
    Exports all collected CatKeys to a single text file, grouped by list name.
    """
    os.makedirs(output_dir, exist_ok=True)

    lines = []
    for list_name, books_data in data.items():
        catkeys = [book['catkey'] for book in books_data if book.get('catkey')]
        if catkeys:
            formatted_list_name = list_name.replace('-', ' ').title()
            line = f"{formatted_list_name}: " + ",".join(catkeys)
            lines.append(line)

    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"All CatKeys saved to '{filepath}'.")
    logging.info(f"All CatKeys saved to '{filepath}'.")
    return filepath

def send_email_with_attachment(subject, body, sender, receiver, password, attachment_path, attachment_filename):
    """Sends an email with a specified attachment."""
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['Subject'] = subject

    # Handle multiple receivers
    if isinstance(receiver, list):
        msg['To'] = ", ".join(receiver)
        to_addresses = receiver
    else:
        msg['To'] = receiver
        to_addresses = [receiver]

    msg.attach(MIMEText(body, 'plain'))

    try:
        with open(attachment_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {attachment_filename}")
        msg.attach(part)
    except Exception as e:
        print(f"Error attaching file {attachment_filename}: {e}")
        logging.error(f"Error attaching file {attachment_filename}: {e}")
        return False

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(sender, password)
        text = msg.as_string()
        server.sendmail(sender, to_addresses, text) # Modified to send to a list of recipients
        server.quit()
        print(f"Email sent successfully to {', '.join(to_addresses)}")
        logging.info(f"Email sent successfully to {', '.join(to_addresses)}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        logging.error(f"Failed to send email: {e}")
        return False

def main():
    logging.info('NYT Bestseller weekly job started.')

    import requests
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import re
    import time
    from tqdm import tqdm # Changed from tqdm.notebook

    # --- Configuration ---
    # It is highly recommended to set these as environment variables, especially for production/CI environments.
    NYT_API_KEY = os.getenv('NYT_API_KEY', 'Yn85l1gl5lKTrIgNEosEX7fvK16EGYHU') # Default, can be overridden by env var
    NYT_LIST_NAMES = [
        "hardcover-fiction",
        "hardcover-nonfiction",
        "picture-books",
        "childrens-middle-grade-hardcover",
        "young-adult-hardcover"
    ]

    # --- IMPORTANT: Configure your library's catalog search URL here ---
    # This URL is specific to your library's SirsiDynix Symphony ILS.
    # Replace YOUR_LIBRARY_CATALOG_BASE_URL with your base URL (e.g., https://yourlibrary.ent.sirsi.net)
    # Replace YOUR_LIBRARY_CLIENT_NAME with your specific client identifier (e.g., lcpl, anytown)
    LCPL_BASE_SEARCH_URL = "YOUR_LIBRARY_CATALOG_BASE_URL/client/en_US/YOUR_LIBRARY_CLIENT_NAME/search/results?qu={}&dt=list&rt=false%7C%7C%7CISBN%7C%7C%7CISBN"

    def get_nyt_bestseller_data(api_key, list_name):
        nyt_api_url = f"https://api.nytimes.com/svc/books/v3/lists/current/{list_name}.json?api-key={api_key}"
        print(f"Fetching NYT Bestsellers from: {list_name} list ({nyt_api_url})")

        bestseller_data = []
        try:
            response = requests.get(nyt_api_url)
            response.raise_for_status()
            data = response.json()

            if 'results' in data and 'books' in data['results']:
                for book in data['results']['books']:
                    isbn13 = None
                    image_url = book.get('book_image')

                    isbns_list = book.get('isbns', [])

                    for isbn_obj in isbns_list:
                        isbn13 = isbn_obj.get('isbn13')
                        if isbn13:
                            break

                    if not isbn13 and 'book_details' in book and book['book_details']:
                        primary_isbn13 = book['book_details'][0].get('primary_isbn13')
                        if primary_isbn13:
                            isbn13 = primary_isbn13
                            print(f"  (Fallback) Used primary_isbn13 for {book['book_details'][0].get('title', 'Unknown Title')}")

                    if isbn13:
                        bestseller_data.append({
                            'isbn13': isbn13,
                            'book_image': image_url if image_url else "N/A"
                        })

            else:
                print(f"Could not find 'results' or 'books' in NYT API response for list: {list_name}.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching NYT data for list {list_name}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while parsing NYT data for list {list_name}: {e}")
        return bestseller_data

    def get_catkey_from_lcpl(isbn, driver):
        search_url = LCPL_BASE_SEARCH_URL.format(isbn)
        try:
            driver.get(search_url)

            # Wait for URL to change to detail page, or a specific element to load on the detail page
            # Increased wait time for robustness, especially if network/server is slow.
            WebDriverWait(driver, 20).until(
                EC.url_contains("detailnonmodal")
            )

            final_url = driver.current_url
            match = re.search(r'SD_ILS:(\d+)/one', final_url)
            if match:
                catkey = match.group(1)
                return catkey
            else:
                # If URL doesn't match expected pattern, try to find a "no results" message
                try:
                    no_results_element = driver.find_element(By.CLASS_NAME, "NoResults")
                    if "no matches found" in no_results_element.text.lower():
                        print(f"  No catalog match found for ISBN: {isbn}")
                        logging.info(f"No catalog match found for ISBN: {isbn}")
                        return None
                except:
                    pass # Element not found, proceed
                print(f"  Catkey pattern not found in URL for ISBN: {isbn}. Final URL: {final_url}")
                logging.warning(f"Catkey pattern not found in URL for ISBN: {isbn}. Final URL: {final_url}")
                return None
        except Exception as e:
            print(f"  Error searching for ISBN {isbn} on catalog: {e}")
            logging.error(f"Error searching for ISBN {isbn} on catalog: {e}")
            return None

    all_list_bestseller_data = {}

    for list_name in NYT_LIST_NAMES:
        bestseller_data = get_nyt_bestseller_data(NYT_API_KEY, list_name)
        if bestseller_data:
            print(f"Found {len(bestseller_data)} books with ISBNs for the '{list_name}' list.")
            all_list_bestseller_data[list_name] = bestseller_data
        else:
            print(f"No books with ISBNs found or an error occurred for the '{list_name}' list.")

    print("\n--- Starting Catalog lookup for all lists ---")

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--log-level=3')
    # Add a user-agent to mimic a real browser, can sometimes help with blocking
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")


    # CHROMEDRIVER_PATH is now more flexible, trying common paths or relying on system PATH
    # The GitHub Actions workflow specifically installs it to /usr/local/bin
    CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH', '/usr/local/bin/chromedriver')


    driver = None
    try:
        service = Service(executable_path=CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)
        print(f"Successfully initialized Chrome Driver using path: {CHROMEDRIVER_PATH}")
        logging.info(f"Successfully initialized Chrome Driver using path: {CHROMEDRIVER_PATH}")

        all_list_results = {}

        # Check if the LCPL_BASE_SEARCH_URL has been configured
        if "YOUR_LIBRARY_CATALOG_BASE_URL" in LCPL_BASE_SEARCH_URL or "YOUR_LIBRARY_CLIENT_NAME" in LCPL_BASE_SEARCH_URL:
            print("\n--- IMPORTANT: LCPL_BASE_SEARCH_URL is not configured! Please update it in the script. ---")
            logging.error("LCPL_BASE_SEARCH_URL not configured. Skipping catalog lookup.")
            # Set all_list_results to empty to prevent email being sent with no data
            all_list_results = {}
        else:
            for list_name, books_data in all_list_bestseller_data.items():
                print(f"\nProcessing list: {list_name}")
                list_results = []
                for book_data in tqdm(books_data, desc=f"Looking up Catkeys for {list_name}"):
                    isbn = book_data['isbn13']
                    image_url = book_data['book_image']
                    catkey = get_catkey_from_lcpl(isbn, driver)
                    list_results.append({
                        'isbn13': isbn,
                        'book_image': image_url,
                        'catkey': catkey
                    })
                    time.sleep(1) # Be respectful to the catalog server
                all_list_results[list_name] = list_results

            print("\n--- Book Data (ISBN, Catkey, Image URL) by List ---")
            for list_name, results in all_list_results.items():
                print(f"\n--- {list_name.replace('-', ' ').title()} ---")
                if results:
                    print("{:<15} {:<15} {}".format("ISBN", "Catkey", "Image URL"))
                    print("-" * 80)

                    for book_info in results:
                        isbn_display = book_info['isbn13']
                        catkey_display = book_info['catkey'] if book_info['catkey'] else "N/A"
                        image_url_display = book_info['book_image'] if book_info['book_image'] else "N/A"
                        print(f"{isbn_display:<15} {catkey_display:<15} {image_url_display}")
                else:
                    print("No results found for this list.")

    except Exception as e:
        print(f"An error occurred during Selenium execution: {e}")
        logging.critical(f"An error occurred during Selenium execution: {e}", exc_info=True)
    finally:
        if driver:
            driver.quit()

    # --- Exporting and Emailing the CatKeys file ---
    # Only proceed if results were actually processed (i.e., not skipped due to URL config)
    if all_list_results and any(all_list_results.values()): # Check if there's any data in any list
        catkey_filename = f"NYT_Bestsellers_CatKeys_{datetime.now().strftime('%Y-%m-%d')}.txt"
        catkey_filepath = export_all_catkeys_to_single_file(all_list_results, filename=catkey_filename)

        email_subject = f"NYT Bestsellers CatKeys Report - {datetime.now().strftime('%Y-%m-%d')}"
        email_body = f"Please find attached the NYT Bestsellers CatKeys report for {datetime.now().strftime('%Y-%m-%d')}."

        send_email_with_attachment(email_subject, email_body,
                                   SENDER_EMAIL, RECEIVER_EMAIL, SENDER_PASSWORD,
                                   catkey_filepath, catkey_filename)

        if os.path.exists(catkey_filepath):
            os.remove(catkey_filepath)
            print(f"Temporary file '{catkey_filepath}' removed.")
            logging.info(f"Temporary file '{catkey_filepath}' removed.")
    else:
        print("No valid results found to generate or email a CatKeys report (check URL configuration and API calls).")
        logging.info("No valid results found to generate or email a CatKeys report.")

if __name__ == "__main__":
    main()
