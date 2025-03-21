import time as sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import os
from datetime import datetime, date, timedelta
import sys

def get_csrf_token():
    return "Xf0R600W0Q0E2D481X2O2O5D604X6D57066Z4U5E4C0N5N5W5C4E71564Z6T4Z065Y4L466C6D674S6M6H0T5G4C5I6M19724R553Y0264566O50046D5R4S6K1P5M625G"

# Function to generate the filename for today
def get_target_filename(day_of_week):
    target_date = get_target_date(day_of_week)  # Get the target date based on the day_of_week
    # Modify this line to create a more human-readable format, e.g., "01-09-2025"
    readable_date = target_date.replace("%2F", "-")  # Replace '%2F' with '-'
    return f"muni_tee_times_{readable_date}.txt"  # Return the filename using the target date

# Function to read previously saved tee times for today
def read_saved_tee_times(file_path):
    saved_times = set()  # Use a set for easy comparison
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            for line in file:
                saved_times.add(line.strip())  # Remove any extra spaces or newlines
    return saved_times

# Function to save the current tee times to the file for today
def save_tee_times(file_path, tee_times):
    with open(file_path, "w") as file:
        for time in tee_times:
            file.write(f"{time}\n")

# Function to calculate the next or previous date of a given day of the week
def get_target_date(day_of_week):
    today = date.today()

    day_of_week_map = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6
    }

    target_day = day_of_week_map.get(day_of_week, None)

    if target_day is None:
        raise ValueError("Invalid day of the week")

    today_weekday = today.weekday()

    # If the target day is today or in the future, calculate the next occurrence
    if target_day >= today_weekday:
        days_ahead = target_day - today_weekday
    else:
        # If the target day is in the past this week, get the target day next week
        days_ahead = 7 - (today_weekday - target_day)

    target_date = today + timedelta(days=days_ahead)

    # Return the target date in the format required for the URL (mm%2Fdd%2Fyyyy)
    return target_date.strftime("%m%%2F%d%%2F%Y")

def extract_time_from_tee_time(tee_time):
    time_str = tee_time.split(",")[0]  # Get the part before the first comma
    time_value = time_str.replace("Time: ", "").strip()  # Remove "Time: " and surrounding spaces
    return time_value

def extract_date_from_tee_time(tee_time):
    date_str = tee_time.split(",")[1]  # Get the part after the time
    date_value = date_str.replace("Date: ", "").strip()  # Remove "Date: " and surrounding spaces
    return date_value

def extract_open_slots_from_tee_time(tee_time):
    open_slots_str = tee_time.split(",")[-1]  # Get the part after the last comma
    open_slots_value = open_slots_str.replace("Open Slots: ", "").strip()  # Remove "Open Slots: " and any surrounding spaces
    return int(open_slots_value)  # Convert to integer for easy comparison

# Hardcoded values for the query parameters
NUMBER_OF_PLAYERS = 1
BEGIN_TIME = "+7%3A00AM"
NUMBER_OF_HOLES = 18
CSRF_TOKEN = "Xf0R600W0Q0E2D481X2O2O5D604X6D57066Z4U5E4C0N5N5W5C4E71564Z6T4Z065Y4L466C6D674S6M6H0T5G4C5I6M19724R553Y0264566O50046D5R4S6K1P5M625G"

def scrape_tee_times(dayOfWeek):
    BEGIN_DATE = get_target_date(dayOfWeek)

    url = f"https://sccharlestonweb.myvscloud.com/webtrac/web/search.html?Action=Start&SubAction=&_csrf_token={CSRF_TOKEN}&numberofplayers={NUMBER_OF_PLAYERS}&secondarycode=&begindate={BEGIN_DATE}&begintime={BEGIN_TIME}&numberofholes={NUMBER_OF_HOLES}&display=Detail&module=GR&multiselectlist_value=&grwebsearch_buttonsearch=yes"

    # Set up options for Chromium
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU for better performance on Pi
    chrome_options.add_argument("--no-sandbox")  # This might help in some environments

    # Path to the ChromeDriver
    chromedriver_path = "/usr/bin/chromedriver"  # Default path for chromedriver on your system

    # Set up the ChromeDriver service
    service = Service(chromedriver_path)

    driver = None  # Initialize driver to None before the try-except block

    new_tee_times_list = []  # Initialize the list to store new tee times

    try:
        print("this our guy", service)
        # Initialize the Chromium WebDriver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("driver has been set")
        # Open the URL
        driver.get(url)
        sleep.sleep(5)

        file_path = get_target_filename(dayOfWeek)

        # Check if the file already exists
        if os.path.exists(file_path):
            print(f"File {file_path} already exists. Checking for new times...")

            # Find all button-cell button-cell--cart elements
            cart_buttons = driver.find_elements(By.CLASS_NAME, "button-cell--cart")
            current_tee_times = []

            for button in cart_buttons:
                # Find the sibling elements for time, date, holes, course, and open slots
                parent_row = button.find_element(By.XPATH, "ancestor::tr")  # The row <tr> containing the data

                time = parent_row.find_element(By.XPATH, ".//td[@data-title='Time']").text
                date = parent_row.find_element(By.XPATH, ".//td[@data-title='Date']").text
                holes = parent_row.find_element(By.XPATH, ".//td[@data-title='Holes']").text
                course = parent_row.find_element(By.XPATH, ".//td[@data-title='Course']").text
                open_slots = parent_row.find_element(By.XPATH, ".//td[@data-title='Open Slots']").text

                # Format the tee time data as a string (you can adjust this format)
                tee_time = f"Time: {time}, Date: {date}, Holes: {holes}, Course: {course}, Open Slots: {open_slots}"
                current_tee_times.append(tee_time)

            # Read the previously saved tee times (using the correct file for the target date)
            saved_tee_times = read_saved_tee_times(file_path)

            # Create a set to store saved tee times (only store the time part)
            saved_tee_times_set = {extract_time_from_tee_time(tee_time) for tee_time in saved_tee_times}

            # Find new tee times based on the logic:
            # 1. If the time is new (not in saved times)
            # 2. Or if the open slots have increased (current_open_slots > saved_open_slots)
            # 3. Ensure the tee time is not in the past
            new_tee_times = []

            for current_tee_time in current_tee_times:
                current_time = extract_time_from_tee_time(current_tee_time)
                current_date = extract_date_from_tee_time(current_tee_time)
                current_open_slots = extract_open_slots_from_tee_time(current_tee_time)

                # Combine date and time into a datetime object
                current_datetime = datetime.strptime(f"{current_date} {current_time}", "%m/%d/%Y %I:%M %p")

                # Skip times in the past
                if current_datetime < datetime.now():
                    continue

                # Check if the time exists in the saved times
                if current_time not in saved_tee_times_set:
                    # If the tee time doesn't exist, it's a new time
                    new_tee_times.append(current_tee_time)
                else:
                    # If the tee time exists, check if the open slots have changed
                    saved_tee_time = next(time for time in saved_tee_times if extract_time_from_tee_time(time) == current_time)
                    saved_open_slots = extract_open_slots_from_tee_time(saved_tee_time)

                    # If the current open slots are greater than saved open slots, it's a new tee time
                    if current_open_slots > saved_open_slots:
                        new_tee_times.append(current_tee_time)  # Add to new tee times list

            if new_tee_times:
                # Log the new tee times
                for new_time in new_tee_times:
                    new_tee_times_list.append(new_time)  # Store the new times in the list

                # Save the new tee times to the file for the target date
                save_tee_times(file_path, current_tee_times)
            else:
                # If no new times, just update the file with the current tee times
                save_tee_times(file_path, current_tee_times)

        else:
            # File does not exist, create the file without marking any tee times as new
            print(f"File {file_path} does not exist. Creating the file...")

            # Find all button-cell button-cell--cart elements
            cart_buttons = driver.find_elements(By.CLASS_NAME, "button-cell--cart")

            current_tee_times = []

            for button in cart_buttons:
                # Find the sibling elements for time, date, holes, course, and open slots
                parent_row = button.find_element(By.XPATH, "ancestor::tr")  # The row <tr> containing the data

                time = parent_row.find_element(By.XPATH, ".//td[@data-title='Time']").text
                date = parent_row.find_element(By.XPATH, ".//td[@data-title='Date']").text
                holes = parent_row.find_element(By.XPATH, ".//td[@data-title='Holes']").text
                course = parent_row.find_element(By.XPATH, ".//td[@data-title='Course']").text
                open_slots = parent_row.find_element(By.XPATH, ".//td[@data-title='Open Slots']").text

                # Format the tee time data as a string (you can adjust this format)
                tee_time = f"Time: {time}, Date: {date}, Holes: {holes}, Course: {course}, Open Slots: {open_slots}"
                current_tee_times.append(tee_time)

            # Save the current tee times to the file (do not mark them as new)
            save_tee_times(file_path, current_tee_times)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if driver:
            driver.quit()

    return new_tee_times_list
