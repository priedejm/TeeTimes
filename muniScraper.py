from selenium import webdriver

options = webdriver.FirefoxOptions()
options.add_argument("--headless")  # Run Firefox in headless mode

# Create the WebDriver instance with options
driver = webdriver.Firefox(options=options)

# Open a test page
driver.get("https://www.google.com")

# Print the title of the page
print(driver.title)

# Quit the driver
driver.quit()
