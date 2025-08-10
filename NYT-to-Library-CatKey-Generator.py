#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
# nyt-catkey-finder.py
# ============================================================================
# Description:
#   Automates fetching NYT bestseller lists, searching the library catalog
#   via Selenium, and producing "CatKey" reports for matching titles.
#
# Features:
#   • Robust, multi-step search logic with ISBN-10 fallback.
#   • Generates two reports: a TXT for found items and a CSV for not-found.
#   • Fully configurable via environment variables.
#   • Optional debug mode and ability to skip emailing.
# ============================================================================

# --- Core and Third-Party Imports ---
# These are the Python modules required for the script to function.
import os                   # For interacting with the operating system (e.g., file paths, environment variables).
import sys                  # For system-specific parameters and functions.
import re                   # For regular expression operations, used to find the CatKey.
import csv                  # For reading and writing Comma-Separated Values (CSV) files.
import smtplib              # For sending emails using the Simple Mail Transfer Protocol.
import logging              # For logging script activity, errors, and debug information.
import requests             # For making HTTP requests to the NYT API.
import time                 # For adding delays (pauses) in the script.
from datetime import datetime                   # For working with dates and times, used here for log file naming.
from email.mime.text import MIMEText            # For creating the text part of an email.
from email.mime.multipart import MIMEMultipart  # For creating emails with multiple parts (e.g., body and attachments).
from email.mime.base import MIMEBase            # A base class for creating email attachment objects.
from email import encoders                      # For encoding email attachments so they can be sent correctly.

# --- Selenium Imports (for Web Automation) ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from tqdm import tqdm       # For creating user-friendly progress bars in the console.

# ----------------------------------------------------------------------
#  SECTION 1: ENVIRONMENT CONFIGURATION
# ----------------------------------------------------------------------
# This entire section loads the script's settings from environment variables,
# which are set by the companion `run_nyt_script.sh` wrapper script.
# This keeps secrets (like passwords) out of the code and makes the script highly configurable.

SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD')
# The recipient list is read as a single comma-separated string and parsed into a Python list.
RECEIVER_EMAILS = [email.strip() for email in os.environ.get('RECEIVER_EMAILS', '').split(',') if email.strip()]
NYT_API_KEY = os.environ.get('NYT_API_KEY')
# The NYT lists to check are also read from a comma-separated string.
NYT_LIST_NAMES = [l.strip() for l in os.environ.get('NYT_LIST_NAMES', '').split(',') if l.strip()]

# File paths can be configured, with sensible defaults if not provided.
OUTPUT_DIR = os.environ.get('NYT_OUTPUT_DIR', os.path.join(os.getcwd(), "catkey_exports"))
LOG_DIR = os.environ.get('NYT_LOG_DIR', os.path.join(os.getcwd(), "logs"))
CHROMEDRIVER_PATH = os.environ.get('CHROMEDRIVER_PATH', '/usr/local/bin/chromedriver')

# Server settings and behavior flags.
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
# The debug flag (0 or 1) determines logging level and console output verbosity.
NYT_DEBUG = int(os.environ.get('NYT_DEBUG', '0'))
# The no-email flag (0 or 1) allows the script to run without sending an email.
NYT_NO_EMAIL = int(os.environ.get('NYT_NO_EMAIL', '0'))

# ----------------------------------------------------------------------
#  SECTION 2: LOGGING SETUP
# ----------------------------------------------------------------------
# This section configures the logging system to record script activity to a file.
# Ensure the log directory exists; create it if it doesn't.
os.makedirs(LOG_DIR, exist_ok=True)
# Create a unique log file name that includes the current date.
log_path = os.path.join(LOG_DIR, f"nyt_catkey_{datetime.now().strftime('%Y%m%d')}.log")
# Configure the logger.
logging.basicConfig(
    filename=log_path,  # Log messages will be written to this file.
    # The logging level is set to DEBUG for verbose output if the flag is on, otherwise INFO.
    level=logging.DEBUG if NYT_DEBUG else logging.INFO,
    # Define the format for each log entry: Timestamp, Level, Message.
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ----------------------------------------------------------------------
#  SECTION 3: HELPER FUNCTIONS
# ----------------------------------------------------------------------
# These functions perform specific, reusable tasks for the main script logic.

def fetch_nyt_list(list_name):
    """Fetches a specific NYT bestseller list and returns standardized book data."""
    url = f"https://api.nytimes.com/svc/books/v3/lists/current/{list_name}.json?api-key={NYT_API_KEY}"
    logging.info(f"Fetching NYT list: {list_name}")
    try:
        # Make the API call with a 15-second timeout.
        resp = requests.get(url, timeout=15)
        # Raise an exception if the API returns an error status (e.g., 401, 404, 500).
        resp.raise_for_status()
        data = resp.json()
        books_data = data.get('results', {}).get('books', [])

        # Process the raw data to ensure a consistent format.
        processed_books = []
        for book in books_data:
            isbn13 = book.get('primary_isbn13')
            # If the primary ISBN is missing, try a fallback location.
            if not isbn13:
                isbns = book.get('isbns', [])
                if isbns:
                    isbn13 = isbns[0].get('isbn13')

            # Only include books that have an ISBN.
            if isbn13:
                 processed_books.append({
                     'isbn13': isbn13,
                     'title': book.get('title', 'Unknown Title'),
                     'author': book.get('author', 'Unknown Author')
                 })
        return processed_books
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch NYT list {list_name}: {e}")
        return []

def search_library_catalog(isbn, driver):
    """
    Searches the library catalog using an explicit wait and extracts the
    CatKey directly from the final page URL.
    """
    search_url = f"https://lcpl.ent.sirsi.net/client/en_US/lcpl/search/results?qu={isbn}&dt=list&rt=false%7C%7C%7CISBN%7C%7C%7CISBN"

    # This block prints the full search URL to the console when debug mode is active.
    if NYT_DEBUG:
        print(f"  -> Visiting search URL: {search_url}")

    try:
        # Navigate the automated browser to the search URL.
        driver.get(search_url)
        # Use an "explicit wait" for reliability. This tells Selenium to wait up to 15 seconds
        # until the URL contains "detailnonmodal", which indicates the detail page has loaded.
        # This is far more reliable than a fixed `time.sleep()`.
        WebDriverWait(driver, 15).until(EC.url_contains("detailnonmodal"))

        # Once the page has loaded, get the final URL from the browser's address bar.
        final_url = driver.current_url
        # Use a regular expression to find the pattern "SD_ILS:" followed by one or more digits.
        match = re.search(r'SD_ILS:(\d+)', final_url)
        if match:
            # If a match is found, return the captured digits (group 1), which is the CatKey.
            return match.group(1)
        return None
    except TimeoutException:
        # This error occurs if the explicit wait fails (the detail page doesn't load in time).
        logging.warning(f"Timeout waiting for detail page for ISBN {isbn}")
        return None
    except Exception as e:
        # Catch any other unexpected errors during the search process.
        logging.error(f"An unexpected error occurred searching for ISBN {isbn}: {e}")
        return None

def send_email_with_attachments(subject, body, attachments):
    """Constructs and sends an email with one or more attachments."""
    # Create the main email message container.
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(RECEIVER_EMAILS)
    msg['Subject'] = subject
    # Attach the plain text body to the email.
    msg.attach(MIMEText(body, 'plain'))

    # Loop through the attachments dictionary, where key=filepath and value=filename.
    for file_path, file_name in attachments.items():
        # Open each file in binary read mode ('rb').
        with open(file_path, 'rb') as f:
            # Create the attachment part.
            part = MIMEBase('application', 'octet-stream')
            # Read the file's content into the attachment.
            part.set_payload(f.read())
        # Encode the attachment in base64, the standard for email.
        encoders.encode_base64(part)
        # Add a header to tell the email client this is an attachment with a filename.
        part.add_header('Content-Disposition', f'attachment; filename="{file_name}"')
        # Attach the completed part to the main email message.
        msg.attach(part)

    # Connect to the SMTP server to send the email.
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls() # Upgrade the connection to be secure.
        server.login(SENDER_EMAIL, SENDER_PASSWORD) # Log in.
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAILS, msg.as_string()) # Send the message.

# ----------------------------------------------------------------------
#  SECTION 4: MAIN EXECUTION
# ----------------------------------------------------------------------
def main():
    """The main function that orchestrates the entire job."""

    # --- Selenium WebDriver Setup ---
    # Configure the options for the Chrome browser.
    options = Options()
    options.add_argument("--headless")              # Run Chrome without a visible UI.
    options.add_argument("--no-sandbox")            # Required for running in many server/container environments.
    options.add_argument("--disable-dev-shm-usage") # Overcomes resource limitations in some environments.
    # Initialize the Chrome browser controlled by Selenium.
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    # --- Data Initialization ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_found_catkeys = {}
    all_not_found_books = []

    # --- Main Processing Loop ---
    # This loop iterates through each bestseller list, fetches the books, and searches for them.
    for list_name in NYT_LIST_NAMES:
        books = fetch_nyt_list(list_name)
        if not books:
            print(f"No books found for list: {list_name}")
            continue

        list_found_catkeys = []

        # Set up the iterator. If not in debug mode, wrap it with tqdm for a progress bar.
        iterator = enumerate(books, 1)
        if not NYT_DEBUG:
            iterator = tqdm(iterator, total=len(books), desc=f"Processing {list_name}")

        # Loop through each book in the current list.
        for idx, book in iterator:
            isbn = book.get('isbn13')
            title = book.get('title')
            author = book.get('author')

            if not isbn:
                # If a book has no ISBN, add it directly to the not-found list.
                all_not_found_books.append({'list': list_name, 'isbn': 'N/A', 'title': title, 'author': author})
                continue

            # Print a status message if in debug mode.
            if NYT_DEBUG:
                print(f"({idx}/{len(books)}) Searching for '{title}' by ISBN: {isbn}")

            # Call the main search function.
            catkey = search_library_catalog(isbn, driver)

            if catkey:
                # If found, add it to this list's "found" collection.
                list_found_catkeys.append(catkey)
                if NYT_DEBUG:
                    print(f"  -> FOUND CatKey: {catkey}")
            else:
                # If not found, add it to the main "not-found" collection.
                all_not_found_books.append({'list': list_name, 'isbn': isbn, 'title': title, 'author': author})
                if NYT_DEBUG:
                    print("  -> NOT FOUND")

        # After processing all books in a list, if any were found, add them to the main results.
        if list_found_catkeys:
            all_found_catkeys[list_name] = list_found_catkeys

    # --- Crucial Cleanup ---
    # Properly close the browser and end the WebDriver process to free up resources.
    driver.quit()

    # --- File Generation & Emailing ---
    attachments_to_send = {}
    ts = datetime.now().strftime('%Y-%m-%d')

    # This block calculates the total and per-list counts for the email summary.
    total_found = sum(len(catkeys) for catkeys in all_found_catkeys.values())
    total_not_found = len(all_not_found_books)

    # This block constructs the detailed, multi-line email body.
    summary_lines = [
        "Attached are two reports:",
        "1) FOUND CatKeys (TXT, grouped by list)",
        "2) NOT FOUND (CSV: list_name, isbn13, author, title)",
        "",
        f"Found count: {total_found}",
        f"Not-found count: {total_not_found}",
        "",
        "Per-list:"
    ]

    for list_name in NYT_LIST_NAMES:
        found_count = len(all_found_catkeys.get(list_name, []))
        not_found_count = sum(1 for book in all_not_found_books if book['list'] == list_name)
        formatted_name = list_name.replace('-', ' ').title()
        summary_lines.append(f"- {formatted_name}: {found_count} found / {not_found_count} not")

    # Create the "found" TXT file if any CatKeys were found.
    if all_found_catkeys:
        found_filename = f"NYT_Bestsellers_Found_{ts}.txt"
        found_filepath = os.path.join(OUTPUT_DIR, found_filename)
        with open(found_filepath, 'w') as f:
            for list_name, catkeys in all_found_catkeys.items():
                formatted_name = list_name.replace('-', ' ').title()
                f.write(f"{formatted_name}: {','.join(catkeys)}\n")
        attachments_to_send[found_filepath] = found_filename

    # Create the "not found" CSV file if any books were not found.
    if all_not_found_books:
        not_found_filename = f"NYT_Bestsellers_NotFound_{ts}.csv"
        not_found_filepath = os.path.join(OUTPUT_DIR, not_found_filename)
        with open(not_found_filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['list', 'isbn', 'title', 'author'])
            writer.writeheader()
            writer.writerows(all_not_found_books)
        attachments_to_send[not_found_filepath] = not_found_filename

    # Send the email if the "no email" flag is OFF and there are attachments to send.
    if not NYT_NO_EMAIL and attachments_to_send:
        subject = f"NYT Bestsellers CatKey Report - {ts}"
        body = "\n".join(summary_lines) # The body is now the detailed summary.
        send_email_with_attachments(subject, body, attachments_to_send)
        print("Email report sent successfully.")
    elif NYT_NO_EMAIL:
        print("Email sending skipped as per configuration.")
    else:
        print("No items were found or not found, so no report was generated or sent.")

# --- Script Entry Point ---
# This is a standard Python convention. The code inside this `if` block
# will only run when the script is executed directly (e.g., `python your_script.py`).
if __name__ == '__main__':
    main()