import time as sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import os
from datetime import date, timedelta
import tempfile
import shutil
import subprocess

CHROMEDRIVER_PATH = "/usr/bin/chromedriver"


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
    return target_date.strftime("%m%%2F%d%%2F%Y")


def get_target_filename(day_of_week, file_prefix="muni"):
    readable_date = get_target_date(day_of_week).replace("%2F", "-")
    return f"{file_prefix}_tee_times_{readable_date}.txt"


def read_saved_tee_times_with_slots(file_path):
    """Read saved tee times and return a dict mapping keys to max slot counts seen"""
    saved_data = {}
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            for line in file:
                line = line.strip()
                if line and ", Open Slots:" in line:
                    parts = line.split(", Open Slots: ")
                    if len(parts) == 2:
                        key = parts[0]
                        try:
                            slot_count = int(parts[1])
                            if key not in saved_data or slot_count > saved_data[key]:
                                saved_data[key] = slot_count
                        except ValueError:
                            if key not in saved_data:
                                saved_data[key] = 0
    return saved_data


def save_tee_times(file_path, tee_times):
    with open(file_path, "w") as file:
        for tee_time in tee_times:
            file.write(f"{tee_time}\n")


def aggressive_cleanup():
    """Aggressively clean up Chrome/Chromium temporary files and processes"""
    try:
        subprocess.run(['pkill', '-9', 'chrome'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-9', 'chromedriver'], stderr=subprocess.DEVNULL)
        sleep.sleep(1)
    except Exception:
        pass

    cleaned_count = 0
    for temp_dir in ['/tmp', '/var/tmp']:
        try:
            if not os.path.exists(temp_dir):
                continue
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                if any(x in item.lower() for x in ['chrome', 'tmp', 'scoped', '.org.chromium']):
                    try:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                            cleaned_count += 1
                        elif os.path.isfile(item_path):
                            os.remove(item_path)
                            cleaned_count += 1
                    except Exception:
                        pass
        except Exception:
            pass

    if cleaned_count > 0:
        print(f"[CLEANUP] Removed {cleaned_count} temp items")


def build_url(cityConfig, day_of_week):
    """Build the search URL from a city config dict."""
    return (
        f"https://{cityConfig['domain']}/webtrac/web/search.html?"
        f"Action=Start&SubAction=&_csrf_token={cityConfig['csrf_token']}"
        f"&numberofplayers={cityConfig['number_of_players']}"
        f"&secondarycode=&begindate={get_target_date(day_of_week)}"
        f"&begintime={cityConfig['begin_time']}"
        f"&numberofholes={cityConfig['number_of_holes']}"
        f"&display=Detail&module=GR&multiselectlist_value="
        f"&grwebsearch_buttonsearch=yes"
    )


def scrape_tee_times(day_of_week, cityConfig):
    """
    Scrape tee times for a given day using the provided city config.

    cityConfig should be a dict with keys:
        domain, csrf_token, number_of_players, begin_time,
        number_of_holes, file_prefix, name
    """
    aggressive_cleanup()

    city_name = cityConfig.get("name", "Unknown")
    file_prefix = cityConfig.get("file_prefix", "muni")

    url = build_url(cityConfig, day_of_week)
    print(f"[{city_name}] Navigating to: {url}")

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )

    local_temp_base = os.path.join(os.getcwd(), '.chrome_temps')
    os.makedirs(local_temp_base, exist_ok=True)

    tmp_profile = tempfile.mkdtemp(dir=local_temp_base)
    chrome_options.add_argument(f"--user-data-dir={tmp_profile}")
    chrome_options.add_argument(f"--crash-dumps-dir={tmp_profile}")

    service = Service(CHROMEDRIVER_PATH)
    driver = None
    new_tee_times_list = []

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print(f"[{city_name}] WebDriver started successfully")

        driver.set_page_load_timeout(30)
        driver.get(url)
        sleep.sleep(5)

        cart_buttons = driver.find_elements(By.CLASS_NAME, "button-cell--cart")
        print(f"[{city_name}] Found {len(cart_buttons)} tee time buttons on page")

        current_tee_times = []

        for button in cart_buttons:
            parent_row = button.find_element(By.XPATH, "ancestor::tr")
            time_val = parent_row.find_element(By.XPATH, ".//td[@data-title='Time']").text
            date_val = parent_row.find_element(By.XPATH, ".//td[@data-title='Date']").text
            holes = parent_row.find_element(By.XPATH, ".//td[@data-title='Holes']").text
            course = parent_row.find_element(By.XPATH, ".//td[@data-title='Course']").text
            open_slots = parent_row.find_element(By.XPATH, ".//td[@data-title='Open Slots']").text

            full_tee_time = f"Time: {time_val}, Date: {date_val}, Holes: {holes}, Course: {course}, Open Slots: {open_slots}"
            current_tee_times.append(full_tee_time)
            print(f"[{city_name}][FOUND] {full_tee_time}")

        file_path = get_target_filename(day_of_week, file_prefix)
        saved_tee_times_data = read_saved_tee_times_with_slots(file_path)
        print(f"[{city_name}] Loaded {len(saved_tee_times_data)} saved tee time keys from file")

        for tee_time in current_tee_times:
            if ", Open Slots: " in tee_time:
                parts = tee_time.split(", Open Slots: ")
                if len(parts) == 2:
                    tee_key = parts[0]
                    try:
                        current_slots = int(parts[1])
                        if tee_key not in saved_tee_times_data:
                            new_tee_times_list.append(tee_time)
                            print(f"[{city_name}][NEW TIME SLOT] {tee_time}")
                        elif current_slots > saved_tee_times_data[tee_key]:
                            new_tee_times_list.append(tee_time)
                            print(f"[{city_name}][MORE SLOTS] {tee_time} (was {saved_tee_times_data[tee_key]}, now {current_slots})")
                    except ValueError:
                        if tee_key not in saved_tee_times_data:
                            new_tee_times_list.append(tee_time)
                            print(f"[{city_name}][NEW TIME SLOT] {tee_time}")

        if new_tee_times_list:
            print(f"[{city_name}] Found {len(new_tee_times_list)} new/increased tee times!")
        else:
            print(f"[{city_name}] No new tee times or increased availability found.")

        save_tee_times(file_path, current_tee_times)

    except Exception as e:
        print(f"[{city_name}][ERROR] An error occurred: {e}")

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
            sleep.sleep(1)

        try:
            if os.path.exists(tmp_profile):
                shutil.rmtree(tmp_profile, ignore_errors=True)
                print(f"[{city_name}][CLEANUP] Removed temp profile: {tmp_profile}")
        except Exception:
            pass

        aggressive_cleanup()

    return new_tee_times_list