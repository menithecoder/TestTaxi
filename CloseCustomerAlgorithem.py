import sqlite3
import math

# Haversine function to calculate distance
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth's radius in kilometers
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def find_sorted_drivers(customernumber):
    try:
        # Connect to the database
        conn = sqlite3.connect('test.db')
        cursor = conn.cursor()
        
        # Fetch the customer's latitude and longitude based on their number
        cursor.execute("SELECT latitude, longitude FROM customer_info WHERE phonenumber  = ?", (customernumber,))
        customer_location = cursor.fetchone()
        
        if not customer_location:
            raise ValueError(f"No customer found with number {customernumber}")
        
        customer_lat, customer_lon = customer_location
        print(customer_lat)
        conn.close()
        # Query only phone number, latitude, and longitude of drivers
        conn = sqlite3.connect('drivers.db')
        cursor = conn.cursor()
        cursor.execute("SELECT phone_number, latitude, longitude FROM drivers")
        drivers = cursor.fetchall()
        
        # Check if no drivers are found
        if not drivers:
            raise ValueError("No drivers available")
        
        # Calculate distances for all drivers
        driver_distances = []
        for driver in drivers:
            phone, lat, lon = driver
            print(f"find_sorted_drivers loop, phone: {phone}, lat: {lat}, lon: {lon}")
            try:
                distance = haversine(customer_lat, customer_lon, lat, lon)
                driver_distances.append((phone, distance))
            except Exception as e:
                print(f"Error calculating distance for driver {phone}: {e}")
        
        # Sort drivers by distance
        driver_distances.sort(key=lambda x: x[1])
        
        return driver_distances
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise
    except ValueError as e:
        print(f"Value error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise
    finally:
        # Close the database connection
        if 'conn' in locals() and conn:
            conn.close()
