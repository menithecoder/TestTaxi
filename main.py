from flask import Flask, request, session , render_template, jsonify, send_from_directory, Response,current_app, url_for
from twilio.twiml.voice_response import VoiceResponse, Gather
import sqlite3
import logging
import threading
import time
from DataBase import  store_user_data,get_price_from_db
from locationFinder import convert_to_coordinates
from Drivers import WHAPI_Location_reply,WHAPI_Poll_reply,update_debt
from CloseCustomerAlgorithem import find_sorted_drivers
import os

import copy
#for telnyx
import time
from google.cloud import speech
from google.cloud.speech import RecognitionConfig, RecognitionAudio
import telnyx
import paypalrestsdk
import requests
from WHAPI import send_message_to_whatsapp,send_Poll_message
from flask_cors import CORS
from Customer import CustomerInfo
from WhatsAppToDriver import get_customer_info,send_customer_info,poll_customer_drivers,DriverAfterAprovePoll,poll_states
app = Flask(__name__)
app.secret_key = "menithecoder"

# Set your Telnyx API key

telnyx.api_key = os.getenv('TELNYX_API_KEY')
PAYPAL_CLIENTID=os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET=os.getenv('PAYPAL_CLIENT_Secret')


db_path = "prices.sqlite"

# Specify the Current_Place and Destination
current_place = "בית שמש"
destination = "ירושלים"

# Call the function
price = get_price_from_db(db_path, current_place, destination)
print(f"the price for {current_place} to {destination} is {price}")
def ConverCustomerLocationToLanLog():
    print("going to coordinate ")
    #thread = threading.Thread(target=convert_to_coordinates)
    convert_to_coordinates()
    #thread.start()
############################################################################################
paypalrestsdk.configure({
    "mode": "sandbox",  # Change to 'live' for production
    "client_id": PAYPAL_CLIENTID,  # Replace with your PayPal client ID
    "client_secret": PAYPAL_CLIENT_SECRET  # Replace with your PayPal client secret
})

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/create-order', methods=['POST'])
def create_order():
    data = request.get_json()

    phone_number = data.get('phone_number')
    amount = data.get('amount')

    # Create PayPal payment order
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "transactions": [{
            "amount": {
                "total": amount,
                "currency": "ILS"
            },
            "description": f"Payment for phone number {phone_number}"
        }],
        "redirect_urls": {
            "return_url": url_for('payment_success', _external=True),
            "cancel_url": url_for('payment_cancel', _external=True)
        }
    })

    if payment.create():
        # Get approval URL
        for link in payment.links:
            if link.rel == "approval_url":
                approval_url = link.href
                return jsonify({'orderID': approval_url})  # Return PayPal order ID
    else:
        return jsonify({'error': 'Payment creation failed'}), 400
@app.route('/payment-success', methods=['POST'])
def payment_success():
    data = request.get_json()
    phone_number = data.get('phone_number')
    amount = data.get('amount')
    payer_name = data.get('payer_name')
    payer_email = data.get('payer_email')

    update_debt(phone_number, amount,'decrease')
    print(f"Payment successful! Phone: {phone_number}, Amount: {amount}, Payer: {payer_name}, Email: {payer_email}")

    return jsonify({
        "status": "success",
        "message": "Payment processed successfully",
        "phone_number": phone_number,
        "amount": amount,
        "payer_name": payer_name,
        "payer_email": payer_email
    }), 200


@app.route("/payment-cancel")
def payment_cancel():
    return render_template("cancel.html")
##############################################################################################################	
@app.route('/whatsapp', methods=['POST'])
def whatsapp():
    # Parse the incoming JSON data
    data = request.get_json(force=True, silent=True)
    
    if not data:
        return jsonify({"error": "Invalid or no JSON data received"}), 400
    
    # Extract relevant data
    try:
        message = data["messages"][0]
       
        if "location" in message:
            print("locationsssssssssssssssssssssssss")
            WHAPI_Location_reply(message)
            
        if "action" in message and message["action"].get("type") == "vote":
            print(f"Message from: {message.get('from', None)}")
            print(f"Poll states: {poll_states}")
            for customernumber, state in poll_states.items():
                if str(state["current_driver"]) == message.get('from', None):
                    if WHAPI_Poll_reply(message):
                        state["response_received"] = True
			    
                        print(f"Customer {customernumber}: Driver {message.get('from')} approved the poll.")
                        #DriverAfterAprovePoll(customernumber, message.get('from', None))
                    else:
                        print(f"Customer {customernumber}: Driver {message.get('from')} responded but did not approve.")
                else:
                    send_message_to_whatsapp(message.get('from'), "מתנצלים עברו 20 שניות נהג אחר כבר על זה")
		    
        print("333333333333333333333333333333333333333333333333333333333")
        #send_Poll_message(from_number)
        return '', 200 

    except KeyError as e:
        # Handle missing keys
        return jsonify({"error": f"Missing key: {str(e)}"}), 400
    except Exception as e:
        # Handle other unexpected errors
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    """
    Handle incoming IVR events from Telnyx.
    """

	
customer_info_dict = {}
@app.route('/ivr', methods=['POST'])
def incomeCall():
    data = request.json
    event_type = data.get("data", {}).get("event_type")
    call_control_id = data["data"]["payload"]["call_control_id"]
    call = telnyx.Call.retrieve(call_control_id)
    
    if event_type == "call.hangup":
        customer_info = customer_info_dict.get(call_control_id)
        if customer_info:
            customer_info.delete_audio_file()

    # Handle different event types
    if event_type == "call.dtmf.received":
        digit_pressed = data["data"]["payload"]["digit"]
        print(f"Digit pressed: {digit_pressed}")
        
        customer_info = customer_info_dict.get(call_control_id)
        if digit_pressed == "1":
            # Playback specific audio for digit "1"
            try:
                call.playback_start(audio_url="https://storage.googleapis.com/telnyxmp3/ReservationMade.mp3")
                time.sleep(4)  # Optional delay before proceeding
                call.hangup()
                store_user_data(customer_info.phone_number, customer_info.city, customer_info.street, customer_info.number, customer_info.destination,0.0,0.0,0,customer_info.price)
                ConverCustomerLocationToLanLog()
                #time.sleep(1)
                background_thread = threading.Thread(target=poll_customer_drivers, args=(customer_info.phone_number,))
                
                # Ensure the thread is non-daemon (which is the default)
                background_thread.daemon = False  # Set to False explicitly, though it's already False by default
                background_thread.start()
            except Exception as e:
                print(f"Error during handling digit 1: {str(e)}")
    

	
    if event_type == "call.initiated":
        print("Call initiated")
        # Handle call initiation, answer the call
        try:
            call.answer()
        except Exception as e:
            return jsonify({"error": f"Failed to answer call: {str(e)}"}), 500

    if event_type == "call.answered":
        # Initialize the customer info and store it in the global dictionary
        customer_info = CustomerInfo()  # Initialize CustomerInfo object
        

        print("Call answered")
        # Start background thread for processing after call is answered
        thread = threading.Thread(target=allProcessBackground, args=(data, call, customer_info,call_control_id,))
       
        thread.start()

    # Return response after processing
    return jsonify({"message": "Event handled successfully", "event_type": event_type}), 200

def allProcessBackground(data, call, customer_info,call_control_id):
    print("answered")

    # Extract phone number
    phone_number = data.get('data', {}).get('payload', {}).get('from')
    if not phone_number:
        print("No 'from' field found in the payload.")
        phone_number = "Unknown"  # Assign a default value
    elif phone_number.startswith('+972'):
        phone_number = '0' + phone_number[4:]  # Convert international format to local

    # Assign phone number to customer_info
    customer_info.phone_number = phone_number
    print("Final Phone Number:", phone_number)

    # Request customer details
    try:
        customer_info.city = customer_info.cityRequest(call)
        customer_info.street = customer_info.streetRequest(call)
        customer_info.number = customer_info.numberRequest(call)
        customer_info.destination = customer_info.destinationRequest(call)
    except Exception as e:
        print(f"Error fetching customer details: {e}")
        return

    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

    
    try:
        call.playback_start(audio_url="https://storage.googleapis.com/telnyxmp3/got.wav")
        time.sleep(1)
    except Exception as e:
        print(f"Error playing initial audio: {e}")
        return

    
    try:
        customer_info.text_to_speech(customer_info.Getmp3File())
        call.playback_start(audio_url=f"https://storage.googleapis.com/telnyxmp3/{phone_number}.mp3?timestamp={int(time.time())}", cache_audio=False)

        time.sleep(6)

        price =customer_info.update_price()
        call.playback_start(audio_url="https://storage.googleapis.com/telnyxmp3/price.mp3",cache_audio=False)
        time.sleep(1.6)
    
        customer_info.text_to_speech(
            str(price),
            "price")
        
        customer_info_dict[call_control_id] = copy.deepcopy(customer_info)##copying the customer info to the dictt############################ 
        call.playback_start(audio_url=f"https://storage.googleapis.com/telnyxmp3/{phone_number}price.mp3?timestamp={int(time.time())}")
        time.sleep(1)
    except Exception as e:
        print(f"Error in text-to-speech or playing final audio: {e}")
        return

    customer_info.reset_info()
    try:
        gather_response = call.gather_using_audio(
            call_control_id=call.call_control_id,
            minimum_digits=1,
            maximum_digits=1,
            timeout_millis=60000,  # 60 seconds timeout
            audio_url="https://storage.googleapis.com/telnyxmp3/confirmation.wav",
            initial_timeout_millis=5000,  # 5 seconds initial timeout
            terminating_digit="#",  # Terminating digit
            valid_digits="12"  # Only '1' and '2' are valid
        )
        print(gather_response)
    except Exception as e:
        print(f"Error during DTMF input gathering: {e}")

    # Clean up audio files
    files_to_delete = [
        f"recording_{phone_number}.wav",
        f"tts{phone_number}.mp3",
        f"mono_{phone_number}.wav"
    ]
    for file in files_to_delete:
        deleteFile(file) 	
            
def deleteFile(file_to_delete):
    if os.path.exists(file_to_delete):
            os.remove(file_to_delete)
            print(f"{file_to_delete} has been deleted.")
    else:
        print(f"{file_to_delete} does not exist.")




def forward_call(call_control_id, new_destination):
    url = f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/transfer"
    headers = {
        "Authorization": f"Bearer {telnyx.api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": new_destination,
        "from": "+972555076947"
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"Call forwarded successfully to {new_destination}.")
    else:
        print(f"Failed to forward call: {response.text}")

@app.route('/forward', methods=['POST'])
def forwardCall():
    data = request.json
    event_type = data.get("data", {}).get("event_type")
    call_control_id = data["data"]["payload"]["call_control_id"]
    call = telnyx.Call.retrieve(call_control_id)

    if event_type == "call.hangup":
        customer_info = customer_info_dict.get(call_control_id)
        if customer_info:
            customer_info.delete_audio_file()

    if event_type == "call.initiated":
        print("Call initiated")
        # Answer the call
        try:
            call.answer()
        except Exception as e:
            return jsonify({"error": f"Failed to answer call: {str(e)}"}), 500

    if event_type == "call.answered":
        print("Call answered")
        # Forward call based on your first condition
        try:
            forward_call(call_control_id, "+972515851322")
        except Exception as e:
            return jsonify({"error": f"Failed to forward call: {str(e)}"}), 500

        

    return jsonify({"message": "Event processed"}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
    
