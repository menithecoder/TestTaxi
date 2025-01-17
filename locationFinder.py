import os
import requests
import time
import threading
from DataBase import printDataBase
import sqlite3
from createLinkToWase import get_waze_link

# Set your API key here
API_KEY =  os.getenv('GOOGLE_API_KEY')


address_cache = {}
cache_lock = threading.Lock()  # Lock to ensure thread safety

# Function to get latitude and longitude using Google Maps Geocoding API
def get_lat_lng(city, street, number, api_key):
    location = f"{number} {street}, {city}, Israel"
    
    # Check if the address is already in the cache
    with cache_lock:  # Ensure only one thread accesses the cache at a time
        if location in address_cache:
            print(f"Using cached coordinates for {location}")
            return address_cache[location]
         
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": location,
        "key": api_key
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data['status'] == 'OK':
        results = data['results'][0]
        lat = results['geometry']['location']['lat']
        lng = results['geometry']['location']['lng']

        with cache_lock:  # Ensure thread safety while updating the cache
            address_cache[location] = (lat, lng)
        
        
        return lat, lng
    else:
        print("Geocoding failed:", data['status'], "| Error Message:", data.get('error_message'))
        return None

# Function to update latitude and longitude for a given customer based on phone number
def update_location(phone_number, latitude, longitude):
    waze_link = get_waze_link(latitude, longitude)  # Generate the Waze link
    
    try:
        # Create a new SQLite connection
        connection = sqlite3.connect('test.db')
        cursor = connection.cursor()

        # Update latitude, longitude, and Waze link for the specific phone number
        cursor.execute('''
            UPDATE customer_info
            SET latitude = ?, longitude = ?, linkToWaze = ?
            WHERE phonenumber = ?
        ''', (latitude, longitude, waze_link, phone_number))

        # Commit the transaction
        connection.commit()
        connection.close()
        print(f"Updated location for phone number {phone_number}: Latitude={latitude}, Longitude={longitude}, Link={waze_link}")
    except sqlite3.DatabaseError as e:
        print(f"Error updating location: {e}")

# Function to fetch customer info from database and get coordinates
def process_customer_data(rows):
    
    # Iterate through each customer and convert address to coordinates
    for row in rows:
        city = row[0]
        street = row[1]
        house_number = row[2]
        if row[4] != 0.0 and row[5] != 0.0:
            continue
        # Call the function to get latitude and longitude
        coordinates = get_lat_lng(city, street, house_number,API_KEY )
        if coordinates:
            # Update the location in the database
            update_location(row[3], coordinates[0], coordinates[1])
    
            print(f"Customer {city}, {street} {house_number}: Latitude: {coordinates[0]}, Longitude: {coordinates[1]}")
        else:
            print(f"Failed to get coordinates for {city}, {street} {house_number}")

    
    
def get_data_from_db():
    try:
        # Create a new SQLite connection in this thread
        conn = sqlite3.connect('test.db')
        cursor = conn.cursor()

        # Query to fetch city, street, and house number from customer_info table
        query = "SELECT cityLocation, street, houseNumber,phonenumber,latitude,longitude FROM customer_info"
        cursor.execute(query)

        # Fetch the data
        rows = cursor.fetchall()

        # Close the connection
        conn.close()

        return rows

    except sqlite3.DatabaseError as db_error:
        # Handle any database-related errors
        print(f"Database error occurred: {db_error}")
        return None

    except sqlite3.OperationalError as op_error:
        # Handle errors such as missing database file
        print(f"Operational error occurred: {op_error}")
        return None

    except Exception as e:
        # Handle any other unexpected errors
        print(f"An error occurred: {e}")
        return None
    
def convert_to_coordinates():
    
   
    last_processed = None

    
    # Check if the file exists
    if os.path.exists('test.db'):
        print("file are in teh system")
        # Get data from database
        rows = get_data_from_db()
    
        if rows != last_processed:  # Check if data has changed
            print("Database has changed, processing new data...")
            process_customer_data(rows)
            last_processed = rows
    
        # Sleep for some time before checking again (e.g., 5 seconds)
        time.sleep(10)
    else:
        print("The file 'text.db' does not exist.")
        time.sleep(100)
    #call the function to print the database
    printDataBase()
         

if __name__ == "__main__":
    fetch_customer_info_and_convert_to_coordinates()
