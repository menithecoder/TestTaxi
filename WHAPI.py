import requests


# Replace these with your actual API URL and token

            
def send_message_to_whatsapp(phone_number, message):
    url = "https://gate.whapi.cloud/messages/text"
    
    # Ensure inputs are strings
    phone_number = str(phone_number)
    message = str(message)
    
    payload = {
        "typing_time": 0,
        "to": phone_number,  # Use the phone_number argument
        "body": message      # Use the message argument
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Bearer hqVHKS4z6gXW0wMgmJyU4S7pTqTn4Tdk"
    }
    
    # Send POST request
    response = requests.post(url, json=payload, headers=headers)
    
    # Print the response text (for debugging purposes)
    print(response.text)

         
def send_Poll_message(phone_number, customerPhone, distance):
    url = "https://gate.whapi.cloud/messages/poll"
    from WhatsAppToDriver import get_customer_info
    # Retrieve customer information
    customer_info = get_customer_info(customerPhone)
    if not customer_info:
        print(f"Customer information for {customerPhone} could not be retrieved.")
        return
    distance=round(distance, 2) 
    # Extract the destination from customer information
    destination = customer_info.get("destination", "Unknown Destination")
    
    # Ensure phone_number is a string
    phone_number = str(phone_number)
    
    # Construct the message title
    title = f"יש לקוח קרוב אליך ({distance} ק\"מ) שרוצה לנסוע ל {destination}. האם תרצה לקחת את הנסיעה(יש לך חצי דקה לאשר)?"
    
    # Payload for the poll message
    payload = {
        "options": ["מאשר", "לא מאשר"],
        "to": phone_number,
        "title": title
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Bearer hqVHKS4z6gXW0wMgmJyU4S7pTqTn4Tdk"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        print(f"Sending poll to {phone_number}")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while sending poll to {phone_number}: {e}")
        return None
