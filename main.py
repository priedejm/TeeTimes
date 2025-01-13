import os
import datetime
import muniScraper
from helpers import send_to_discord

# Function to print the current time to the console
def print_current_time():
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Script started at: {current_time}")

# Function to delete files with dates in the past
def delete_past_files():
    today = datetime.date.today()
    files = os.listdir() 
    for file in files:
        if file.endswith(".txt"):
            # Extract the date from the filename (format: muni_tee_times_yyyy-mm-dd.txt)
            try:
                filename_parts = file.split('_')
                date_str = filename_parts[-1].replace(".txt", "") # Get the date part from the filename
                file_date = datetime.datetime.strptime(date_str, "%m-%d-%Y").date() # Convert to date object
                
                # If the file date is in the past, delete it
                if file_date < today:
                    os.remove(file) # Delete the file
                    print(f"Deleted past file: {file}")
            except Exception as e:
                print(f"Error processing file {file}: {e}")

# Print the current time at the beginning of the script
print_current_time()
# Run the function to delete past files
delete_past_files()

DISCORD_URL = "https://discord.com/api/webhooks/1326397023171252255/dV5__1t-tiXcqnkGzNTayMFejrOAqwpPbP-L3_K9ulExLBfuKzAjr2eocLxJayVtXIRA"

new_times_friday = muniScraper.scrape_tee_times("Friday")
new_times_saturday = muniScraper.scrape_tee_times("Saturday")
new_times_sunday = muniScraper.scrape_tee_times("Sunday")

combined_new_times = new_times_friday + new_times_saturday + new_times_sunday

# Process the combined times and send to Discord
if combined_new_times:
    print("\nAll new tee times collected:")
    send_to_discord(DISCORD_URL, combined_new_times)
    for time in combined_new_times:
        print(time)
else:
    print("No new tee times found.")
