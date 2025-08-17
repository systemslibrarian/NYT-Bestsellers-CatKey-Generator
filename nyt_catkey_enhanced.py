#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
████████████████████████████████████████████████████████████████████████████████
█                                                                              █
█    ███    ██ ██    ██ ████████       ███████  █████  ████████ ██   ██ ███████ █
█    ████   ██  ██  ██     ██         ██      ██   ██    ██    ██  ██  ██       █
█    ██ ██  ██   ████      ██   █████ ██      ███████    ██    █████   █████    █
█    ██  ██ ██    ██       ██         ██      ██   ██    ██    ██  ██  ██       █
█    ██   ████    ██       ██          ███████ ██   ██    ██    ██   ██ ███████ █
█                                                                              █
█                     Library CatKey Generator v3.0                           █
█                     Enhanced Professional Edition                            █
█                                                                              █
████████████████████████████████████████████████████████████████████████████████

NYT-to-Library CatKey Generator v3.0 — Enhanced Professional Edition
===================================================================

DESCRIPTION
    Automates retrieval of New York Times bestseller lists and searches a
    single SirsiDynix Enterprise catalog for matching records to extract
    CatKeys. Produces TXT/CSV reports and can optionally email them.

ARCHITECTURE (ASCII)

    ┌────────────────────────┐     HTTP      ┌───────────────────────────┐
    │  NYT Books API         │ ───────────▶  │  fetch_nyt_list()         │
    └────────────────────────┘               └─────────────┬─────────────┘
                                                         books[]
                                                            │
                                                            ▼
    ┌────────────────────────┐   Selenium    ┌──────────────────────────────┐
    │ SirsiDynix Enterprise  │ ◀──────────▶ │ search_library_catalog()     │
    └────────────────────────┘               └───────────────┬──────────────┘
                                                         CatKey|None
                                                            │
                                                            ▼
    ┌────────────────────────┐     files     ┌──────────────────────────────┐
    │ generate_reports()     │ (.txt,.csv)   │ send_email_with_attachments │
    │ generate_email_summary │─────────────▶ │     (optional)              │
    └──────────┬─────────────┘               └──────────────┬──────────────┘
               │                                           │
               ▼                                           ▼
        ┌───────────────┐                           ┌─────────────────┐
        │   Logging     │◀──────────────────────────│      main()     │
        └───────────────┘                           └─────────────────┘

WORKFLOW
    1) Validate configuration (env/.env) and set up logging
    2) Launch WebDriver (headless Chrome)
    3) For each requested NYT list:
       a) Pull books from the NYT API (with retry + backoff)
       b) For each ISBN, search the catalog and extract CatKey
       c) Track found/not-found per list
    4) Generate TXT/CSV reports
    5) Optionally email reports with attachments
    6) Cleanly shut down WebDriver

FEATURES
    ✓ Single‑catalog search via CATALOG_BASE_URL
    ✓ Robust timeouts, retries, and logging
    ✓ Portable env‑based configuration (+ optional .env loader by runner)
    ✓ Professional TXT/CSV reports and optional SMTP email

REQUIRED ENV
    SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAILS,
    NYT_API_KEY, NYT_LIST_NAMES, CATALOG_BASE_URL

OPTIONAL ENV (defaults shown)
    NYT_OUTPUT_DIR=./catkey_exports
    NYT_LOG_DIR=./logs
    CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
    SMTP_SERVER=smtp.gmail.com
    SMTP_PORT=587
    NYT_DEBUG=0
    NYT_NO_EMAIL=0
    NYT_MAX_RETRIES=3
    NYT_REQUEST_TIMEOUT=15
    NYT_PAGE_TIMEOUT=20

REPORT SCHEMAS (ASCII ERD)

    ┌───────────────────────────────┐          ┌───────────────────────────────┐
    │  Found Report (TXT)           │          │  Not Found Report (CSV)       │
    ├───────────────────────────────┤          ├───────────────────────────────┤
    │ list_name: str                │          │ list: str                     │
    │ catkeys: List[str]            │          │ isbn: str                     │
    │ total_found: int              │          │ title: str                    │
    │ combined_catkeys: List[str]   │          │ author: str                   │
    └───────────────────────────────┘          └───────────────────────────────┘

TROUBLESHOOTING TREE

    start
      │
      ├─ No results?
      │    ├─ Check DNS / network
      │    ├─ Open CATALOG_BASE_URL manually
      │    └─ Increase NYT_PAGE_TIMEOUT
      │
      ├─ Sometimes times out?
      │    ├─ Add/keep 0.5s pacing
      │    └─ Tune PAGE_TIMEOUT
      │
      ├─ Detail page but no CatKey?
      │    ├─ Inspect final URL pattern
      │    ├─ Update regex r"SD_ILS:(\d+)"
      │    └─ Wait for overlays/selectors
      │
      └─ SMTP errors?
           ├─ Use app password
           ├─ Verify SMTP_SERVER/PORT
           └─ Set NYT_NO_EMAIL=1 during testing
"""
from __future__ import annotations

import os
import sys
import re
import csv
import smtplib
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

import requests
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException

# ──────────────────────────────────────────────────────────────────────────────
# Configuration validation
# ──────────────────────────────────────────────────────────────────────────────
def validate_config() -> None:
    required = [
        'SENDER_EMAIL', 'SENDER_PASSWORD', 'RECEIVER_EMAILS',
        'NYT_API_KEY', 'NYT_LIST_NAMES', 'CATALOG_BASE_URL'
    ]
    missing = [var for var in required if not os.environ.get(var)]
    if missing:
        print(
            f"ERROR: Missing required environment variables: {', '.join(missing)}",
            file=sys.stderr,
        )
        sys.exit(1)

validate_config()

# ──────────────────────────────────────────────────────────────────────────────
# Read configuration
# ──────────────────────────────────────────────────────────────────────────────
SENDER_EMAIL: str = os.environ['SENDER_EMAIL']
SENDER_PASSWORD: str = os.environ['SENDER_PASSWORD']
RECEIVER_EMAILS: List[str] = [
    e.strip() for e in os.environ.get('RECEIVER_EMAILS', '').split(',') if e.strip()
]
NYT_API_KEY: str = os.environ['NYT_API_KEY']
NYT_LIST_NAMES: List[str] = [
    l.strip() for l in os.environ.get('NYT_LIST_NAMES', '').split(',') if l.strip()
]
CATALOG_BASE_URL: str = os.environ['CATALOG_BASE_URL'].strip().rstrip('/')

OUTPUT_DIR: str = os.environ.get('NYT_OUTPUT_DIR', os.path.join(os.getcwd(), 'catkey_exports'))
LOG_DIR: str = os.environ.get('NYT_LOG_DIR', os.path.join(os.getcwd(), 'logs'))
CHROMEDRIVER_PATH: str = os.environ.get('CHROMEDRIVER_PATH', '/usr/local/bin/chromedriver')

SMTP_SERVER: str = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT: int = int(os.environ.get('SMTP_PORT', 587))

NYT_DEBUG: int = int(os.environ.get('NYT_DEBUG', '0'))
NYT_NO_EMAIL: int = int(os.environ.get('NYT_NO_EMAIL', '0'))

MAX_RETRIES: int = int(os.environ.get('NYT_MAX_RETRIES', '3'))
REQUEST_TIMEOUT: int = int(os.environ.get('NYT_REQUEST_TIMEOUT', '15'))
PAGE_TIMEOUT: int = int(os.environ.get('NYT_PAGE_TIMEOUT', '20'))

# ──────────────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────────────
os.makedirs(LOG_DIR, exist_ok=True)
_log_path = os.path.join(LOG_DIR, f"nyt_catkey_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

_handlers = [logging.FileHandler(_log_path, encoding='utf-8')]
if NYT_DEBUG:
    _handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.DEBUG if NYT_DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=_handlers,
)
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# ──────────────────────────────────────────────────────────────────────────────
# NYT API client
# ──────────────────────────────────────────────────────────────────────────────
def fetch_nyt_list(list_name: str) -> List[Dict[str, str]]:
    url = f"https://api.nytimes.com/svc/books/v3/lists/current/{list_name}.json"
    params = {'api-key': NYT_API_KEY}
    logging.info(f"Fetching NYT list: {list_name}")

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            books = data.get('results', {}).get('books', [])
            out: List[Dict[str, str]] = []
            for b in books:
                isbn13: Optional[str] = b.get('primary_isbn13')
                if not isbn13:
                    for ent in b.get('isbns', []) or []:
                        if isinstance(ent, dict) and ent.get('isbn13'):
                            isbn13 = ent['isbn13']
                            break
                if isbn13:
                    clean = re.sub(r'[^\d]', '', isbn13)
                    if len(clean) == 13:
                        out.append({
                            'isbn13': clean,
                            'title': b.get('title', 'Unknown Title'),
                            'author': b.get('author', 'Unknown Author'),
                        })
                    else:
                        logging.warning(f"Invalid ISBN13 for book: {b.get('title','Unknown')}")
            logging.info(f"Retrieved {len(out)} valid books from {list_name}")
            return out
        except requests.exceptions.Timeout:
            logging.warning(f"Timeout on attempt {attempt + 1} for {list_name}")
        except requests.exceptions.RequestException as exc:
            logging.warning(f"Request error on attempt {attempt + 1} for {list_name}: {exc}")
        if attempt < MAX_RETRIES - 1:
            wait = 2 ** attempt
            logging.info(f"Retrying in {wait} seconds…")
            time.sleep(wait)

    logging.error(f"Failed to fetch NYT list {list_name} after {MAX_RETRIES} attempts")
    return []

# ──────────────────────────────────────────────────────────────────────────────
# Selenium WebDriver
# ──────────────────────────────────────────────────────────────────────────────
def create_webdriver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--disable-extensions')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('--log-level=3')
    opts.add_experimental_option('excludeSwitches', ['enable-logging'])
    opts.add_experimental_option('useAutomationExtension', False)

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(PAGE_TIMEOUT)
    driver.implicitly_wait(5)
    return driver

# ──────────────────────────────────────────────────────────────────────────────
# Catalog search (single catalog)
# ──────────────────────────────────────────────────────────────────────────────
def _extract_catkey_from_url(url: str) -> Optional[str]:
    m = re.search(r'SD_ILS:(\d+)', url)
    return m.group(1) if m else None

def search_library_catalog(isbn: str, driver: webdriver.Chrome) -> Optional[str]:
    """Return CatKey if found, else None."""
    try:
        q1 = f"{CATALOG_BASE_URL}/search/results?qu={isbn}&dt=list&rt=false%7C%7C%7CISBN%7C%7C%7CISBN"
        driver.get(q1)
        WebDriverWait(driver, PAGE_TIMEOUT).until(
            lambda d: ('detailnonmodal' in d.current_url) or ('search/results' in d.current_url)
        )
        catkey = _extract_catkey_from_url(driver.current_url)
        if not catkey:
            links = driver.find_elements("css selector", "a[href*='SD_ILS:']")
            for a in links:
                href = a.get_attribute("href") or ""
                catkey = _extract_catkey_from_url(href)
                if catkey:
                    break
        if not catkey:
            q2 = f"{CATALOG_BASE_URL}/search/title?qu={isbn}"
            driver.get(q2)
            WebDriverWait(driver, PAGE_TIMEOUT).until(
                lambda d: ('detailnonmodal' in d.current_url) or ('search/results' in d.current_url)
            )
            catkey = _extract_catkey_from_url(driver.current_url)
            if not catkey:
                links = driver.find_elements("css selector", "a[href*=\"SD_ILS:\"]")
                for a in links:
                    href = a.get_attribute("href") or ""
                    catkey = _extract_catkey_from_url(href)
                    if catkey:
                        break
        if catkey:
            logging.debug(f"Found CatKey {catkey} for ISBN {isbn}")
            return catkey
    except TimeoutException:
        logging.warning(f"Timeout for ISBN {isbn} @ {CATALOG_BASE_URL}")
    except WebDriverException as exc:
        logging.error(f"WebDriver error for ISBN {isbn} @ {CATALOG_BASE_URL}: {exc}")
    except Exception as exc:
        logging.error(f"Unexpected error for ISBN {isbn} @ {CATALOG_BASE_URL}: {exc}")
    return None

# ──────────────────────────────────────────────────────────────────────────────
# Email helper
# ──────────────────────────────────────────────────────────────────────────────
def send_email_with_attachments(subject: str, body: str, attachments: Dict[str, str]) -> bool:
    if not RECEIVER_EMAILS:
        logging.error("No receiver emails configured")
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = ", ".join(RECEIVER_EMAILS)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        for filepath, filename in attachments.items():
            if not os.path.exists(filepath):
                logging.warning(f"Attachment not found: {filepath}")
                continue
            with open(filepath, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename=\"{filename}\"')
            msg.attach(part)
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAILS, msg.as_string())
        logging.info("Email sent successfully")
        return True
    except smtplib.SMTPAuthenticationError:
        logging.error("SMTP authentication failed - check email credentials")
    except smtplib.SMTPException as exc:
        logging.error(f"SMTP error: {exc}")
    except Exception as exc:
        logging.error(f"Email sending error: {exc}")
    return False

# ──────────────────────────────────────────────────────────────────────────────
# Reports
# ──────────────────────────────────────────────────────────────────────────────
def generate_reports(all_found_catkeys: Dict[str, List[str]],
                     all_not_found_books: List[Dict[str, str]]) -> Dict[str, str]:
    attachments: Dict[str, str] = {}
    ts = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if all_found_catkeys:
        found_name = f"NYT_Bestsellers_Found_{ts}.txt"
        found_path = os.path.join(OUTPUT_DIR, found_name)
        try:
            with open(found_path, 'w', encoding='utf-8') as f:
                f.write("NYT Bestsellers — Found CatKeys\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                all_keys: List[str] = []
                for list_name, keys in all_found_catkeys.items():
                    title = list_name.replace('-', ' ').title()
                    f.write(f"{title}:\n")
                    f.write(f"CatKeys: {','.join(keys)}\n")
                    f.write(f"Count: {len(keys)}\n\n")
                    all_keys.extend(keys)
                f.write(f"All CatKeys Combined:\n{','.join(all_keys)}\n")
            attachments[found_path] = found_name
            logging.info(f"Generated found report: {found_name}")
        except Exception as exc:
            logging.error(f"Failed to generate found report: {exc}")

    if all_not_found_books:
        nf_name = f"NYT_Bestsellers_NotFound_{ts}.csv"
        nf_path = os.path.join(OUTPUT_DIR, nf_name)
        try:
            with open(nf_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['list', 'isbn', 'title', 'author'])
                writer.writeheader()
                writer.writerows(all_not_found_books)
            attachments[nf_path] = nf_name
            logging.info(f"Generated not found report: {nf_name}")
        except Exception as exc:
            logging.error(f"Failed to generate not found report: {exc}")

    return attachments

def generate_email_summary(all_found_catkeys: Dict[str, List[str]],
                           all_not_found_books: List[Dict[str, str]]) -> str:
    total_found = sum(len(v) for v in all_found_catkeys.values())
    total_not = len(all_not_found_books)
    lines: List[str] = [
        "NYT Bestsellers CatKey Processing Complete",
        "=" * 45,
        "",
        f"Processing completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "SUMMARY:",
        f"Total found: {total_found}",
        f"Total not found: {total_not}",
        "",
        "REPORTS ATTACHED:",
        "• Found CatKeys (TXT) — CatKeys grouped by list",
        "• Not Found Books (CSV) — Books not found in catalog",
        "",
        "PER-LIST BREAKDOWN:",
    ]
    for list_name in NYT_LIST_NAMES:
        found = len(all_found_catkeys.get(list_name, []))
        not_found = sum(1 for b in all_not_found_books if b['list'] == list_name)
        lines.append(f"• {list_name.replace('-', ' ').title()}: {found} found, {not_found} not found")
    lines.extend(["", "Generated by NYT-to-Library CatKey Generator (Enhanced)"])
    return "\n".join(lines)

# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    logging.info("Using catalog base: %s", CATALOG_BASE_URL)
    driver: Optional[webdriver.Chrome] = None
    try:
        driver = create_webdriver()
        logging.info("WebDriver initialized successfully")
        all_found: Dict[str, List[str]] = {}
        not_found_rows: List[Dict[str, str]] = []
        total_processed = 0
        total_found = 0
        for list_name in NYT_LIST_NAMES:
            logging.info("Processing list: %s", list_name)
            books = fetch_nyt_list(list_name)
            if not books:
                print(f"No books found for list: {list_name}")
                continue
            perlist_found: List[str] = []
            iterator = enumerate(books, 1)
            if not NYT_DEBUG:
                iterator = tqdm(iterator, total=len(books), desc=f"Processing {list_name}")
            for idx, book in iterator:
                total_processed += 1
                isbn = book.get('isbn13')
                title = book.get('title')
                author = book.get('author')
                if not isbn:
                    not_found_rows.append({'list': list_name, 'isbn': 'N/A', 'title': title, 'author': author})
                    continue
                if NYT_DEBUG:
                    print(f"({idx}/{len(books)}) Searching: '{title}' (ISBN: {isbn})")
                catkey = search_library_catalog(isbn, driver)
                if catkey:
                    perlist_found.append(catkey)
                    total_found += 1
                    if NYT_DEBUG:
                        print(f"  -> FOUND CatKey: {catkey}")
                else:
                    not_found_rows.append({'list': list_name, 'isbn': isbn, 'title': title, 'author': author})
                    if NYT_DEBUG:
                        print("  -> NOT FOUND")
                time.sleep(0.5)
            if perlist_found:
                all_found[list_name] = perlist_found
        logging.info("Processing complete: %s/%s books found", total_found, total_processed)
        attachments = generate_reports(all_found, not_found_rows)
        if not NYT_NO_EMAIL and attachments:
            subject = f"NYT Bestsellers CatKey Report - {datetime.now().strftime('%Y-%m-%d')}"
            body = generate_email_summary(all_found, not_found_rows)
            ok = send_email_with_attachments(subject, body, attachments)
            print("Email report sent successfully." if ok else "Failed to send email report.")
        elif NYT_NO_EMAIL:
            print("Email sending skipped as per configuration.")
        else:
            print("No reports generated or email not configured.")
        print(f"Processing complete: {total_found} found, {len(not_found_rows)} not found")
    finally:
        if driver:
            try:
                driver.quit()
                logging.info("WebDriver cleaned up successfully")
            except Exception as exc:
                logging.warning(f"Error during WebDriver cleanup: {exc}")

if __name__ == '__main__':
    main()
