from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from .serializers import UserSerializer
from .models import User, GPTMessageLog
import datetime
import os
import secrets  # For generating secure random tokens
from dotenv import load_dotenv
import requests
from django.utils import timezone

load_dotenv()

class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = User.objects.filter(email=email).first()
        if user is None:
            raise AuthenticationFailed('User not found!')

        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect password!')

        # Generate a secure token (example length: 32 characters)
        token = secrets.token_hex(32)

        # Save token to the user object or a separate Token model
        user.token = token  # Ensure 'token' field exists in the User model or create a Token model
        user.token_expiration = datetime.datetime.now() + datetime.timedelta(hours=1)
        user.save()

        return Response({'token': token})  # Return the token to the client

class LogoutView(APIView):
    def post(self, request):
        # Extract the Bearer token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise AuthenticationFailed('No Bearer token provided!')

        token = auth_header.split(' ')[1]

        # Find the user associated with this token
        user = User.objects.filter(token=token).first()
        if not user:
            raise AuthenticationFailed('Invalid token!')

        # Invalidate the token by clearing it
        user.token = None
        user.token_expiration = None
        user.save()

        return Response({'message': 'Successfully logged out!'})


class UserView(APIView):
    def get(self, request):
        # Extract Bearer token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise AuthenticationFailed('No Bearer token provided!')

        token = auth_header.split(' ')[1]

        # Validate the token
        user = User.objects.filter(token=token).first()
        if not user or user.token_expiration < datetime.datetime.now():
            raise AuthenticationFailed('Invalid or expired token!')

        serializer = UserSerializer(user)
        return Response(serializer.data)


class GPTView(APIView):
    def post(self, request):
        # Authenticate using Bearer token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise AuthenticationFailed('No Bearer token provided!')

        token = auth_header.split(' ')[1]
        user = User.objects.filter(token=token).first()
        if not user or user.token_expiration < timezone.now():  # Use timezone-aware now()
            raise AuthenticationFailed('Invalid or expired token!')

        # Validate and process the prompt
        prompt = request.data.get('prompt')
        if not prompt:
            raise ValidationError('Prompt is required!')

        try:
            microservice_url = "http://16.171.159.54:8000/items/"
            response = requests.post(microservice_url, json={"prompt": prompt})
            response.raise_for_status()

            response_data = response.json()
            answer = response_data.get("answer")
            voice_base64 = response_data.get("voice")

            # Save the data to the database
            GPTMessageLog.objects.create(
                user_id=user.id,
                prompt=prompt,
                gpt_response=answer,
                timestamp=timezone.now(),  # Ensure timezone-aware timestamp
            )

            return Response({
                "answer": answer,
                "category": "new",
                "date": timezone.now(),  # Ensure timezone-aware timestamp
                "voice": voice_base64
            })

        except requests.exceptions.RequestException as e:
            raise ValidationError(f"Error communicating with microservice: {str(e)}")
        except Exception as e:
            raise ValidationError(f"An unexpected error occurred: {str(e)}")
