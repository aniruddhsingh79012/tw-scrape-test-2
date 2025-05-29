from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def extract_auth_token(username, password):
    options = Options()
    # Uncomment the next line to run in headless mode
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("start-maximized")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://twitter.com/login")
        wait = WebDriverWait(driver, 15)

        # Step 1: Enter username
        username_input = wait.until(EC.presence_of_element_located((By.NAME, "text")))
        username_input.send_keys(username)
        username_input.send_keys(Keys.RETURN)

        # Step 2: Enter password
        password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)

        # Wait for login to complete
        time.sleep(5)

        # Check cookies for auth_token
        cookies = driver.get_cookies()
        for cookie in cookies:
            if cookie['name'] == 'auth_token':
                return cookie['value']

        return None

    except Exception as e:
        print(f"Error logging in as {username}: {e}")
        return None
    finally:
        driver.quit()

# Read account data and extract tokens
with open('twitteracc.txt', 'r') as file:
    for line in file:
        parts = line.strip().split(':')
        if len(parts) >= 2:
            username, password = parts[0], parts[1]
            token = extract_auth_token(username, password)
            if token:
                print(f"{username}: {token}")
            else:
                print(f"{username}: Failed to retrieve auth_token")
