# NYT-to-Library CatKey Generator v3.2

Automates retrieval of New York Times bestseller lists and matches ISBNs against a SirsiDynix Enterprise catalog to extract CatKeys. Produces TXT/CSV reports and can optionally email them.

## Features
- Single catalog support (no hardcoding, configured via `.env`)
- Headless Selenium with retries and logging
- Portable configuration via environment variables
- TXT + CSV reports

## Requirements
- Python 3.8+
- `requests`, `selenium`, `tqdm`

## Setup
1. Clone the repo.
2. Copy `.env.example` to `.env` and fill in values.
3. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```
4. Run:  
   ```bash
   ./run_nyt_script.sh
   ```

## Configuration
Main env vars:
- `CATALOG_BASE_URL` — SirsiDynix catalog base URL
- `NYT_API_KEY` — NYT Books API key
- `NYT_LIST_NAMES` — Comma-separated list names (e.g. `hardcover-fiction`)

## License
MIT
