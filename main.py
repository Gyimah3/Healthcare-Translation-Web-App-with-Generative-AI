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
from library.config import settings

from dotenv import load_dotenv
load_dotenv()

from loguru import logger

# Initialize API clients and keys
ASSEMBLY_AI_API_KEY = settings.assembly_ai_api_key
OPENAI_API_KEY = settings.openai_api_key
ELEVENLABS_API_KEY = settings.elevenlabs_api_key

aai.settings.api_key = ASSEMBLY_AI_API_KEY
openai_client = OpenAI(api_key=OPENAI_API_KEY)
elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Initialize FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Render the home page."""
    return 'server is running'#templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/medical-translator")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_running_loop() 
    
    transcriber = None
    transcriber_task = None  
    microphone_stream = None
    source_language = "en-US"
    target_language = "es-ES"
    conversation_history = []
    session_translation = ""  # Accumulates all final translations -> will USE REDIS IN THE FUTURE

    async def process_transcript(text, is_final=False):
        nonlocal session_translation
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
                session_translation += translation + " "  # Accumulate
                # Sending... both the individual translation and the full accumulated transcript
                await websocket.send_json({
                    "type": "translation",
                    "text": translation,
                    "full_translation": session_translation
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
        # Waiting for initial configuration from frontend as a default
        config_data = await websocket.receive_json()
        source_language = config_data.get('source_language', source_language)
        target_language = config_data.get('target_language', target_language)
        logger.info(f"Initialized languages: {source_language} → {target_language}")
        logger.info(f"information in config_data: {config_data}")
        
        while True:
            message = await websocket.receive_json()
            logger.info(f"Received message: {message}")
            command = message.get("command")

            if command == "start_listening":
                # Reset accumulator on new session-> new conversation with language preference
                session_translation = ""
                if transcriber_task:
                    transcriber_task.cancel()
                    transcriber_task = None
                if transcriber:
                    transcriber.close()
                    transcriber = None

                assembly_lang = LANGUAGE_MAPPING[source_language]['assembly']
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
                microphone_stream = aai.extras.MicrophoneStream(sample_rate=16000)
                transcriber_task = asyncio.create_task(
                    asyncio.to_thread(transcriber.stream, microphone_stream)
                )
                await websocket.send_json({"type": "listening_started"})
                logger.info(f"Started listening in {assembly_lang}")

            elif command == "stop_listening":
                if transcriber_task:
                    transcriber_task.cancel()
                    transcriber_task = None
                if transcriber:
                    # transcriber.close() to avoid server disconnection
                    transcriber = None
                if microphone_stream:
                    microphone_stream.close()
                    microphone_stream = None
                await websocket.send_json({"type": "listening_stopped"})
                logger.info("Stopped listening")

            elif command == "speak":
                text = message.get("text")
                if text:
                    # Stopping listening during audio playback so that playback is not re-captured
                    if transcriber_task:
                        transcriber_task.cancel()
                        transcriber_task = None
                    if transcriber:
                        transcriber.close()
                        transcriber = None
                    if microphone_stream:
                        microphone_stream.close()
                        microphone_stream = None
                    try:
                        await websocket.send_json({"type": "audio_starting"})
                        voice_id = "EXAVITQu4vr4xnSDxMaL"  # Rachel voice ID from elevenlabs -> we can change it based on our needs
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
                    # Note: resuming listening after playback, have the client send a new "start_listening" command.
                    
            elif command == "update_languages":
                source_language = message.get('source_language', source_language)
                target_language = message.get('target_language', target_language)
                conversation_history = []
                session_translation = ""  #--->>> resetting accumulated translation
                await websocket.send_json({
                    "type": "languages_updated",
                    "source_language": source_language,
                    "target_language": target_language
                })
                logger.info(f"Updated languages: {source_language} → {target_language}")

            elif command == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        if transcriber:
            transcriber.close()
        if microphone_stream:
            microphone_stream.close()
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        if transcriber:
            transcriber.close()
        if microphone_stream:
            microphone_stream.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
