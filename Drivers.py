import sqlite3
from DataBase import create_Driver_table
from flask import request
from twilio.twiml.messaging_response import MessagingResponse
from createLinkToWase import get_waze_link
from WHAPI import send_message_to_whatsapp,send_Poll_message

Poll_Choices = {
    "pqFInAQgaE5habxcSZ6IPBU9RXvCrpLp9wM4JYAhJtI=": True,   # Approve (True)
    "9zaG33TkTJTO1BI2/mJAyEbyN2sBScZ9VxA77n5gNDI=": False  # Do not approve (False)
}

def insert_or_update_location(phone_number, latitude, longitude):
    create_Driver_table()  # Ensure the table is created before proceeding
    try:
        conn = sqlite3.connect('drivers.db')
        cursor = conn.cursor()

        # Check if the phone_number already exists in the database
        cursor.execute("SELECT * FROM drivers WHERE phone_number = ?", (phone_number,))
        if cursor.fetchone():
            # Update the existing record
            cursor.execute("UPDATE drivers SET latitude = ?, longitude = ? WHERE phone_number = ?",
                           (latitude, longitude, phone_number))
        else:
            # Insert a new record with debt set to 0
            cursor.execute("INSERT INTO drivers (phone_number, latitude, longitude, debt) VALUES (?, ?, ?, ?)",
                           (phone_number, latitude, longitude, 0))  # Debt is set to 0 for new entries
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        conn.close()

def WHAPI_Poll_reply(message):
    print("# Function that handles the /whatsapp route logic")
    print("Received message:", message)
    
    # Extracting votes from the message
    votes = message.get('action', {}).get('votes', [])
    if votes:
        print(f"Votes: {votes}")
    else:
        print("No votes found in the message.")
    
    # Extracting the sender's number
    from_number = message.get('from', None)
    if from_number:
        print(f"Message received from: {from_number}")
    else:
        print("Sender's number not found in the message.")

    Is_DreiverTookTheDrive = Poll_Choices.get( votes[0] , False)  # Safe access
    print(f"the driver dicide to {Is_DreiverTookTheDrive}")
    

    if Is_DreiverTookTheDrive:
        return True
    else:
        return False

def WHAPI_Location_reply(message):
    location = message["location"]
    latitude = location['latitude']
    longitude = location['longitude']

    from_number = message["from"]  # Extract 'from'
    from_name = message["from_name"]  # Extract 'from_name'
    print(f"Latitude: {latitude}, Longitude: {longitude}")
    print("From:", from_number)
    print("From Name:", from_name)
    
    
   
    send_message_to_whatsapp(from_number,"תודה ,כבר נשלח אליך את הלקוח הקרוב ביותר")
    
    # Convert latitude and longitude to float values
    latitude = float(latitude)
    longitude = float(longitude)

    # Insert or update the location in your database
    insert_or_update_location(from_number, latitude, longitude)
    print(f"The driver {from_number} sent location. It's saved in the database.")

def update_debt(phone_number, debt_change, debt_type):
    """
    Update the debt for a driver by phone number.

    Parameters:
        phone_number (str): The driver's phone number.
        debt_change : The amount to change the debt.
        debt_type (str): 'increase' to add to the debt, 'decrease' to deduct. Default is 'decrease'.
    """

    # Ensure the phone number starts with 972 if it starts with 0
    if str(phone_number).startswith("0"):
        phone_number = "972" + str(phone_number)[1:]

    # Connect to the database
    conn = sqlite3.connect('drivers.db')
    cursor = conn.cursor()

    # Check if the phone number exists in the database
    cursor.execute("SELECT debt FROM drivers WHERE phone_number = ?", (phone_number,))
    result = cursor.fetchone()

    if result:
        # Update debt based on debt_type
        current_debt = result[0]
        if debt_type == 'increase':
            new_debt = current_debt + debt_change
        elif debt_type == 'decrease':
            new_debt = current_debt - debt_change
        else:
            print("Error: Invalid debt_type. Use 'increase' or 'decrease'.")
            conn.close()
            return

        # Update the debt in the database
        cursor.execute("UPDATE drivers SET debt = ? WHERE phone_number = ?", (new_debt, phone_number))

        # Send WhatsApp message
        if new_debt > 0:
            message = f"תודה, היתרה שלך כרגע היא {new_debt} בחובה"
        elif new_debt == 0:
            message = f"תודה, היתרה שלך כרגע היא {new_debt}"
        else:
            message = f"תודה, היתרה שלך כרגע היא {-new_debt} בזכות"

        send_message_to_whatsapp(phone_number, message)
    else:
        print("Error: Phone number not found in the database.")

    # Commit changes and close the connection
    conn.commit()
    conn.close()

    
        
   
