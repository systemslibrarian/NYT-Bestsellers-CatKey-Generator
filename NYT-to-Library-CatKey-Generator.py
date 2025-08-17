#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NYT-to-Library CatKey Generator v3.2 — Single Catalog Edition
==============================================================
Fetches New York Times bestseller lists and extracts SirsiDynix CatKeys.
Configuration via environment variables (.env).

Environment:
    CATALOG_BASE_URL, NYT_API_KEY, NYT_LIST_NAMES, SENDER_EMAIL,
    SENDER_PASSWORD, RECEIVER_EMAILS
Optional:
    NYT_OUTPUT_DIR, NYT_LOG_DIR, NYT_DEBUG, NYT_NO_EMAIL
"""

import os
import re
import time
import logging
import requests
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def get_catalog_base_url() -> str:
    base = os.environ.get("CATALOG_BASE_URL")
    if not base:
        raise RuntimeError("No catalog base URL configured. Set CATALOG_BASE_URL.")
    return base.strip()

def search_library_catalog(isbn: str, driver: webdriver.Chrome, base_url: str) -> Optional[str]:
    try:
        search_url = f"{base_url}/search/title?qu={isbn}"
        driver.get(search_url)
        time.sleep(2)
        detail_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='SD_ILS']")
        if detail_links:
            href = detail_links[0].get_attribute("href")
            match = re.search(r"SD_ILS:(\d+)", href)
            if match:
                return match.group(1)
    except Exception as e:
        logging.warning(f"Error searching {base_url} for ISBN {isbn}: {e}")
    return None

def main():
    base_url = get_catalog_base_url()
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    try:
        catkey = search_library_catalog("9780385545969", driver, base_url)
        print("Found:", catkey)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
