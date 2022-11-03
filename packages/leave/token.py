from itsdangerous import URLSafeTimedSerializer
from flask import current_app


def generate_token(value):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(value, salt=current_app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt= current_app.config['SECURITY_PASSWORD_SALT']
        )
    except:
        return False
    return email

