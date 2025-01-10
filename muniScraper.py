from selenium import webdriver
from selenium.webdriver.firefox.service import Service

options = webdriver.FirefoxOptions()
options.add_argument("--headless")

# Specify the geckodriver path explicitly
geckodriver_path = "/usr/local/bin/geckodriver"  # Replace with your geckodriver path
service = Service(geckodriver_path)

# Use the service to initialize Firefox driver
driver = webdriver.Firefox(service=service, options=options)

driver.get("https://www.example.com")
print(driver.title)

driver.quit()
