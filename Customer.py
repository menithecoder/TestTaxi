from pydub import AudioSegment
import requests
import base64
import os
import requests
import json
import base64
from google.cloud import storage
import time
import telnyx
from DataBase import get_price_from_db

# Set your API key 
API_KEY =  os.getenv('GOOGLE_API_KEY')
telnyx.api_key = os.getenv('TELNYX_API_KEY')
json_creds = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
class CustomerInfo:
    def __init__(self, city="", street="", number="", destination="", phone_number="", price=0.0):
        self.city = city
        self.street = street
        self.number = number
        self.destination = destination
        self.phone_number = phone_number
        self.price = price  # Added price attribute

    def update_price(self):
        price = get_price_from_db("prices.sqlite", self.city, self.destination)
        if price is not None:
            self.price = price  # Update the price attribute
            return price  # Return the price directly
        else:
            return None  # Return None if no price is found

    def reset_info(self):
        # Resetting all attributes to their default empty values
        print("Resetting customer info...")
        self.city = ""
        self.street = ""
        self.number = ""
        self.destination = ""
        self.phone_number = ""
        self.price = 0.0  # Reset price to default

    def __del__(self):
        self.reset_info()

    # Method to convert object to dictionary (serialization)
    def to_dict(self):
        return {
            'city': self.city,
            'street': self.street,
            'number': self.number,
            'destination': self.destination,
            'phone_number': self.phone_number,
            'price': self.price  # Include price in the dictionary
        }


    # Static method to create a CustomerInfo object from a dictionary (deserialization)
    @staticmethod
    def from_dict(data):
        return CustomerInfo(
            city=data.get('city'),
            street=data.get('street'),
            number=data.get('number'),
            destination=data.get('destination'),
            phone_number=data.get('phone_number')
        )
    def __repr__(self):
        return (
            f"CustomerInfo(city='{self.city}', street='{self.street}', "
            f"number='{self.number}', destination='{self.destination}')"
        )
    def Getmp3File(self):
        return (
            f"לסיכום, אתה נמצא בעיר {self.city},  ברחוב {self.street}, מספר  {self.number},  והיעד {self.destination}"
        )
    
    def cityRequest(self,call):
        call.playback_start(audio_url="https://storage.googleapis.com/telnyxmp3/intro.mp3")
        
        time.sleep(5.92)
        
        # Start recording
        
        
        response = call.record_start(format="wav", channels="single")
        print(response)
        print("record start")
        recording_id = response.get("recording_id")
    
        # Wait for 3 seconds before stopping the recording
        time.sleep(2.2)
        
        stop_response = call.record_stop()
        print("Recording stopped")
        #call.send_dtmf(digits="555")
         # Check if the recording was successful
        if stop_response.get("data", {}).get("result") == "ok":
            print("Recording succeeded:", stop_response)
        else:
            print("Recording failed or result unknown:", stop_response)
        time.sleep(1)
        start_time = time.time()
        self.downloadWav(recording_id)
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"downloadWav: {elapsed_time} seconds")
        start_timeT = time.time()
       
        recording_name = f"recording_{self.phone_number}.wav"
        city=self.transcribe_audio(recording_name)
        end_timeT = time.time()
        elapsed_timeT = end_timeT - start_timeT
        print(f"transcribe_audio: {elapsed_timeT} seconds")
    
        start_timeTS = time.time()
        #text_to_speech(city)
        end_timeTS = time.time()
        elapsed_timeTS = end_timeTS - start_timeTS
        print(f"transcribe_audio: {elapsed_timeTS} seconds")
        return city
    def streetRequest(self,call):
        print("streeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeet")
        call.playback_start(audio_url="https://storage.googleapis.com/telnyxmp3/got.wav")
        call.playback_start(audio_url="https://storage.googleapis.com/telnyxmp3/street.wav")
        time.sleep(2.7)
        
        # Start recording
        
        
        response = call.record_start(format="wav", channels="single")
        print(response)
        print("record start")
        recording_id = response.get("recording_id")
    
        # Wait for 3 seconds before stopping the recording
        time.sleep(2.2)
        
        stop_response = call.record_stop()
        print("Recording stopped")
        #call.send_dtmf(digits="555")
         # Check if the recording was successful
        if stop_response.get("data", {}).get("result") == "ok":
            print("Recording succeeded:", stop_response)
        else:
            print("Recording failed or result unknown:", stop_response)
        time.sleep(1)
        self.downloadWav(recording_id)
        
        recording_name = f"recording_{self.phone_number}.wav"
        street=self.transcribe_audio(recording_name)
        #text_to_speech(street)
        return street
    def numberRequest(self,call):
        print("numeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeer")
        call.playback_start(audio_url="https://storage.googleapis.com/telnyxmp3/got.wav")
        call.playback_start(audio_url="https://storage.googleapis.com/telnyxmp3/number.wav")
        time.sleep(2.2)
        
        # Start recording
        response = call.record_start(format="wav", channels="single")
        print(response)
        print("record start")
        recording_id = response.get("recording_id")
    
        # Wait for 3 seconds before stopping the recording
        time.sleep(2.8)
        
        stop_response = call.record_stop()
        print("Recording stopped")
        #call.send_dtmf(digits="555")
         # Check if the recording was successful
        if stop_response.get("data", {}).get("result") == "ok":
            print("Recording succeeded:", stop_response)
        else:
            print("Recording failed or result unknown:", stop_response)
        time.sleep(1)
        self.downloadWav(recording_id)
        
        recording_name = f"recording_{self.phone_number}.wav"
        number=self.transcribe_audio(recording_name)
        ##text_to_speech(number)
        return number
        
    def destinationRequest(self,call):
        print("destiiiiiiiiiiiiiiiiiiiiination")
        call.playback_start(audio_url="https://storage.googleapis.com/telnyxmp3/got.wav")
        call.playback_start(audio_url="https://storage.googleapis.com/telnyxmp3/destination.wav")
        time.sleep(2.4)
        
        # Start recording
        
        
        response = call.record_start(format="wav", channels="single")
        print(response)
        print("record start")
        recording_id = response.get("recording_id")
    
        # Wait for 3 seconds before stopping the recording
        time.sleep(2.8)
        
        stop_response = call.record_stop()
        print("Recording stopped")
        #call.send_dtmf(digits="555")
         # Check if the recording was successful
        if stop_response.get("data", {}).get("result") == "ok":
            print("Recording succeeded:", stop_response)
        else:
            print("Recording failed or result unknown:", stop_response)
        time.sleep(1)
        self.downloadWav(recording_id)
        recording_name = f"recording_{self.phone_number}.wav"
        dest=self.transcribe_audio(recording_name)
        #text_to_speech(dest)
        return dest

    
    def downloadWav(self,recording_id):
        url = f"https://api.telnyx.com/v2/recordings/{recording_id}"
        
        # Headers for authentication
        headers = {
            "Authorization": f"Bearer {telnyx.api_key}"
        }
        
        # Make a GET request to retrieve the recording details
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            recording_data = response.json().get('data')
            download_url = recording_data['download_urls']['wav']  # or 'mp3' if you prefer
        
            # Download the recording file
            recording_response = requests.get(download_url)
        
            if recording_response.status_code == 200:
                # Save the file locally
               
                recording_name = f"recording_{self.phone_number}.wav"
                with open(recording_name, "wb") as file:
                    file.write(recording_response.content)
                print("Recording downloaded successfully.")
            else:
                print("Failed to download the recording.")
        else:
            print("Failed to retrieve recording details.")

    ############################################################3
    ######speeech to text google
    ##############################################################
    
    def transcribe_audio(self,wav_file):
        print("transcibeFunctionStarted")
        # Load the audio file using pydub
        audio = AudioSegment.from_wav(wav_file)
    
        # Convert the audio to mono
        mono_audio = audio.set_channels(1)  # Converts to mono (1 channel)
    
        # Save the mono audio temporarily (optional, or you can skip this if not saving)
        mono_wav_file = f"mono_{self.phone_number}.wav"
        mono_audio.export(mono_wav_file, format="wav")
    
        # Extract the sample rate from the mono audio file
        sample_rate = mono_audio.frame_rate  # Sample rate from the WAV file
    
        # Google Speech-to-Text API URL
        url = f'https://speech.googleapis.com/v1p1beta1/speech:recognize?key={API_KEY}'
        
        # Read the mono WAV file and prepare the audio data
        with open(mono_wav_file, "rb") as audio_file:
            audio_content = audio_file.read()
    
        # Base64 encode the audio content
        encoded_audio = base64.b64encode(audio_content).decode('utf-8')
    
        # Prepare the request payload
        payload = {
            "config": {
                "encoding": "LINEAR16",  # Specify WAV encoding
                "sampleRateHertz": sample_rate,  # Use the correct sample rate
                "languageCode": "he-IL"  # Hebrew language code
            },
            "audio": {
                "content": encoded_audio  # Use base64 encoded audio content
            }
        }
    
        # Make the request to Google Cloud Speech-to-Text API
        response = requests.post(url, json=payload)
        print("transcibeFunctionfinidhedalmost")
        # Check for a successful response
        if response.status_code == 200:
            try:
                result = response.json()
                transcript = result['results'][0]['alternatives'][0]['transcript']
                print(transcript)
                return transcript
            except (KeyError, IndexError) as e:
                print(f"Error accessing transcript: {e}")
                return None
        else:
            print(f"Error: {response.status_code}, {response.text}") 
    ############################################################3
    ######text to speech google
    ##############################################################
    
    def text_to_speech(self,text, suffix=""):
        print("text to tpeech start")
        url = f'https://texttospeech.googleapis.com/v1/text:synthesize?key={API_KEY}'
    
        headers = {
            'Content-Type': 'application/json',
        }
    
        # Prepare the request body
        body = {
            'input': {
                'text': text
            },
            'voice': {
                'languageCode': 'he-IL',  # Hebrew
                'ssmlGender': 'MALE'  # Choose gender: FEMALE or MALE
            },
            'audioConfig': {
                'audioEncoding': 'MP3'  # Can be MP3, OGG_OPUS, LINEAR16
            }
        }
    
        # Send POST request
        response = requests.post(url, headers=headers, data=json.dumps(body))
        print("text to tpeech almost end")
        if response.status_code == 200:
            audio_content = response.json()['audioContent']
            print("try tts")
                 # Decode the base64 audio content and save it as a file
            audio_data = base64.b64decode(audio_content)
            ttsPath=f"tts{self.phone_number}.mp3"
            with open(ttsPath, 'wb') as audio_file:
                audio_file.write(audio_data)
            
            destination_blob_name = f"{self.phone_number}{suffix}.mp3"
            bucket_name = "telnyxmp3"
            upload_mp3_to_bucket(bucket_name, ttsPath, destination_blob_name)
            print("Audio content saved as output_hebrew.mp3")
        else:
            print(f"Error: {response.status_code}, {response.text}")

    def delete_audio_file(self):
        """
        Deletes audio files associated with the phone number from the bucket.
        """
        # Define file names based on the phone number
        destination_blob_name_price = f"{self.phone_number}price.mp3"
        destination_blob_name = f"{self.phone_number}.mp3"
    
        # Delete the files from the bucket
        delete_mp3_from_bucket("telnyxmp3", destination_blob_name_price)
        delete_mp3_from_bucket("telnyxmp3", destination_blob_name)
def upload_mp3_to_bucket(bucket_name, source_file_path, destination_blob_name):
    """
    Uploads an MP3 file to a Google Cloud Storage bucket.

    :param bucket_name: Name of the bucket to upload the file to.
    :param source_file_path: Local path of the MP3 file.
    :param destination_blob_name: Name of the file in the bucket.
    """
    # Initialize the Cloud Storage client
    # Initialize the Cloud Storage client with the service account
    credentials = service_account.Credentials.from_service_account_info(json_creds)

# Initialize the client with credentials
    client = storage.Client(credentials=credentials)

    # Get the bucket
    bucket = client.bucket(bucket_name)

    # Create a blob (object in the bucket)
    blob = bucket.blob(destination_blob_name)

    # Upload the file to the bucket
    blob.upload_from_filename(source_file_path)

    print(f"File {source_file_path} uploaded to {bucket_name}/{destination_blob_name}.")
    
def delete_mp3_from_bucket(bucket_name, destination_blob_name):
    """
    Deletes an MP3 file from a Google Cloud Storage bucket.

    :param bucket_name: Name of the bucket to delete the file from.
    :param destination_blob_name: Name of the file to delete in the bucket.
    """
    # Initialize the Cloud Storage client
    credentials = service_account.Credentials.from_service_account_info(json_creds)


    client = storage.Client(credentials=credentials)

    # Get the bucket
    bucket = client.bucket(bucket_name)

    # Create a blob (object in the bucket)
    blob = bucket.blob(destination_blob_name)

    # Delete the file from the bucket
    blob.delete()

    print(f"File {destination_blob_name} deleted from {bucket_name}.")

            
