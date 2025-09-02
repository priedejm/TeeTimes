import time as sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import os
from datetime import date, timedelta

CSRF_TOKEN = "Xf0R600W0Q0E2D481X2O2O5D604X6D57066Z4U5E4C0N5N5W5C4E71564Z6T4Z065Y4L466C6D674S6M6H0T5G4C5I6M19724R553Y0264566O50046D5R4S6K1P5M625G"
NUMBER_OF_PLAYERS = 1
BEGIN_TIME = "+7%3A00AM"
NUMBER_OF_HOLES = 18
CHROMEDRIVER_PATH = "/opt/homebrew/bin/chromedriver"

def get_target_date(day_of_week):
    today = date.today()
    day_of_week_map = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2,
        "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
    }
    target_day = day_of_week_map.get(day_of_week)
    if target_day is None:
        raise ValueError("Invalid day of the week")
    days_ahead = (target_day - today.weekday() + 7) % 7
    target_date = today + timedelta(days=days_ahead)
    return target_date.strftime("%m%%2F%d%%2F%Y")  # mm%2Fdd%2Fyyyy

def get_target_filename(day_of_week):
    readable_date = get_target_date(day_of_week).replace("%2F", "-")
    return f"muni_tee_times_{readable_date}.txt"

def read_saved_tee_times(file_path):
    saved_times = set()
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            for line in file:
                saved_times.add(line.strip())
    return saved_times

def save_tee_times(file_path, tee_times):
    with open(file_path, "w") as file:
        for tee_time in tee_times:
            file.write(f"{tee_time}\n")

def scrape_tee_times(dayOfWeek):
    url = (
        f"https://sccharlestonweb.myvscloud.com/webtrac/web/search.html?"
        f"Action=Start&SubAction=&_csrf_token={CSRF_TOKEN}&numberofplayers={NUMBER_OF_PLAYERS}"
        f"&secondarycode=&begindate={get_target_date(dayOfWeek)}&begintime={BEGIN_TIME}"
        f"&numberofholes={NUMBER_OF_HOLES}&display=Detail&module=GR&multiselectlist_value="
        f"&grwebsearch_buttonsearch=yes"
    )
    print(f"[INFO] Navigating to: {url}")

    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    service = Service(CHROMEDRIVER_PATH)
    driver = None
    new_tee_times_list = []

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("[INFO] WebDriver started successfully")
        driver.get(url)
        sleep.sleep(5)

        cart_buttons = driver.find_elements(By.CLASS_NAME, "button-cell--cart")
        print(f"[INFO] Found {len(cart_buttons)} tee time buttons on page")

        current_tee_times = []
        for button in cart_buttons:
            parent_row = button.find_element(By.XPATH, "ancestor::tr")
            time_val = parent_row.find_element(By.XPATH, ".//td[@data-title='Time']").text
            date_val = parent_row.find_element(By.XPATH, ".//td[@data-title='Date']").text
            holes = parent_row.find_element(By.XPATH, ".//td[@data-title='Holes']").text
            course = parent_row.find_element(By.XPATH, ".//td[@data-title='Course']").text
            open_slots = parent_row.find_element(By.XPATH, ".//td[@data-title='Open Slots']").text

            tee_time = f"Time: {time_val}, Date: {date_val}, Holes: {holes}, Course: {course}, Open Slots: {open_slots}"
            current_tee_times.append(tee_time)
            print(f"[FOUND] {tee_time}")

        file_path = get_target_filename(dayOfWeek)
        saved_tee_times = read_saved_tee_times(file_path)
        print(f"[INFO] Loaded {len(saved_tee_times)} saved times from file")

        # Detect new tee times
        for tee_time in current_tee_times:
            if tee_time not in saved_tee_times:
                new_tee_times_list.append(tee_time)

        if new_tee_times_list:
            print(f"[INFO] Found {len(new_tee_times_list)} new tee times!")
        else:
            print("[INFO] No new tee times found.")

        # Save the current list to file (overwrite)
        save_tee_times(file_path, current_tee_times)

    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")

    finally:
        if driver:
            print("[STEP] Closing browser...")
            driver.quit()

    return new_tee_times_list
