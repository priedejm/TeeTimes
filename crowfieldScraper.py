# crowfieldScraper.py
import time as sleep
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import os

# Function to get the current CSRF token (if necessary)
def get_csrf_token():
    # For the purpose of this example, we'll assume no CSRF token is needed
    return ""

# Function to read previously saved tee times from the file
def read_saved_tee_times(file_path):
    saved_times = set()  # Use a set for easy comparison
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            for line in file:
                saved_times.add(line.strip())  # Remove any extra spaces or newlines
    return saved_times

# Function to save current tee times to a file
def save_tee_times(file_path, tee_times):
    with open(file_path, "w") as file:
        for time in tee_times:
            file.write(f"{time}\n")

# Function to scrape the tee times
def scrape_tee_times():
    # Base URL and query parameters
    base_url = "https://crowfieldgc.cps.golf/onlineresweb/search-teetime"
    TeeOffTimeMin = 0
    TeeOffTimeMax = 23.999722222222225
    url = f"{base_url}?TeeOffTimeMin={TeeOffTimeMin}&TeeOffTimeMax={TeeOffTimeMax}"

    # Set up undetected-chromedriver options
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")  # Maximize the window
    options.add_argument("--disable-extensions")  # Disable extensions
    # options.add_argument("--headless")  # If you need headless mode, enable this line
    options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration

    # Initialize the undetected ChromeDriver
    driver = uc.Chrome(options=options)

    # Open the URL
    driver.get(url)

    # Allow some time for the page to load
    sleep.sleep(5000)
    
    # Path to store the saved tee times
    file_path = "crowfield_tee_times.txt"

    # List to store new tee times
    new_tee_times_list = []

    # Find the tee times from the page
    tee_times_elements = driver.find_elements(By.CLASS_NAME, "available-tee-time")  # Modify this as needed based on the page's HTML structure

    # Extract the current tee times
    current_tee_times = []

    for element in tee_times_elements:
        # Extract time, date, and other relevant info (adjust XPATH/CLASS based on actual page)
        time = element.find_element(By.XPATH, ".//span[@class='tee-time']").text
        date = element.find_element(By.XPATH, ".//span[@class='date']").text
        course = element.find_element(By.XPATH, ".//span[@class='course']").text
        open_slots = element.find_element(By.XPATH, ".//span[@class='open-slots']").text

        # Format the tee time data as a string (you can adjust this format)
        tee_time = f"Time: {time}, Date: {date}, Course: {course}, Open Slots: {open_slots}"
        current_tee_times.append(tee_time)

    # Read the previously saved tee times
    saved_tee_times = read_saved_tee_times(file_path)

    # Find new tee times
    new_tee_times = [time for time in current_tee_times if time not in saved_tee_times]

    if new_tee_times:
        # Log the new tee times
        for new_time in new_tee_times:
            print(new_time)
            new_tee_times_list.append(new_time)  # Store the new times in the list
        
        # Save the new tee times to the file
        save_tee_times(file_path, current_tee_times)
    else:
        print("No new times found.")

    # Close the driver
    driver.quit()

    # Return the list of new tee times
    return new_tee_times_list
