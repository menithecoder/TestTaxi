import sqlite3


def create_Driver_table():
    conn = sqlite3.connect('drivers.db')
    cursor = conn.cursor()

    # Create the table if it doesn't exist already
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            number INTEGER PRIMARY KEY,
            phone_number INTEGER ,
            latitude REAL,
            longitude REAL,
            debt INTEGER
        )
    ''')
    
def store_user_data(phone_number, city, street, houseNumber, destination, latitude=0.0, longitude=0.0, waiting=0, price=0):
    connection = sqlite3.connect("test.db")
    cursor = connection.cursor()

    # Create table if it doesn't exist (added latitude, longitude, linkToWaze, and price columns)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer_info (
            number INTEGER PRIMARY KEY,
            phonenumber TEXT,  -- Store phone number as INTEGER
            cityLocation TEXT,
            street TEXT,
            houseNumber INTEGER,
            destination TEXT,
            latitude REAL,
            longitude REAL,
            linkToWaze TEXT,
            waiting INTEGER,
            price REAL
        );
    ''')

    # Insert the captured data into the table, including an empty link for Waze and price
    cursor.execute('''
        INSERT INTO customer_info (phonenumber, cityLocation, street, houseNumber, destination, latitude, longitude, linkToWaze, waiting, price)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (phone_number, city, street, houseNumber, destination, latitude, longitude, "", waiting, price))

    # Commit the transaction and close the connection
    connection.commit()
    connection.close()

    
#retrieve the data from the database
def retrieve_data():
    # Connect to the SQLite database
    connection = sqlite3.connect("test.db")
    cursor = connection.cursor()

    # Retrieve all rows from the customer_info table
    cursor.execute('SELECT * FROM customer_info')
    data = cursor.fetchall()

    # Close the database connection
    connection.close()

    # Return the retrieved data
    return data
#print database 
def printDataBase():
    print("\nStored Customer Data:")
    customer_data = retrieve_data()

    for row in customer_data:
        print(row)
def get_price_from_db(db_path, current_place, destination):
  
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Define the SQL query
        query = """
        SELECT Price
        FROM Pricing
        WHERE Current_Place = ? AND Destination = ?
        """

        # Execute the query with parameters
        cursor.execute(query, (current_place, destination))
        result = cursor.fetchone()

        # Close the connection
        conn.close()

        # Return the result if found
        if result:
            return int(result[0])  # Extract the price from the result tuple
        else:
            return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None

