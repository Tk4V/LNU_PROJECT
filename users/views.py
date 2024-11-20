from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
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






class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LoginView(APIView):
    def post(self, request):
        email = request.data['email']
        password = request.data['password']

        
        user = User.objects.filter(email=email).first()

        
        if user is None:
            raise AuthenticationFailed('User not found!')

        
        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect password!')

        
        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            'iat': datetime.datetime.utcnow()
        }

       
        token = jwt.encode(payload, 'secret', algorithm='HS256')

        
        response = Response()

        
        response.set_cookie(key='jwt', value=token, httponly=True)

        
        response.data = {
            'jwt': token
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


load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise EnvironmentError("OPENAI_API_KEY environment variable is not set!")

class GPTView(APIView):
    def get(self, request):
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

        recent_logs = GPTMessageLog.objects.filter(user_id=user_id).order_by('-timestamp')[:10]
        
        logs_data = [
            {
                "prompt": log.prompt,
                "response": log.gpt_response,
                "timestamp": log.timestamp
            }
            for log in recent_logs
        ]

        return Response({
            "user_id": user_id,
            "recent_logs": logs_data
        })

    # Handle POST requests
    def post(self, request):
        print("Request received: ", request.data)
        
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

        prompt = request.data.get('prompt')
        if not prompt:
            raise AuthenticationFailed('Prompt is required!')

        try:
            print(f"Prompt received: {prompt}")
            completion = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "user",
                        "content": f"""відповідай дуже коротко до 20 слів,
                        Ти мені повинен довомогти вивчитись мови,
                        ось що я тебе прошу (Відповідай та тій мові яка іде далі):
                        {prompt}"""
                    }
                ]
            )

            chat_response = completion['choices'][0]['message']['content']
            print(f"Chat response: {chat_response}")

            GPTMessageLog.objects.create(
                user_id=user_id,
                prompt=prompt,
                gpt_response=chat_response,
                timestamp=datetime.datetime.now()
            )

            return Response({
                "answer": chat_response,
                "category": "new",
                "date": datetime.datetime.now(),
            })

        except Exception as e:
            raise AuthenticationFailed(f"Error processing the request: {str(e)}")
class AudioView(APIView):
    def post(self, request):
        try:
            token = request.COOKIES.get('jwt')
            if not token:
                raise AuthenticationFailed('Unauthenticated!')

            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
            user_id = str(payload.get('id'))
            if not user_id:
                raise AuthenticationFailed('Invalid user!')

            prompt = request.data.get('prompt')
            if not prompt:
                return JsonResponse({"error": "Prompt is required!"}, status=400)

  
            safe_prompt = prompt.replace(" ", "_").replace("/", "_").replace("\\", "_")
            audio_file_path = os.path.join(settings.MEDIA_ROOT, 'audio', f"{user_id}_{safe_prompt}.mp3")

  
            os.makedirs(os.path.dirname(audio_file_path), exist_ok=True)

   
            if not os.path.exists(audio_file_path):
                chat_response = f"Response based on the prompt: {prompt}"  # Replace with actual logic if needed
                tts = gTTS(text=chat_response, lang='uk')
                tts.save(audio_file_path)

            return FileResponse(open(audio_file_path, 'rb'), content_type='audio/mp3')

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired!')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token!')
        except Exception as e:
            return JsonResponse({"error": f"Error generating audio: {str(e)}"}, status=500)