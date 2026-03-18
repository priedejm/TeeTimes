import os
import datetime
import muniScraper
from helpers import send_to_discord
from cityConfig import CITY_CONFIGS


def print_current_time():
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Script started at: {current_time}")


def delete_past_files():
    """Delete cache files with dates in the past. Handles both old and new prefixed filenames."""
    today = datetime.date.today()
    files = os.listdir()
    for file in files:
        if file.endswith(".txt") and "_tee_times_" in file:
            try:
                # Extract the date part after the last "tee_times_" segment
                date_str = file.split("_tee_times_")[-1].replace(".txt", "")
                file_date = datetime.datetime.strptime(date_str, "%m-%d-%Y").date()

                if file_date < today:
                    os.remove(file)
                    print(f"Deleted past file: {file}")
            except Exception as e:
                print(f"Error processing file {file}: {e}")


print_current_time()
delete_past_files()

# ── Run scraper for each city ──────────────────────────────────────────────
for city_key, config in CITY_CONFIGS.items():
    city_name = config["name"]
    print(f"\n{'='*50}")
    print(f"  Scraping: {city_name}")
    print(f"{'='*50}")

    try:
        combined_new_times = []
        for day in config["scrape_days"]:
            new_times = muniScraper.scrape_tee_times(day, config)
            combined_new_times.extend(new_times)

        if combined_new_times:
            print(f"\n[{city_name}] {len(combined_new_times)} new tee times collected — sending to Discord")
            send_to_discord(config["discord_webhook"], combined_new_times, cityConfig=config)
            for t in combined_new_times:
                print(t)
        else:
            print(f"[{city_name}] No new tee times found.")

    except Exception as e:
        print(f"[{city_name}] An error occurred: {e}")