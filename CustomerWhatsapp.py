
customer_data = {}

@app.route('/whatsapp', methods=['POST'])
def whatsapp():
    data = request.get_json(force=True, silent=True)

    if not data or "messages" not in data:
        return jsonify({"error": "Invalid or no JSON data received"}), 400

    # Extract sender and message
    message = data["messages"][0]
    sender = message.get('from', None)  # Safely get the sender's ID

    if not sender:
        return jsonify({"error": "Sender ID not found in message"}), 400

    # Initialize customer data if not present
    if sender not in customer_data:
        customer_data[sender] = {"state": "awaiting_current_location", "current": None, "destination": None}

    # Handle location messages
    if "location" in message:
        latitude = message["location"]["latitude"]
        longitude = message["location"]["longitude"]

        if customer_data[sender]["state"] == "awaiting_current_location":
            # Store current location
            customer_data[sender]["current"] = (latitude, longitude)
            customer_data[sender]["state"] = "awaiting_destination"
            send_message_to_whatsapp(sender, "תודה ,עכשיו כנס למיקום  ותשלח את היעד ")
            return jsonify({"status": "waiting_for_destination"})

        elif customer_data[sender]["state"] == "awaiting_destination":
            # Store destination
            customer_data[sender]["destination"] = (latitude, longitude)
            customer_data[sender]["state"] = "completed"
            current = customer_data[sender]["current"]
            destination = customer_data[sender]["destination"]
            response_message = f"מעולה הבקשה שלך התקבלה Current location: {current}, Destination: {destination}."
            send_message_to_whatsapp(sender, response_message)
            return jsonify({"status": "journey_completed"})

    # Default response for non-location messages
    send_message_to_whatsapp(sender, " היי לקוח יקר ,בבקשה תשלח מיקום דרך הוואטסאפ כאן למטה (לחץ על הסיכת ביטחון לאחר מכן על מיקום ושלח) ")
    return jsonify({
        "status": "awaiting_location"
    })

def WHAPI_Location_reply(message):
    location = message["location"]
    latitude = location['latitude']
    longitude = location['longitude']

    from_number = message["from"]  # Extract 'from'
    from_name = message["from_name"]  # Extract 'from_name'
    print(f"Latitude: {latitude}, Longitude: {longitude}")
    print("From:", from_number)
    print("From Name:", from_name)
    
    
   
    send_message_to_whatsapp(from_number,"מצוין ,בבקשה תשלחו מיקום של היעד אליו תרצו לנסוע ")
    
    # Convert latitude and longitude to float values
    latitude = float(latitude)
    longitude = float(longitude)

    # Insert or update the location in your database
    insert_or_update_location(from_number, latitude, longitude)
    print(f"The custoemr {from_number} sent location. It's saved in the database.")
