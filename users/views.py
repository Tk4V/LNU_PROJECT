from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from .serializers import UserSerializer
from .models import User
from gtts import gTTS
import jwt, datetime
import openai
import datetime
import base64
from .models import GPTMessageLog 
import os
from django.conf import settings
from django.http import JsonResponse
from dotenv import load_dotenv
import requests


load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise EnvironmentError("OPENAI_API_KEY environment variable is not set!")



class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')  # Retrieve email from the request
        password = request.data.get('password')  # Retrieve password from the request

        # Check if a user with the provided email exists
        user = User.objects.filter(email=email).first()
        if user is None:
            raise AuthenticationFailed('User not found!')

        # Verify the password
        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect password!')

        # Generate the JWT payload
        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),  # Expiration time
            'iat': datetime.datetime.utcnow()  # Issued at time
        }

        # Generate a JWT token
        token = jwt.encode(payload, 'secret', algorithm='HS256')

        # Create the response object
        response = Response()
        response.set_cookie(key='jwt', value=token, httponly=True)  # Set token as an HTTP-only cookie
        response.data = {
            'jwt': token  # Include the token in the response
        }

        return response

class UserView(APIView):
    def get(self, request):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Unauthenticated!')

        try:
            # Decode the token using the specified algorithm
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])  # Corrected 'algorithms' argument
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired!')

        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token!')

        # Get the user from the decoded payload
        user = User.objects.filter(id=payload['id']).first()
        
        if not user:
            raise AuthenticationFailed('User not found!')

        # Serialize the user data
        serializer = UserSerializer(user)

        return Response(serializer.data)

class LogoutView(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {
            'message': 'success'
        }
        return response



class GPTView(APIView):
    """
    DRF view to handle GPT interactions: send prompt, save response, and return data.
    """
    def post(self, request):
        # Authenticate the user
        token = request.COOKIES.get('jwt')
        if not token:
            raise AuthenticationFailed('Unauthenticated!')

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired!')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token!')

        user_id = payload.get('id')
        if not user_id:
            raise AuthenticationFailed('User not found!')

        # Validate the prompt
        prompt = request.data.get('prompt')
        if not prompt:
            raise ValidationError('Prompt is required!')

        try:
            # Send prompt to microservice
            microservice_url = "http://127.0.0.1:8001/items/"
            response = requests.post(
                microservice_url,
                json={"prompt": prompt}
            )
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Extract response data
            response_data = response.json()
            answer = response_data.get("answer")
            voice_base64 = response_data.get("voice")

            # Save the data to the database
            GPTMessageLog.objects.create(
                user_id=user_id,
                prompt=prompt,
                gpt_response=answer,
                timestamp=datetime.datetime.now(),
            )

            # Return the response to the user
            return Response({
                "answer": answer,
                "category": "new",
                "date": datetime.datetime.now(),
                "voice": voice_base64
            })

        except requests.exceptions.RequestException as e:
            raise ValidationError(f"Error communicating with microservice: {str(e)}")
        except Exception as e:
            raise ValidationError(f"An unexpected error occurred: {str(e)}")