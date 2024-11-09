from flask_restx import fields





SEND_EMAIL_FIELDS_SERIALIZER = {
    'email' : fields.String(required=True , description='Auth email'),
    'password' : fields.String(required=True , description='Auth password'),
    'to' : fields.String(required=True , description='Receiver email'),
    'subject' : fields.String(required=True , description='Email subject'),
    'body' : fields.String(required=True , description='Email body'),
    'queue_id' : fields.String(required=True , description='Unique Identifier'),
}



OTP_FIELDS_SERIALIZER = {
    'otp' : fields.String(required=True , description='OTP'),
    'identifier' : fields.String(required=True , description='Identifier'),
}