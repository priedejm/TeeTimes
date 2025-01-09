import requests
import logging
from datetime import datetime

# Function to read and update the counter stored in a file
def update_counter(file_path="muniCount.txt"):
    try:
        # Open the file to read the current count
        with open(file_path, 'r') as file:
            counter = int(file.read())  # Read the current counter value
    except FileNotFoundError:
        # If file doesn't exist, start the counter at 1
        counter = 1

    # Increment the counter by 1
    counter += 1
    
    # Write the updated counter back to the file
    with open(file_path, 'w') as file:
        file.write(str(counter))
    
    return counter

def send_to_discord(webhook_url, message):
    # Count the number of cancelled tee times
    cancelled_count = len(message)
    
    # Check if the message is a list and format each item accordingly
    formatted_messages = []
    
    for item in message:
        try:
            # Split the message into individual components (time, date, holes, course, and open slots)
            parts = item.split(", ")
            time = parts[0].replace("Time: ", "")
            date = parts[1].replace("Date: ", "")
            holes = parts[2].replace("Holes: ", "")
            course = parts[3].replace("Course: ", "")
            open_slots = parts[4].replace("Open Slots: ", "")
            
            # Parse the date to find the day of the week
            date_obj = datetime.strptime(date, "%m/%d/%Y")  # Assuming date is in MM/DD/YYYY format
            day_of_week = date_obj.strftime("%A")  # Full weekday name (e.g., "Monday")
            
            # Manually format the date to remove leading zero for month and day
            formatted_month = str(date_obj.month).lstrip('0')
            formatted_day = str(date_obj.day).lstrip('0')
            formatted_date = f"{formatted_month}/{formatted_day}"
            
            # Format the message (Slots before Holes)
            formatted_message = f"**Cancelled Time at the Muni!**```Date: {formatted_date} - {day_of_week}``````Time: {time}``````Slots: {open_slots}``````Holes: {holes}```"
            formatted_messages.append(formatted_message)

        except Exception as e:
            logging.error(f"Error formatting message: {item}. Error: {e}")
    
    # Ensure there's at least one formatted message to send
    if not formatted_messages:
        logging.error("No valid messages to send!")
        return
    
    # Join all formatted messages with a new line to send them as a single payload
    final_message = '\n'.join(formatted_messages)
    
    # Get the updated counter value and append it to the username
    counter = update_counter()
    username = f"Muni - {cancelled_count} Tee Time(s) cancelled #{counter}"
    
    # Prepare the final message for Discord
    full_message = f"\n{final_message}"
    
    chat_message = {
        "username": username,
        "avatar": "https://i.imgur.com/kfjHRvR.jpeg",
        "content": full_message
    }

    try:
        # Send the POST request to the Discord webhook URL
        response = requests.post(webhook_url, json=chat_message)
        
        if response.status_code == 204:
            logging.info("Message sent successfully!")
        else:
            logging.error(f"Failed to send message. Status code: {response.status_code}")
            logging.error(f"Response text: {response.text}")
    
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred: {str(e)}")
