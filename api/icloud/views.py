import json
import threading
import time
import uuid
from flask_restx import Namespace , Resource
import hmac
from http import HTTPStatus
from flask import request
from ..helpers.utils import db
from api.icloud.models import Account, AccountConfig
from .manager import ICloudManager
from .serializers import (
   SEND_EMAIL_FIELDS_SERIALIZER,
   OTP_FIELDS_SERIALIZER,
   LOGIN_FIELDS_SERIALIZER,
   SEND_NEW_EMAIL_FIELDS_SERIALIZER,
   REMOVE_ACCOUNT_FIELDS_SERIALIZER,
   ACCOUNT_THRESHOLD_UPDATE_FIELDS_SERIALIZER
)




icloud_namespace = Namespace('email', 'Email api endpoints namespace' ,path='/email')


send_email_model = icloud_namespace.model( 'Email Sending Initialization', SEND_EMAIL_FIELDS_SERIALIZER)
otp_submission_model = icloud_namespace.model( 'OTP Submission', OTP_FIELDS_SERIALIZER)
icloud_login_model = icloud_namespace.model( 'Login', LOGIN_FIELDS_SERIALIZER)
send_new_email_model = icloud_namespace.model( 'New email', SEND_NEW_EMAIL_FIELDS_SERIALIZER)
remove_email_account_model = icloud_namespace.model( 'Remove email account', REMOVE_ACCOUNT_FIELDS_SERIALIZER)
update_email_accounts_threshold_model = icloud_namespace.model( 'Update account limit', ACCOUNT_THRESHOLD_UPDATE_FIELDS_SERIALIZER)



icloud_manager = ICloudManager()


def _validate_auth(auth_header):
    """
    Validate the Basic Auth credentials from the Authorization header.
    """
    WEBHOOK_USERNAME = "scraping"
    WEBHOOK_PASSWORD = "Hm_P&d5(7i2mEn4*dH,Stmq"
    try:
        # Basic authentication header format: "Basic base64encoded(username:password)"
        auth_type, credentials = auth_header.split(' ')
        if auth_type != 'Basic':
            return False

        import base64
        decoded_credentials = base64.b64decode(credentials).decode('utf-8')
        username, password = decoded_credentials.split(':', 1)

        # Compare credentials securely
        return hmac.compare_digest(username, WEBHOOK_USERNAME) and hmac.compare_digest(password, WEBHOOK_PASSWORD)
    except Exception:
        return False


@icloud_namespace.route('/threshold')
class AccountCountResource(Resource):
    """Endpoint to get the count of available accounts."""

    def get(self):
        """Get the count of accounts in the database."""
        try:
            active_account_count = Account.query.filter_by(is_active=True).count()

            account_config = AccountConfig.get_or_create(title="threshold")
            # find the percentage of active accounts to account_config.max_accounts
            threshold_percentage = (active_account_count / account_config.max_accounts) * 100

            return {
                "status": True, 
                "data": {
                    "percentage":threshold_percentage,
                    "registered": active_account_count, 
                    'threshold':account_config.max_accounts
                }
                }, 200
        except Exception as e:
            return {"status": False, "message": str(e)}, 500


@icloud_namespace.route('/setting/account-limit')
class AccountLimitResource(Resource):
    """Endpoint to update the account limit."""


    @icloud_namespace.expect(update_email_accounts_threshold_model)  
    @icloud_namespace.doc(description='Account Limit Update' )
    def put(self):
        """Update the account limit."""
        try:
            # # Extract and validate the 'Authorization' header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not _validate_auth(auth_header):
                return {"status": False, "message": "Unauthorized"}, HTTPStatus.UNAUTHORIZED
        
            data = request.get_json()

            if 'max_accounts' not in data:
                return {"status": False, "message": "max_accounts is required"}, 400
            
            if not isinstance(data['max_accounts'], int) or data['max_accounts'] <= 0:
                return {"status": False, "message": "max_accounts must be a positive integer"}, 400
            
            account_config = AccountConfig.get_or_create(title="threshold")
            account_config.max_accounts = data['max_accounts']
            db.session.commit()
            return {"status": True, "message": "Account limit updated successfully"}, 200
        except:
            return {"status": False, "message": "Failed to update account limit"}, 500



@icloud_namespace.route('/setting/accounts')
class AccountsListResource(Resource):
    """Endpoint to update the account limit."""

    def get(self):
        """Get all accounts."""
        accounts = [ dict(id=str(val.id),email=val.email) for val in Account.query.all()]
        return {"status": True, "data": accounts}, 200
    

    @icloud_namespace.expect(remove_email_account_model)  
    @icloud_namespace.doc(description='Delete account' )
    def delete(self):
        """Delete an accounts."""
        try:
            # # Extract and validate the 'Authorization' header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not _validate_auth(auth_header):
                return {"status": False, "message": "Unauthorized"}, HTTPStatus.UNAUTHORIZED
            data = request.get_json()
            if 'id' not in data:
                return {"status": False, "message": "id is required"}, 400
            account = Account.query.filter_by(id=data['id']).first()
            if not account:
                return {"status": False, "message": "Account not found"}, 404
            db.session.delete(account)
            db.session.commit()
            return {"status": True, "message": "Account deleted successfully"}, 200
        except:
            return {"status": False, "message": "Failed to delete account"}, 500
            


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

        account_exist = Account.query.filter_by(id=uuid.UUID(identifier)).first()

        if not account_exist:
            return {"status": False, "message": "Account does not exist"}, 400

        icloud_manager.add_otp_to_json_file(identifier,otp,account_exist.email)
        return {"status": True, "message": "OTP submitted successfully"}, 200




@icloud_namespace.route('/login')
class IcloudMailSenderLoginApiView(Resource):

    @icloud_namespace.expect(icloud_login_model)  
    @icloud_namespace.doc(description='Icloud Login' )
    def post(self):
        data = request.get_json()  
        identifier = str(uuid.uuid4())

        email = data['email'].lower() 
        password = data['password'] 
        try:
            # if icloud_manager.driver:
            #     return {"status": False, "message": "There is an active session"}, 400
            

            # Check if the email already exists
            existing_account = Account.query.filter_by(email=email).first()

            if not existing_account:
                # Fetch account configuration (with title 'threshold')
                account_config = AccountConfig.get_or_create(title="threshold")

                # Check if the number of active accounts is equal to max_accounts
                active_account_count = Account.query.filter_by(is_active=True).count()

                if active_account_count >= account_config.max_accounts:
                    return {
                        "status": False,
                        "message": f"Account limit reached. Maximum number of active accounts is {account_config.max_accounts}."
                    }, HTTPStatus.BAD_REQUEST
                # else:
            account = Account.get_or_create(email=email,is_active=True) 
                    # new_account = Account.add_account(email=email, is_active=False)

            email_thread = threading.Thread(
                target=icloud_manager.login_to_icloud, args=(email,password,account.id),
                kwargs={}
            )
            email_thread.start()
            response = {
                "status": "queued", 
                "message":"Kinldy provide the otp send to your phone/device",
                'identifier':str(account.id)
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

        # # Extract and validate the 'Authorization' header
        # auth_header = request.headers.get('Authorization')
        # if not auth_header or not self._validate_auth(auth_header):
        #     return {"status": False, "message": "Unauthorized"}, HTTPStatus.UNAUTHORIZED
        
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
        




@icloud_namespace.route('/kill')
class IcloudMailSenderApiView(Resource):

    @icloud_namespace.doc(description='Session Kill' )
    def get(self):


        icloud_manager.close_session()
        

        response = {
                "status": True, 
                "message":"Session destroyed",
            }
        return response , HTTPStatus.OK 




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
