import sqlite3
import threading
import time
from CloseCustomerAlgorithem import find_sorted_drivers
from WHAPI import send_message_to_whatsapp
from Drivers import update_debt
poll_states = {}
poll_states_lock = threading.Lock()

def get_customer_info(phone_number):
    print(f"Attempting to retrieve customer info for phone number: {phone_number}")
    
    # Connect to the database
    connection = sqlite3.connect("test.db")
    print("Connected to the database successfully.")
    
    cursor = connection.cursor()
    print("Cursor created.")
    
    # Query to retrieve the required customer information
    query = '''
        SELECT phonenumber, destination, cityLocation, street, houseNumber, linkToWaze,price
        FROM customer_info
        WHERE phonenumber = ?;
    '''
    print(f"Executing query: {query}")
    cursor.execute(query, (phone_number,))
    
    # Fetch the result
    result = cursor.fetchone()
    print(f"Query result: {result}")
    
    # Close the connection
    connection.close()
    print("Database connection closed.")
    
    # If no result is found, return None
    if not result:
        print("No customer info found for the given phone number.")
        return None

    # Extract information from the query result
    phonenumber, destination, cityLocation, street, houseNumber, link_to_waze,price = result
    print(f"Extracted info - Phone Number: {phonenumber}, Destination: {destination}, Link to Waze: {link_to_waze}")
    
    # Return the desired information
    return {
        "phone_number": phonenumber,
        "destination": destination,
        "city_location": cityLocation,
        "street": street,
        "house_number": houseNumber,
        "link_to_waze": link_to_waze,
	"price":price    
    }

def send_customer_info(CustomerPhoneNumber, DriverNumber):
    # Retrieve customer information
    customer_info = get_customer_info(CustomerPhoneNumber)
    if not customer_info:
        print("Customer not found.")
        return

    # Construct the message
    message = (
        f"מספר של הלקוח: {customer_info['phone_number']}\n\n"
        f"הלקוח רוצה לנסוע ל : {customer_info['destination']}\n\n"
        f"כתובת של הלקוח: {customer_info['city_location']} {customer_info['street']} {customer_info['house_number']}\n\n"
        f"לינק לוויז : {customer_info['link_to_waze']}\n"
	f"מחיר הנסיעה :{customer_info['price']}"    
    )

    send_message_to_whatsapp(DriverNumber, f"העמלה שתיגבה: {customer_info['price']/10}")
    update_debt(DriverNumber, int(customer_info['price'] / 10), 'increase')

    print(message)

    
    send_message_to_whatsapp(DriverNumber, message)
	
def poll_customer_drivers(customernumber):
    global poll_states

    try:
        # Lock to avoid race conditions on shared poll_states
        with poll_states_lock:
            # Find sorted drivers for the given customer
            sorted_drivers = find_sorted_drivers(customernumber)

            # If no drivers are available, initialize customer in poll_states
            if not sorted_drivers:
                print(f"No drivers available for customer {customernumber}.")
                if customernumber not in poll_states:
                    poll_states[customernumber] = {
                        "current_driver": None,
                        "response_received": False,
                        "completed": False
                    }
                poll_states[customernumber]["completed"] = False
                return

            # If customer not in poll_states, initialize customer data
            elif customernumber not in poll_states:
                poll_states[customernumber] = {
                    "current_driver": None,
                    "response_received": False,
                    "completed": False,
                }
                print(f"Customer {customernumber} added to poll_states with drivers: {sorted_drivers}")

            # Iterate through sorted drivers to send polls
            for driver in sorted_drivers:
                phone_number = driver[0]
                poll_states[customernumber]["current_driver"] = phone_number
                poll_states[customernumber]["response_received"] = False

                # Send the poll message using the WHAPI send_Poll_message function
                from WHAPI import send_Poll_message
                send_Poll_message(phone_number, customernumber, driver[1])

                # Wait for a response with a timeout of 30 seconds
                start_time = time.time()
                while time.time() - start_time < 30:
                    if poll_states[customernumber]["response_received"]:
                        DriverAfterAprovePoll(customernumber,phone_number)
			
                        delete_customer_info(customernumber)
                        poll_states[customernumber]["completed"] = True
                        del poll_states[customernumber]  # Remove customer from poll_states after completion
                        return
                    time.sleep(0.1)

                print(f"Customer {customernumber}: Driver {phone_number} did not respond in time or did not approve. Moving to next driver.")

            # If no drivers responded with approval, log that result
            print(f"Customer {customernumber}: No drivers responded with approval.")

    except Exception as e:
        print(f"Error polling for customer {customernumber}: {e}")
def DriverAfterAprovePoll(customerNumber, DriverNumber):
    print(f"Sending information: Customer {customerNumber}, Driver {DriverNumber}")
    send_customer_info(customerNumber, DriverNumber)  
def delete_customer_info(phone_number):
    print(f"Attempting to delete customer info for phone number: {phone_number}")
    
    # Connect to the database
    connection = sqlite3.connect("test.db")
    print("Connected to the database successfully.")
    
    cursor = connection.cursor()
    print("Cursor created.")
    
    # Query to delete the customer info with the matching phone number
    query = '''
        DELETE FROM customer_info
        WHERE phonenumber = ?;
    '''
    print(f"Executing query: {query}")
    
    # Execute the delete query
    cursor.execute(query, (phone_number,))
    
    # Commit the changes to the database
    connection.commit()
    print("Customer info deleted successfully.")
    
    # Check if any rows were deleted
    if cursor.rowcount == 0:
        print("No customer info found for the given phone number.")
    else:
        print(f"{cursor.rowcount} row(s) deleted.")
    
    # Close the connection
    connection.close()
    print("Database connection closed.")	
