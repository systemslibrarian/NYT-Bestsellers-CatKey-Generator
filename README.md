# NYT Bestsellers CatKey Generator

This project is designed for libraries using the Solus Library App and the SirsiDynix Symphony ILS. It automates the process of collecting ISBNs from the New York Times Bestseller lists, locating their corresponding CatKeys in the library catalog, and emailing a grouped report of those CatKeys. Useful for book rivers within the app.

## Features

* Fetches ISBNs for specified NYT Bestseller lists.
* Searches your library's SirsiDynix Symphony catalog using the collected ISBNs to find CatKeys.
* Generates a single text file containing all found CatKeys, grouped by bestseller list.
* Emails the generated CatKey report as an attachment to specified recipients.
* Includes logging for tracking script execution.

## Setup and Installation

### Prerequisites

* Python 3.x
* A Google account with "App Passwords" enabled if using Gmail for sending emails. **Using an App Password is required and more secure than "Less secure app access" which Google has deprecated.**
* A New York Times Developer Account to obtain an API Key.

### Steps

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/NYT-Bestsellers-CatKey-Generator.git](https://github.com/YOUR_USERNAME/NYT-Bestsellers-CatKey-Generator.git)
    cd NYT-Bestsellers-CatKey-Generator
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

You **must** configure the following variables in the `nyt_bestsellers_scraper.py` file, and it is highly recommended to set sensitive credentials as environment variables or GitHub Secrets for scheduled runs.

1.  **Library Catalog Search URL (`LCPL_BASE_SEARCH_URL`)**:
    In `nyt_bestsellers_scraper.py`, locate the `LCPL_BASE_SEARCH_URL` variable. This URL is specific to your library's SirsiDynix Symphony ILS.

    **Find this line:**
    ```python
    LCPL_BASE_SEARCH_URL = "YOUR_LIBRARY_CATALOG_BASE_URL/client/en_US/YOUR_LIBRARY_CLIENT_NAME/search/results?qu={}&dt=list&rt=false%7C%7C%7CISBN%7C%7C%7CISBN"
    ```

    **And replace the placeholders with your library's specific information:**
    * `YOUR_LIBRARY_CATALOG_BASE_URL`: The base domain of your library's SirsiDynix catalog (e.g., `https://yourcity.ent.sirsi.net`).
    * `YOUR_LIBRARY_CLIENT_NAME`: Your library's specific client identifier used in the SirsiDynix URL (e.g., `lcpl`, `anytown`, `mainlib`).

    **Example:** If your catalog URL for "Anytown Public Library" is `https://anytown.ent.sirsi.net/client/en_US/anytown/`, then you would set:
    ```python
    LCPL_BASE_SEARCH_URL = "[https://anytown.ent.sirsi.net/client/en_US/anytown/search/results?qu=](https://anytown.ent.sirsi.net/client/en_US/anytown/search/results?qu=){}&dt=list&rt=false%7C%7C%7CISBN%7C%7C%7CISBN"
    ```

2.  **Sensitive Credentials (Environment Variables / GitHub Secrets):**

    For security, it is **highly recommended** to use environment variables (for local execution) or GitHub Secrets (for GitHub Actions) for the following:

    * `NYT_API_KEY`: Your New York Times Books API key.
    * `SENDER_EMAIL`: The email address from which the reports will be sent (e.g., `library.reports@gmail.com`).
    * `SENDER_PASSWORD`: The App Password for the `SENDER_EMAIL` (if using Gmail, generate an App Password from your Google Account settings).
    * `RECEIVER_EMAILS`: A comma-separated list of recipient email addresses (e.g., `recipient1@example.com,recipient2@example.com`).

    **Example for setting environment variables (Linux/macOS):**
    ```bash
    export NYT_API_KEY="Yn85l1gl5lKTrIgNEosEX7fvK16EGYHU"
    export SENDER_EMAIL="your_email@gmail.com"
    export SENDER_PASSWORD="your_app_password"
    export RECEIVER_EMAILS="recipient1@example.com,recipient2@example.com"
    ```
    **Example for setting environment variables (Windows - Command Prompt):**
    ```cmd
    set NYT_API_KEY="Yn85l1gl5lKTrIgNEosEX7fvK16EGYHU"
    set SENDER_EMAIL="your_email@gmail.com"
    set SENDER_PASSWORD="your_app_password"
    set RECEIVER_EMAILS="recipient1@example.com,recipient2@example.com"
    ```
    (Replace placeholder values with your actual credentials.)

    **Alternatively (less secure, only for quick local testing and never for public repositories), you can directly modify these lines in `nyt_bestsellers_scraper.py`:**
    ```python
    NYT_API_KEY = "YOUR_NYT_API_KEY_HERE"
    SENDER_EMAIL = 'your_sender_email@gmail.com'
    SENDER_PASSWORD = 'your_app_password_here'
    RECEIVER_EMAIL = ['recipient1@example.com', 'recipient2@example.com'] # Convert this to a list if hardcoding
    ```

3.  **Chromedriver Setup (`CHROMEDRIVER_PATH`)**:
    The script uses Selenium and Chromedriver to interact with the catalog website. The script attempts to use `/usr/local/bin/chromedriver` by default, which is common on Linux systems and is where the GitHub Actions workflow installs it.

    If your Chromedriver is located elsewhere, you can set an environment variable `CHROMEDRIVER_PATH` to its full path, or you can directly modify the `CHROMEDRIVER_PATH` variable in `nyt_bestsellers_scraper.py`:
    ```python
    CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH', '/usr/local/bin/chromedriver') # Update this line if necessary
    ```
    You can download Chromedriver from [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads) (make sure to match your Chrome browser version) and place it in a directory that's in your system's PATH, or specify its full path.

## Usage

To run the script:

```bash
python nyt_bestsellers_scraper.py
