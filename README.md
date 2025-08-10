# 📚 NYT-Bestsellers-CatKey-Generator

Automates the process of collecting **ISBNs** from the New York Times Bestseller lists, finding their matching **CatKeys** in your library’s catalog, and generating easy-to-use reports.  

Designed for libraries using **SirsiDynix Symphony** and the **Solus Library App**.

---

## ✨ Features

- 🔍 **Multi-list support** — Pull multiple NYT Bestseller categories in one run.
- 🆔 **ISBN-10 / ISBN-13 detection** — Improves catalog match accuracy.
- 🖥 **Automated catalog searches** via Selenium.
- 📂 **Two reports per list**:  
  - `*_found.txt` — Comma-separated CatKeys for direct Solus import.  
  - `*_not_found.csv` — Books your library does **not** currently own.
- 📧 **Automatic email delivery** of reports (optional).
- 🛠 **Debug mode** for step-by-step output.

---

## 🛠 Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

You’ll need:
- Python 3.8+
- Google Chrome + ChromeDriver
- NYT API Key ([Get one here](https://developer.nytimes.com/))
- SirsiDynix Symphony catalog access

---

## ⚙️ Configuration

All settings are controlled via **environment variables**:

| Variable | Description |
|----------|-------------|
| `NYT_API_KEY` | Your NYT API key |
| `SENDER_EMAIL` | Sender email address |
| `SENDER_PASSWORD` | Email account password |
| `RECEIVER_EMAILS` | Comma-separated recipient list |
| `NYT_LIST_NAMES` | Comma-separated NYT list names (e.g. `hardcover-fiction,young-adult-hardcover`) |
| `NYT_OUTPUT_DIR` | Directory for output files |
| `NYT_LOG_DIR` | Directory for logs |
| `CHROMEDRIVER_PATH` | Path to ChromeDriver |
| `NYT_DEBUG` | `1` for detailed per-ISBN output |
| `NYT_NO_EMAIL` | `1` to skip sending email |

---

## 🚀 Usage

Run **all lists**:

```bash
./run_nyt_script.sh
```

Run **one category for quick testing**:

```bash
NYT_LIST_NAMES=hardcover-fiction ./NYT-to-Library-CatKey-Generator.py
```

Skip email sending:

```bash
NYT_NO_EMAIL=1 ./run_nyt_script.sh
```

---

## 📄 Output Files

For each NYT list processed, two files are created:

1. **`<list>_found.txt`**  
   - Comma-separated CatKeys — ready for Solus import.
   - Example:  
     ```
     12345,67890,54321
     ```

2. **`<list>_not_found.csv`**  
   - ISBN, title, and author of items **not in your catalog**.

---

## 💡 Why It’s Useful

- Quickly identify NYT bestsellers your library already owns.
- Instantly know which popular titles are missing from your collection.
- Load found CatKeys directly into Solus “book rivers” — no manual formatting required.

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.
