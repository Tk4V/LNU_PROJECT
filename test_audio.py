import jwt
import datetime

user_data = {
    'id': '1',  # user_id
    'username': 'kuku',
    'email': 'newuser@example.com',
}

token = jwt.encode(
    {'id': user_data['id'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)},  # Expiry time of 1 hour
    'secret',  # Replace with your actual secret key
    algorithm='HS256'
)

print(f"Generated token: {token}")
