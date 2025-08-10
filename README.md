# NYT-to-Library-CatKey-Generator

Fetch New York Times bestseller lists, search your SirsiDynix Enterprise catalog via Selenium, and generate **CatKey** reports.

**Features**
- Pulls NYT bestseller lists via NYT Books API
- Searches catalog by **ISBN-13**, falls back to **ISBN-10** when possible
- Generates:
  - **Found (TXT)** → per list, CatKeys only
  - **Not Found (CSV)** → list, ISBN, title, author
- Optional email with both files attached
- Headless Chrome support for PythonAnywhere or other Linux environments
- Debug mode prints each ISBN and search URL

---

## Why this exists
Designed for library selectors and tech services teams who need a **weekly, automated, accurate match** between NYT bestsellers and their library's holdings.

---

## Quick start

### 1. Clone repo
```bash
git clone https://github.com/systemslibrarian/NYT-Bestsellers-CatKey-Generator.git
cd NYT-Bestsellers-CatKey-Generator
