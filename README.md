# NYT-to-Library-CatKey-Generator

Fetch New York Times bestseller lists, search your SirsiDynix Enterprise catalog (LCPL example) via Selenium, and generate **CatKey** reports:
- **FOUND** → TXT (per list: `List Name: catkey1,catkey2,...`)
- **NOT FOUND** → CSV (`list_name,isbn13,author,title`)
- Optional email delivery with both files attached.

> Built and maintained by Paul Clark (systemslibrarian)

---

## Why this exists
- Automates weekly bestseller processing for selectors/tech services
- Robust ISBN search: tries **ISBN-13**, then **ISBN-10** fallback (for 978-prefix)
- Works headless on PythonAnywhere (or any Linux host with Chromium/Chrome + chromedriver)

---

## Quick start

1) **Clone**
```bash
git clone https://github.com/systemslibrarian/NYT-Bestsellers-CatKey-Generator.git
cd NYT-Bestsellers-CatKey-Generator
