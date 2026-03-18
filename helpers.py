import requests
import logging
from datetime import datetime


def update_counter(file_path="muniCount.txt"):
    try:
        with open(file_path, 'r') as file:
            counter = int(file.read())
    except FileNotFoundError:
        counter = 1

    counter += 1

    with open(file_path, 'w') as file:
        file.write(str(counter))

    return counter


def send_to_discord(webhook_url, message, cityConfig=None):
    """
    Send tee time alerts to Discord.

    If cityConfig is provided, uses city-specific counter file and bot name.
    Falls back to legacy defaults if cityConfig is None (backward compatible).
    """
    bot_name = cityConfig.get("bot_name", "Muni") if cityConfig else "Muni"
    counter_file = cityConfig.get("counter_file", "muniCount.txt") if cityConfig else "muniCount.txt"
    avatar_url = cityConfig.get("avatar_url", "https://i.imgur.com/kfjHRvR.jpeg") if cityConfig else "https://i.imgur.com/kfjHRvR.jpeg"

    cancelled_count = len(message)

    formatted_messages = []

    for item in message:
        try:
            parts = item.split(", ")
            time = parts[0].replace("Time: ", "")
            date = parts[1].replace("Date: ", "")
            holes = parts[2].replace("Holes: ", "")
            course = parts[3].replace("Course: ", "")
            open_slots = parts[4].replace("Open Slots: ", "")

            date_obj = datetime.strptime(date, "%m/%d/%Y")
            day_of_week = date_obj.strftime("%A")

            formatted_month = str(date_obj.month).lstrip('0')
            formatted_day = str(date_obj.day).lstrip('0')
            formatted_date = f"{formatted_month}/{formatted_day}"

            formatted_message = f"**Cancelled Time at the Muni!**```Date: {formatted_date} - {day_of_week}``````Time: {time}``````Slots: {open_slots}``````Holes: {holes}```"
            formatted_messages.append(formatted_message)
        except Exception as e:
            logging.error(f"Error formatting message: {item}. Error: {e}")

    if not formatted_messages:
        logging.error("No valid messages to send!")
        return

    final_message = '\n'.join(formatted_messages)

    counter = update_counter(counter_file)
    username = f"{bot_name} - {cancelled_count} Tee Time(s) cancelled #{counter}"

    full_message = f"\n{final_message}"

    chat_message = {
        "username": username,
        "avatar": avatar_url,
        "content": full_message
    }
    try:
        response = requests.post(webhook_url, json=chat_message)

        if response.status_code == 204:
            logging.info(f"[{bot_name}] Message sent successfully!")
        else:
            logging.error(f"[{bot_name}] Failed to send message. Status code: {response.status_code}")
            logging.error(f"Response text: {response.text}")

    except requests.exceptions.RequestException as e:
        logging.error(f"[{bot_name}] An error occurred: {str(e)}")