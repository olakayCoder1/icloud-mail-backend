import json
import threading
import time
import uuid
from flask_restx import Namespace , Resource 
from http import HTTPStatus
from flask import request
from .manager import ICloudManager
from .serializers import (
   SEND_EMAIL_FIELDS_SERIALIZER,
   OTP_FIELDS_SERIALIZER
)




icloud_namespace = Namespace('email', 'Email api endpoints namespace' ,path='/email')


send_email_model = icloud_namespace.model( 'Email Sending Initialization', SEND_EMAIL_FIELDS_SERIALIZER)
otp_submission_model = icloud_namespace.model( 'OTP Submission', OTP_FIELDS_SERIALIZER)



@icloud_namespace.route('/initiate')
class IcloudMailSenderApiView(Resource):

    @icloud_namespace.expect(send_email_model)  
    @icloud_namespace.doc(description='Email sending initialization' )
    def post(self):
        data = request.get_json()  
        identifier = str(uuid.uuid4())
        data['identifier'] = identifier
        email_thread = threading.Thread(
            target=ICloudManager().send_icloud_mail, args=(data,),
            kwargs={}
        )
        email_thread.start()
        

        response = {
                "status": "queued", 
                "message":"Email sending session initiated. Kinldy provide the otp send to your phone/device",
                "queue_id": data['queue_id'], 
                'identifier':identifier 
            }
        return response , HTTPStatus.ACCEPTED 


@icloud_namespace.route('/submit-otp')
class OTPSubmissionApiView(Resource):

    @icloud_namespace.expect(otp_submission_model)  
    @icloud_namespace.doc(description='OTP Submission' )
    def post(self):
        data = request.get_json()  
        otp = data.get('otp')

        data = request.get_json()
        required_fields = ["identifier", "otp"]
        if not all(field in data for field in required_fields):
            return {"status": False, "message": "Missing required fields"}, 400
        

        identifier = data["identifier"]
        otp = data["otp"]
        
        # Load existing OTP data from the JSON file
        try:
            with open("otp_credentials.json", "r") as f:
                otp_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            otp_data = {}  # Initialize an empty dict if the file doesn't exist or is invalid

        # Update the identifier key with the new OTP
        otp_data[identifier] = otp
        
        # Save the updated data back to the JSON file
        with open("otp_credentials.json", "w") as f:
            json.dump(otp_data, f, indent=4)
        


        return  {"status": True , "message": "OTP submitted successfully"}, HTTPStatus.OK




