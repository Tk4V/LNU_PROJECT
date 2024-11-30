import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import base64
import io
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize FastAPI app
app = FastAPI()

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Define Pydantic model for the request body
class ItemRequest(BaseModel):
    prompt: str  # Accepts a field named "prompt" in the JSON body

@app.post("/items/")
def create_item(item: ItemRequest):
    # Extract the prompt from the received JSON body
    prompt = item.prompt
    
    # Call OpenAI's Chat API for completion
    completion = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": f"""відповідай дуже коротко до 20 слів,
                    Ти мені повинен довомогти вивчитати мови,
                     ось що я тебе прошу (Відповідай та тій мові яка іде далі):
                     {prompt}""",
            },
        ],
    )

    # Extract the chat response
    chat_response = completion.choices[0].message.content
    
    # Call OpenAI's Text-to-Speech (TTS) API to generate audio from text
    response = openai.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=f"{chat_response}",
    )

    # Save the audio response to a file
    response.stream_to_file("output.mp3")
    
    # Read the file and encode it as base64
    with open("output.mp3", "rb") as file:
        file_data = file.read()

    mp3_base64 = base64.b64encode(file_data).decode("utf-8")

    # Return the response as JSON
    return {
        "answer": chat_response,
        "category": "new",
        "date": datetime.now(),
        "voice": mp3_base64,
    }
