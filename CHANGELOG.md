# Changelog

## v3.0 — Enhanced Professional Edition (Single Catalog)
**Refined Release — Single Catalog Only**

### ✨ Key Changes
- **Single Catalog Configuration**  
  - Removed multi-catalog support and `--bases` runner flag.
  - `CATALOG_BASE_URL` is now **required** and is the sole catalog endpoint.

- **ASCII Art & Documentation**  
  - ASCII banner, architecture, and troubleshooting tree retained.
  - Function-level docstrings and comments throughout.

- **Runner Simplification**  
  - Loads `.env` (optional), supports debug, quick-test, and list overrides.
  - Startup summary reflects single-catalog config.

- **Security & Packaging**  
  - No hardcoded credentials or URLs.
  - Example `.env` shows LCPL as a sample (not required in code).
  - Updated README for single-catalog assumptions.
