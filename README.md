# NYT-to-Library-CatKey-Generator

## 📖 Overview
This project is designed for **libraries using the Solus Library App** and the **SirsiDynix Symphony ILS**.  
It automates the process of collecting ISBNs from the New York Times Bestseller lists, locating their corresponding **CatKeys** in the library catalog, and emailing a grouped report of those CatKeys.

**Primary Uses:**
- 📚 Updating the **book rivers** in the Solus App with items you already own.
- 🕵️ Identifying books on the NYT Bestsellers list **that your library does not currently own**.

---

## ✨ Features
- Pulls data from **multiple NYT Bestseller lists** in one run.
- Matches ISBNs against your library catalog via **Selenium automation**.
- Produces two reports for each list:
  1. **Found** — CatKeys for titles in your collection (comma-separated, ready for Solus App).
  2. **Not Found** — Titles you do not own (CSV format for easy review).
- Can **email reports** automatically or save them locally.
- Highly configurable via environment variables or the `run_nyt_script.sh` wrapper.

---

## 📂 Output Details

### **Found File**
- Contains **comma-separated CatKeys**.
- Ready for direct **copy & paste** into the Solus App — *no reformatting required*.

### **Not Found File**
- CSV format listing ISBN, title, and author.
- Helps collection development staff quickly identify missing bestsellers.

---

## 🚀 Quick Start

### **Requirements**
- Python 3.8+
- Google Chrome + ChromeDriver
- Selenium
- tqdm
- Access to NYT Books API
- Library catalog URL (SirsiDynix Symphony Web Client)

### **Setup**
1. Clone this repository:
   ```bash
   git clone https://github.com/systemslibrarian/NYT-to-Library-CatKey-Generator.git
   cd NYT-to-Library-CatKey-Generator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set required environment variables (in `.env` or export manually):
   ```bash
   export SENDER_EMAIL="youremail@example.com"
   export SENDER_PASSWORD="yourpassword"
   export RECEIVER_EMAILS="email1@example.com,email2@example.com"
   export NYT_API_KEY="your-nyt-api-key"
   export NYT_LIST_NAMES="hardcover-fiction,hardcover-nonfiction"
   export CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"
   ```

4. Run the script via wrapper:
   ```bash
   ./run_nyt_script.sh
   ```

---

## ⚙️ Configuration via `run_nyt_script.sh`

**Options:**
```
--debug       # Verbose output (disables tqdm progress bar)
--no-debug    # Quiet mode (progress bar enabled)
--lists "a,b" # Override list names
--no-email    # Skip email sending, only generate files
```

---

## 📬 Example Email Report
**Subject:** NYT CatKey Report  
**Body:**
```
hardcover-fiction: 10 found / 5 not found
hardcover-nonfiction: 8 found / 7 not found
```

**Attachments:**
- `hardcover-fiction_found.txt`
- `hardcover-fiction_not_found.csv`
- `hardcover-nonfiction_found.txt`
- `hardcover-nonfiction_not_found.csv`

---

## 📜 License
MIT License — feel free to use and modify.

---

## 👨‍💻 Author
**Paul Clark**  
Systems Librarian & Data Analyst  
GitHub: [systemslibrarian](https://github.com/systemslibrarian)
