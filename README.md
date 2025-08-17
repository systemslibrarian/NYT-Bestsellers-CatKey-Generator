# 📚 NYT-to-Library-CatKey-Generator

Automates the process of generating **library catalog keys (CatKeys)** from the **New York Times Bestseller API**.  
Designed for libraries to easily integrate bestseller lists into their catalogs.

---

## ✨ Features

- Fetches **Bestseller data** from the *New York Times API*  
- Exports results into **TXT + CSV files** for catalog integration  
- Optional **automated email delivery** of reports  
- Configurable **list categories**, **output locations**, and **SMTP settings**  
- Debug and quick-test modes for safe iteration  

---

## 📁 Project Structure

```
NYT-to-Library-CatKey-Generator/
├── NYT-to-Library-CatKey-Generator.py   # Main Python script
├── run_nyt_script.sh                    # Runner script with env setup
├── .env.example                         # Example environment variables
├── README.md                            # Documentation
├── requirements.txt                     # Python dependencies
└── CHANGELOG.md                         # Version history
```

---

## 🛠 Requirements

- **Python 3.8+**  
- Google Chrome + ChromeDriver  
- New York Times API key  
- Gmail (or other SMTP) credentials  

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file (copy from `.env.example`) with:

```
NYT_API_KEY=your-nyt-api-key
LIBRARY_CODE=LCPL
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=youremail@gmail.com
SMTP_PASSWORD=yourpassword
OUTPUT_DIR=./output
```

---

## ▶️ Running the Script

**Direct Run**

```bash
python3 NYT-to-Library-CatKey-Generator.py
```

**Using the Runner (with `.env` auto-load)**

```bash
./run_nyt_script.sh
```

Make it executable if needed:

```bash
chmod +x run_nyt_script.sh
```

---

## 📤 Output

- Bestseller list reports saved as `.txt` and `.csv` in the output directory  
- Optional email summary if SMTP is configured  

---

## 📅 Example Crontab (Run Daily at 8 AM)

```bash
0 8 * * * /home/systemsLibrarian/run_nyt_script.sh >> /home/systemsLibrarian/logs/nyt.log 2>&1
```

---

## 🤝 Credits

- Maintained by **Leon County Public Library**  
- Built for internal automation of **NYT Bestseller → Library Catalog** workflows  

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.
