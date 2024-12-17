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




LOGIN_FIELDS_SERIALIZER = {
    'email' : fields.String(required=True , description='Icloud email'),
    'password' : fields.String(required=True , description='Password'),
}



SEND_NEW_EMAIL_FIELDS_SERIALIZER = {
    'to' : fields.String(required=True , description='Receiver email'),
    'subject' : fields.String(required=True , description='Email subject'),
    'body' : fields.String(required=True , description='Email body'),
    'queue_id' : fields.String(required=True , description='Unique Identifier'),
}



ACCOUNT_THRESHOLD_UPDATE_FIELDS_SERIALIZER = {
    'max_accounts' : fields.Integer(required=True , description='Maximum account'),
}

REMOVE_ACCOUNT_FIELDS_SERIALIZER = {
    'id' : fields.String(required=True , description='Account ID'),
}
