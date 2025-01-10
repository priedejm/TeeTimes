from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Set up options for Chromium
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")  # Disable GPU for better performance on Pi
chrome_options.add_argument("--no-sandbox")  # This might help in some environments

# Path to the ChromeDriver (use the path found with 'which chromedriver')
chromedriver_path = "/usr/bin/chromedriver"  # Default path for chromedriver on your system

# Set up the ChromeDriver service
service = Service(chromedriver_path)

try:
    # Initialize the Chromium WebDriver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Open a website (for example, www.google.com)
    driver.get("https://www.google.com")
    
    # Print the page title to confirm that it's working
    print(driver.title)
    
except Exception as e:
    print(f"Error occurred: {e}")
finally:
    driver.quit()
