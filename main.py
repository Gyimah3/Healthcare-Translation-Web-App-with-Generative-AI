# main.py
import queue
from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import assemblyai as aai
from elevenlabs import stream
from elevenlabs.client import ElevenLabs
from openai import OpenAI
import os
import json
import logging
from datetime import datetime
import asyncio

# Load environment variables
from dotenv import load_dotenv
import uvicorn
load_dotenv()
from library.config import settings
# Configure logging
from loguru import logger

# Initialize API clients and keys
ASSEMBLY_AI_API_KEY = settings.assembly_ai_api_key
OPENAI_API_KEY = settings.openai_api_key
ELEVENLABS_API_KEY = settings.elevenlabs_api_key

aai.settings.api_key = ASSEMBLY_AI_API_KEY
openai_client = OpenAI(api_key=OPENAI_API_KEY)
elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)


# Language mapping between frontend codes and backend API codes -> this should be database in the future
LANGUAGE_MAPPING = {
    'en-US': {'assembly': 'en_us', 'openai': 'english', 'display': 'EN-US'},
    'en-GB': {'assembly': 'en_gb', 'openai': 'english', 'display': 'EN-GB'},
    'en-AU': {'assembly': 'en_au', 'openai': 'english', 'display': 'EN-AU'},
    'en-CA': {'assembly': 'en_ca', 'openai': 'english', 'display': 'EN-CA'},
    'ja': {'assembly': 'ja', 'openai': 'japanese', 'display': 'JA'},
    'zh': {'assembly': 'zh', 'openai': 'chinese', 'display': 'ZH'},
    'de': {'assembly': 'de', 'openai': 'german', 'display': 'DE'},
    'hi': {'assembly': 'hi', 'openai': 'hindi', 'display': 'HI'},
    'fr-FR': {'assembly': 'fr_fr', 'openai': 'french', 'display': 'FR-FR'},
    'fr-CA': {'assembly': 'fr_ca', 'openai': 'french', 'display': 'FR-CA'},
    'ko': {'assembly': 'ko', 'openai': 'korean', 'display': 'KO'},
    'pt-BR': {'assembly': 'pt_br', 'openai': 'portuguese', 'display': 'PT-BR'},
    'pt-PT': {'assembly': 'pt_pt', 'openai': 'portuguese', 'display': 'PT-PT'},
    'it': {'assembly': 'it', 'openai': 'italian', 'display': 'IT'},
    'es-ES': {'assembly': 'es_es', 'openai': 'spanish', 'display': 'ES-ES'},
    'es-MX': {'assembly': 'es_mx', 'openai': 'spanish', 'display': 'ES-MX'},
    'nl': {'assembly': 'nl', 'openai': 'dutch', 'display': 'NL'},
    'tr': {'assembly': 'tr', 'openai': 'turkish', 'display': 'TR'},
    'pl': {'assembly': 'pl', 'openai': 'polish', 'display': 'PL'},
    'fi': {'assembly': 'fi', 'openai': 'finnish', 'display': 'FI'},
    'uk': {'assembly': 'uk', 'openai': 'ukrainian', 'display': 'UK'},
    'ru': {'assembly': 'ru', 'openai': 'russian', 'display': 'RU'}
}

app = FastAPI()
@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Render the home page."""
    return 'server is running'#--->>> uncomment this to use the small templatebtemplates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws/medical-translator")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_running_loop()
    
    transcriber = None
    transcriber_task = None
    # Instead of a microphone stream, we create a thread-safe queue
    audio_queue = queue.Queue()  # ->>>> This will hold audio byte chunks from the frontend

    source_language = "en-US"
    target_language = "es-ES"
    conversation_history = []

    #-->> synchronous generator that yields audio chunks from the queue
    def audio_generator():
        while True:
            # --->>>blocking until a chunk is available
            chunk = audio_queue.get()  
            if chunk is None:
                break
            yield chunk

    async def process_transcript(text, is_final=False):
        if not text:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        if is_final:
            logger.info(f"[{timestamp}] TRANSCRIPT: {text}")
            await websocket.send_json({
                "type": "transcript",
                "text": text,
                "is_final": True
            })
            conversation_history.append({"role": "user", "content": text})
            
            source_code = LANGUAGE_MAPPING[source_language]['openai']
            target_code = LANGUAGE_MAPPING[target_language]['openai']
            system_prompt = (
                f"You are a medical translator. Translate the following from {source_code} "
                f"to {target_code}. Focus on medical terminology accuracy. Only respond with the translation."
            )
            
            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.3
                )
                translation = response.choices[0].message.content
                logger.info(f"[{timestamp}] TRANSLATION: {translation}")
                await websocket.send_json({
                    "type": "translation",
                    "text": translation
                })
                conversation_history.append({"role": "assistant", "content": translation})
            except Exception as e:
                logger.error(f"Translation error: {str(e)}")
                await websocket.send_json({
                    "type": "error", 
                    "message": f"Translation error: {str(e)}"
                })
        else:
            await websocket.send_json({
                "type": "transcript",
                "text": text,
                "is_final": False
            })

    try:
        # Wait for initial configuration from client
        config_data = await websocket.receive_json()
        source_language = config_data.get('source_language', source_language)
        target_language = config_data.get('target_language', target_language)
        logger.info(f"Initialized languages: {source_language} → {target_language}")
        logger.info(f"information in config_data: {config_data}")
        
        while True:
            message = await websocket.receive()
            
            if message["type"] == "websocket.receive":
                if "bytes" in message:
                    # Audio data received as binary
                    audio_chunk = message["bytes"]
                    logger.info(f"Received audio chunk: {len(audio_chunk)} bytes, first 20 bytes: {audio_chunk[:20]}")
                    audio_queue.put(audio_chunk)
                elif "text" in message:
                    data = json.loads(message["text"])
                    logger.info(f"Received command: {data}")
                    command = data.get("command")
                    
                    if command == "start_listening":
                        if transcriber_task:
                            transcriber_task.cancel()
                            transcriber_task = None
                        if transcriber:
                            transcriber.close()
                            transcriber = None

                        transcriber = aai.RealtimeTranscriber(
                            sample_rate=16000,
                            on_data=lambda t: asyncio.run_coroutine_threadsafe(
                                process_transcript(t.text, isinstance(t, aai.RealtimeFinalTranscript)),
                                loop
                            ),
                            on_error=lambda e: logger.error(f"Transcription error: {str(e)}"),
                            on_open=lambda s: logger.info(f"Session opened: {s.session_id}"),
                            on_close=lambda: logger.info("Session closed"),
                            end_utterance_silence_threshold=1000
                        )
                        transcriber.connect()
                        transcriber_task = asyncio.create_task(
                            asyncio.to_thread(transcriber.stream, audio_generator())
                        )
                        await websocket.send_json({"type": "listening_started"})
                        logger.info("Started listening .with audio from WebSocket")
                    
                    
                    elif command == "stop_listening":
                        if transcriber_task:
                            transcriber_task.cancel()
                            transcriber_task = None
                        if transcriber:
                            transcriber.close()
                            transcriber = None
                        await websocket.send_json({"type": "listening_stopped"})
                        logger.info("Stopped listening")
                    
                    elif command == "speak":
                        text = data.get("text")
                        if text:
                            try:
                                await websocket.send_json({"type": "audio_starting"})
                                voice_id = "EXAVITQu4vr4xnSDxMaL"  #->>>  voice ID (Alice)
                                response = elevenlabs_client.text_to_speech.convert_as_stream(
                                    text=text,
                                    voice_id=voice_id,
                                    model_id="eleven_turbo_v2"
                                )
                                audio_data = b"".join(response)
                                import base64
                                audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                                await websocket.send_json({
                                    "type": "audio_data",
                                    "data": audio_b64
                                })
                                await websocket.send_json({"type": "audio_completed"})
                            except Exception as e:
                                logger.error(f"Audio error: {str(e)}")
                                await websocket.send_json({
                                    "type": "error",
                                    "message": f"Audio error: {str(e)}"
                                })
                    
                    elif command == "update_languages":
                        source_language = data.get('source_language', source_language)
                        target_language = data.get('target_language', target_language)
                        conversation_history = []
                        await websocket.send_json({
                            "type": "languages_updated",
                            "source_language": source_language,
                            "target_language": target_language
                        })
                        logger.info(f"Updated languages: {source_language} → {target_language}")
                    
                    elif command == "ping":
                        await websocket.send_json({"type": "pong"})
            
            # --->>>ignoring other message types

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        if transcriber:
            transcriber.close()
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        if transcriber:
            transcriber.close()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port= 8000, reload=True, log_level="debug")