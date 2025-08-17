# NYT‑to‑Library CatKey Generator v3.0 — Enhanced Professional Edition (Single Catalog)

```
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
```

An automation tool that fetches **New York Times bestseller** lists and searches a **SirsiDynix Enterprise** catalog to extract **CatKeys**. Produces TXT/CSV reports and can email them.

---

## Files

- `nyt_catkey_enhanced.py` — Full Python app (single catalog, ASCII docs, documented functions).
- `run_nyt_script.sh` — Runner with ASCII header and optional `.env` loading.
- `nyt_catkey.env.example` — Example configuration (LCPL provided as sample).

> **No hardcoded LCPL in code.** Configure the catalog with `CATALOG_BASE_URL`.

---

## Requirements

- Python 3.8+
- Google Chrome + chromedriver (configurable via `CHROMEDRIVER_PATH`)
- Python packages: `requests`, `selenium`, `tqdm`

Install packages:
```bash
pip install -r <(printf "requests\nselenium\ntqdm\n")
```

---

## Configuration

**Required**
- `SENDER_EMAIL`, `SENDER_PASSWORD`, `RECEIVER_EMAILS`
- `NYT_API_KEY`
- `NYT_LIST_NAMES` (or use defaults via runner)
- `CATALOG_BASE_URL` (single base, no multi-catalog)

**Optional (defaults)**
- `NYT_OUTPUT_DIR`, `NYT_LOG_DIR`, `CHROMEDRIVER_PATH`
- `SMTP_SERVER`, `SMTP_PORT`
- `NYT_DEBUG`, `NYT_NO_EMAIL`
- `NYT_MAX_RETRIES`, `NYT_REQUEST_TIMEOUT`, `NYT_PAGE_TIMEOUT`

Copy and edit:
```bash
cp nyt_catkey.env.example .env
```

---

## Usage

Make runner executable:
```bash
chmod +x run_nyt_script.sh
```

Run (loads `.env`):
```bash
./run_nyt_script.sh --env ./.env --quick-test --debug
```

---

## Reports

- **TXT**: Found CatKeys by list + combined list
- **CSV**: Not‑found rows with list, ISBN, title, author

---

## License

MIT
