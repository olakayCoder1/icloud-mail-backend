import json
import threading
import time
import uuid
from flask_restx import Namespace , Resource 
from http import HTTPStatus
from flask import request
from ..tasks import backgroud_email_sending_via_icloud_webmail
from .manager import ICloudManager
from .serializers import (
   SEND_EMAIL_FIELDS_SERIALIZER,
   OTP_FIELDS_SERIALIZER,
   LOGIN_FIELDS_SERIALIZER,
   SEND_NEW_EMAIL_FIELDS_SERIALIZER
)




icloud_namespace = Namespace('email', 'Email api endpoints namespace' ,path='/email')


send_email_model = icloud_namespace.model( 'Email Sending Initialization', SEND_EMAIL_FIELDS_SERIALIZER)
otp_submission_model = icloud_namespace.model( 'OTP Submission', OTP_FIELDS_SERIALIZER)
icloud_login_model = icloud_namespace.model( 'Login', LOGIN_FIELDS_SERIALIZER)
send_new_email_model = icloud_namespace.model( 'New email', SEND_NEW_EMAIL_FIELDS_SERIALIZER)



icloud_manager = ICloudManager()

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
        icloud_manager.add_otp_to_json_file(identifier,otp)
        # time.sleep(10)
        # success = icloud_manager.remove_otp_from_json_file(identifier)
        # if success:
        #     return {"status":True, "message":"Login successful"}, 200
        # else:
        #     return {"status":False, "message":"Invalid otp"} , 400
        # Poll the file for removal
        for _ in range(10):  # Check every second for up to 10 seconds
            success = icloud_manager.remove_otp_from_json_file(identifier)
            if success:
                return {"status": True, "message": "Login successful"}, 200
            time.sleep(1)

        return {"status": False, "message": "Invalid OTP"}, 400




@icloud_namespace.route('/login')
class IcloudMailSenderLoginApiView(Resource):

    @icloud_namespace.expect(icloud_login_model)  
    @icloud_namespace.doc(description='Icloud Login' )
    def post(self):
        data = request.get_json()  
        identifier = str(uuid.uuid4())

        email = data['email'] 
        password = data['password'] 
        try:
            time.sleep(3)
            if icloud_manager.driver:
                return {"status": False, "message": "There is an active session"}, 400
            
            email_thread = threading.Thread(
                target=icloud_manager.login_to_icloud, args=(email,password,identifier,),
                kwargs={}
            )
            email_thread.start()
            response = {
                "status": "queued", 
                "message":"Kinldy provide the otp send to your phone/device",
                'identifier':identifier 
            }
            return response , HTTPStatus.OK
        except Exception as e:
            # return internal server error
            return {"status": False, "message": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR
        



@icloud_namespace.route('/webhook-send-mail')
class IcloudMailSenderNewMailApiView(Resource):

    @icloud_namespace.expect(send_new_email_model)  
    @icloud_namespace.doc(description='Send new email' )
    def post(self):
        data = request.get_json()  

        email = data['to'] 
        body = data['body'] 
        subject = data['subject'] 
        queue_id = data['queue_id'] 
        try:
            # email_thread = threading.Thread(
            #     target=icloud_manager.send_email, args=(email,subject,body,queue_id,),
            #     kwargs={}
            # )
            # email_thread.start()
            # response = {
            #     "status": "true", 
            #     "message":"",
            # }
            response = icloud_manager.send_email(email,subject,body,queue_id)
            return response , HTTPStatus.OK
        except Exception as e:
            # return internal server error
            return {"status": False, "message": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR





@icloud_namespace.route('/initiate')
class IcloudMailSenderApiView(Resource):

    @icloud_namespace.expect(send_email_model)  
    @icloud_namespace.doc(description='Email sending initialization' )
    def post(self):
        data = request.get_json()  
        identifier = str(uuid.uuid4())
        data['identifier'] = identifier


        # using celery make the api call to send the email
        # task = backgroud_email_sending_via_icloud_webmail.delay(data)

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



# @app.route("/email/logout", methods=["POST"])
# def logout():
#     icloud_manager.close_session()
#     return jsonify({"status": "success", "message": "Logged out and session closed"}), HTTPStatus.OK
