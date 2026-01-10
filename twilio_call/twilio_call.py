import os
import json
from dotenv import load_dotenv
from flask import Flask, request
from flask_sock import Sock
from pyngrok import ngrok
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Start
import threading
from openai import OpenAI
import asyncio
import websockets
from elevenlabs import ElevenLabs
import uuid

load_dotenv()

#########################################
# AI-Powered Restaurant Reservation Call
# Uses Twilio + OpenAI Realtime API + ElevenLabs
#########################################

# Initialize Flask app
app = Flask(__name__)
sock = Sock(app)

# Configuration
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone = os.getenv("FROM_TWILIO_PHONE_NUMBER", "+14156970481")
to_phone = os.getenv("TO_PHONE_NUMBER", "+34610515020")
openai_api_key = os.getenv("OPENAI_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

twilio_client = Client(account_sid, auth_token)
openai_client = OpenAI(api_key=openai_api_key)
elevenlabs_client = ElevenLabs(api_key=elevenlabs_api_key)

# Reservation persona system prompt
RESERVATION_SYSTEM_PROMPT = """TÚ ERES: Ana Román, una cliente que está llamando a un restaurante para hacer una reserva.

TÚ NO ERES: El personal del restaurante. NO preguntes "¿en qué puedo ayudarte?" ni actúes como si trabajaras allí.

SITUACIÓN ACTUAL: Acabas de llamar al restaurante y el personal ha contestado el teléfono.

PRIMERA RESPUESTA (cuando el restaurante te salude con "Hola", "Dígame", etc.):
Di algo como: "Hola, buenos días/tardes. Llamaba para hacer una reserva para dos personas. ¿Sería posible para mañana a las siete de la tarde?"

CONVERSACIÓN:
- Cuando te pregunten detalles, responde claramente
- Nombre: Ana Román
- Teléfono: Cuando des tu número, díctalo DESPACIO con pausas: "seis cero cero... uno dos tres... cuatro cinco seis"
- Número de personas: 2
- Fecha/hora: Sugiere "mañana a las 7 de la tarde" o similar
- Si te ofrecen otro horario, acepta o negocia educadamente
- Al final, confirma los detalles y agradece

REGLAS CRÍTICAS:
- TÚ ERES LA CLIENTE que llama, NO el restaurante
- NUNCA preguntes "¿en qué puedo ayudarte?"
- NUNCA actúes como personal del restaurante
- Habla SIEMPRE en español
- Sé breve y natural
- Responde solo a lo que te preguntan

EJEMPLO CORRECTO:
Restaurante: "Hola"
Tú: "Hola, buenas tardes. Quería hacer una reserva para dos personas para mañana a las siete de la tarde, ¿sería posible?"

EJEMPLO INCORRECTO:
Restaurante: "Hola"
Tú: "Hola, ¿en qué puedo ayudarte?" ← ¡NUNCA HAGAS ESTO!"""


# Health check endpoint
@app.route("/", methods=["GET"])
def health():
    """Health check endpoint"""
    return "Restaurant Reservation AI Ready", 200


@app.route("/test-openai", methods=["GET"])
def test_openai():
    """Test OpenAI API key and Realtime API connection"""
    import asyncio

    # Print the full URL to console
    print("\n" + "=" * 70)
    print("🔗 TEST ENDPOINT URL:")
    print(f"   https://{request.host}/test-openai")
    print("=" * 70 + "\n")

    async def test_connection():
        try:
            print(f"[TEST] Testing OpenAI connection...")
            print(
                f"[TEST] API Key prefix: {openai_api_key[:20]}..."
                if openai_api_key
                else "[TEST] API Key: NOT SET"
            )

            # Try to connect to OpenAI Realtime API
            ws = await websockets.connect(
                "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17",
                additional_headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "OpenAI-Beta": "realtime=v1",
                },
            )

            print("[TEST] Connected successfully!")

            # Wait for session.created event
            message = await ws.recv()
            data = json.loads(message)
            print(f"[TEST] Received event: {data.get('type')}")

            await ws.close()

            return {
                "status": "✅ SUCCESS",
                "api_key_prefix": (
                    openai_api_key[:20] + "..." if openai_api_key else "NOT SET"
                ),
                "first_event": data.get("type"),
                "session_id": data.get("session", {}).get("id", "unknown"),
                "message": "OpenAI Realtime API connection works!",
            }
        except Exception as e:
            print(f"[TEST] Error: {e}")
            import traceback

            traceback.print_exc()
            return {
                "status": "❌ ERROR",
                "error": str(e),
                "error_type": type(e).__name__,
                "api_key_prefix": (
                    openai_api_key[:20] + "..." if openai_api_key else "NOT SET"
                ),
            }

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(test_connection())
    loop.close()

    return result, 200


# Webhook endpoint for Twilio - initiates the call
@app.route("/voice", methods=["GET", "POST"])
def voice():
    """Respond to incoming calls - CORRECT ConversationRelay implementation"""
    from twilio.twiml.voice_response import Connect, ConversationRelay

    response = VoiceResponse()
    connect = Connect()

    # ConversationRelay connects to OUR WebSocket server (not OpenAI directly!)
    # Twilio handles STT/TTS automatically, we just do text-to-text with OpenAI Chat API
    host = request.host
    conversation_relay = ConversationRelay(
        url=f"wss://{host}/conversation-ws",
        # No welcome greeting - let the restaurant speak first, then AI responds
        language="es-ES",  # Spanish language for STT and TTS
        tts_provider="elevenlabs",  # Use ElevenLabs for TTS
        voice=elevenlabs_voice_id,  # Voice ID from .env file
        dtmf_detection=False,
    )

    connect.append(conversation_relay)
    response.append(connect)

    # Log the TwiML for debugging
    twiml_str = str(response)
    print(f"[DOC] ConversationRelay (CORRECT):\n{twiml_str}")

    return twiml_str, 200, {"Content-Type": "application/xml"}


# WebSocket endpoint for ConversationRelay
@sock.route("/conversation-ws")
def conversation_websocket(ws):
    """
    WebSocket handler for Twilio ConversationRelay
    Twilio sends TEXT prompts (already transcribed) and expects TEXT responses
    Twilio handles all audio conversion (STT/TTS)
    """
    print("\n" + "=" * 70)
    print("[CONVERSATION] ConversationRelay WebSocket connected")
    print("=" * 70 + "\n")

    call_sid = None

    try:
        message_count = 0
        while True:
            try:
                # Add timeout to prevent blocking forever (increased to 60s)
                message_raw = ws.receive(timeout=60)
                message_count += 1
                print(f"[CR] Received message #{message_count}")
                if message_raw is None:
                    print("[CR] WebSocket received None - connection closed")
                    break

                print(
                    f"[CR] Raw message: {message_raw[:200]}..."
                )  # Log first 200 chars
                message = json.loads(message_raw)
                message_type = message.get("type")

                print(f"[CR] Received message type: {message_type}")
            except Exception as recv_error:
                print(f"[X] Error receiving message: {recv_error}")
                # Check if it's a timeout - if so, continue waiting
                if "timeout" in str(recv_error).lower():
                    print("[CR] Receive timeout - continuing to wait for messages...")
                    continue
                else:
                    # Other error - break
                    break

            if message_type == "setup":
                # Initial setup message from Twilio
                call_sid = message.get("callSid")
                print(f"[CR] Setup for call: {call_sid}")

                # Initialize conversation history
                conversation_sessions[call_sid] = [
                    {"role": "system", "content": RESERVATION_SYSTEM_PROMPT}
                ]

            elif message_type == "prompt":
                # User spoke - Twilio already converted speech to text
                voice_prompt = message.get("voicePrompt", "")
                print(f"[CR] User said: {voice_prompt}")

                if call_sid and call_sid in conversation_sessions:
                    # Add user message to conversation
                    conversation_sessions[call_sid].append(
                        {"role": "user", "content": voice_prompt}
                    )

                    # Log conversation
                    log_conversation("Restaurant", voice_prompt)

                    # Call OpenAI Chat API (text-to-text)
                    print("[CR] Calling OpenAI Chat API...")
                    try:
                        completion = openai_client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=conversation_sessions[call_sid],
                        )

                        ai_response = completion.choices[0].message.content

                        if not ai_response:
                            ai_response = "Lo siento, no pude generar una respuesta."

                        print(f"[CR] AI response: {ai_response}")

                        # Add AI response to conversation
                        conversation_sessions[call_sid].append(
                            {"role": "assistant", "content": ai_response}
                        )

                        # Log conversation
                        log_conversation("AI", ai_response)

                        # Send TEXT response back to Twilio as single message (like reference implementation)
                        # Twilio will convert it to speech automatically
                        response_message = {
                            "type": "text",
                            "token": ai_response,
                            "last": True,
                        }
                        ws.send(json.dumps(response_message))
                        print(f"[CR] Response sent - waiting for next message...")

                    except Exception as e:
                        print(f"[X] Error calling OpenAI: {e}")
                        import traceback

                        traceback.print_exc()
                        error_response = {
                            "type": "text",
                            "token": "Lo siento, hubo un error. ¿Puedes repetir?",
                            "last": True,
                            "interruptible": True,
                            "preemptible": False,
                        }
                        ws.send(json.dumps(error_response))

            elif message_type == "interrupt":
                # User interrupted the AI - log and continue
                utterance = message.get("utteranceUntilInterrupt", "")
                print(f"[CR] User interrupted (partial: '{utterance}')")
                # The conversation history is already correct, just wait for next prompt

            elif message_type == "error":
                # ConversationRelay error
                error_msg = message.get("description", "Unknown error")
                print(f"[CR] Error from Twilio: {error_msg}")

            else:
                # Unknown message type
                print(f"[CR] Unknown message type: {message_type}")
                print(f"[CR] Full message: {json.dumps(message, indent=2)}")

    except Exception as e:
        print(f"[X] WebSocket error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Clean up session
        if call_sid and call_sid in conversation_sessions:
            del conversation_sessions[call_sid]
        print("[CR] WebSocket closed")


# Store conversation sessions for ConversationRelay
conversation_sessions = {}

# Store active call SID, AI response queue, and server host
active_call_sid = None
ai_response_text = ""
ai_audio_file = None
server_host = None

# Conversation transcript storage
conversation_transcript = []

# Create directory for temporary audio files
import os

AUDIO_DIR = "temp_audio"
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)


def log_conversation(speaker, message):
    """Log conversation with timestamp"""
    from datetime import datetime

    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
    entry = {"timestamp": timestamp, "speaker": speaker, "message": message}
    conversation_transcript.append(entry)

    # Print formatted transcript line
    speaker_label = "[AI]" if speaker == "AI" else "[RESTAURANT]"
    print(f"\n{'='*70}")
    print(f"{timestamp} {speaker_label}: {message}")
    print(f"{'='*70}\n")


# Endpoint to serve audio files
@app.route("/audio/<filename>")
def serve_audio(filename):
    """Serve generated audio files"""
    from flask import send_from_directory

    return send_from_directory(AUDIO_DIR, filename)


# Endpoint to serve TwiML for AI response playback
@app.route("/ai-response", methods=["POST"])
def ai_response():
    """Serve TwiML to play AI response using <Play> with ElevenLabs audio"""
    global ai_response_text, ai_audio_file
    from twilio.twiml.voice_response import Stream
    from datetime import datetime

    twiml_start = datetime.now()
    print(
        f"[TWIML] /ai-response endpoint called at {twiml_start.strftime('%H:%M:%S.%f')[:-3]}"
    )

    response = VoiceResponse()

    # Use Twilio's built-in TTS for INSTANT playback (no download delay)
    if ai_response_text:
        print(f"[PLAY] Using Twilio TTS (alice voice): {ai_response_text[:50]}...")
        # Using alice voice with Spanish - should play instantly
        response.say(ai_response_text, voice="alice", language="es-ES")
        ai_response_text = ""  # Clear after use
        ai_audio_file = None  # Clear any pending file
    elif ai_audio_file:
        # Fallback to file if needed
        audio_url = f"https://{request.host}/audio/{ai_audio_file}"
        print(f"[PLAY] Playing audio file: {audio_url}")
        response.play(audio_url)
        ai_audio_file = None

    # Reconnect to media stream
    host = request.host
    start = Start()
    stream = Stream(url=f"wss://{host}/media-stream", track="both_tracks")
    start.append(stream)
    response.append(start)

    # Keep call alive
    response.pause(length=3600)

    return str(response), 200, {"Content-Type": "application/xml"}


# Simplified WebSocket relay for OpenAI with audio playback via Twilio API
@sock.route("/simple-relay")
def simple_relay(ws):
    """
    Simple relay: Twilio audio -> OpenAI, OpenAI audio -> Save to file -> Play via Twilio API
    This avoids the complexity of bidirectional WebSocket audio streaming
    """
    print("\n" + "=" * 70)
    print("[RELAY] Simple relay connected")
    print("=" * 70 + "\n")

    stream_sid = None
    call_sid = None
    global active_call_sid, server_host

    # Store server host for generating URLs
    server_host = request.host

    # Use asyncio for OpenAI WebSocket
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def handle_call():
        nonlocal stream_sid, call_sid
        openai_ws = None

        try:
            # Connect to OpenAI
            print("[OPENAI] Connecting...")
            openai_ws = await websockets.connect(
                "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17",
                additional_headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "OpenAI-Beta": "realtime=v1",
                },
            )
            print("[OK] Connected to OpenAI")

            # Configure session for audio input and output
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": RESERVATION_SYSTEM_PROMPT,
                    "voice": "alloy",
                    "input_audio_format": "g711_ulaw",
                    "output_audio_format": "g711_ulaw",
                    "input_audio_transcription": {"model": "whisper-1"},
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.3,  # Lower = more sensitive
                        "prefix_padding_ms": 100,  # Less padding before speech
                        "silence_duration_ms": 300,  # Shorter silence needed to detect end
                    },
                    "temperature": 0.8,
                },
            }
            await openai_ws.send(json.dumps(session_config))
            print("[OK] Session configured for audio I/O")

            # Handle OpenAI responses
            async def handle_openai_events():
                nonlocal call_sid
                audio_buffer = b""
                collecting_audio = False

                try:
                    async for message in openai_ws:
                        data = json.loads(message)
                        event_type = data.get("type")

                        # Log ALL events for debugging
                        if event_type not in [
                            "response.audio.delta",
                            "input_audio_buffer.append",
                        ]:
                            print(f"[EVENT] {event_type}")

                        if event_type == "session.created":
                            print(f"[OK] Session: {data.get('session', {}).get('id')}")
                        elif event_type == "session.updated":
                            print("[OK] Session updated")
                        elif event_type == "input_audio_buffer.speech_started":
                            print("[SPEECH] Restaurant speaking!")
                        elif event_type == "input_audio_buffer.speech_stopped":
                            print("[QUIET] Speech stopped")
                        elif event_type == "response.created":
                            print("[AI] Generating response...")
                            audio_buffer = b""
                            collecting_audio = True
                        elif event_type == "response.audio.delta":
                            # Collect audio chunks
                            if collecting_audio:
                                import base64

                                audio_chunk = base64.b64decode(data.get("delta", ""))
                                audio_buffer += audio_chunk
                                if (
                                    len(audio_buffer) % 1000 < 200
                                ):  # Log every ~1000 bytes
                                    print(
                                        f"[AUDIO] Collected {len(audio_buffer)} bytes so far...",
                                        end="\r",
                                    )
                        elif event_type == "response.audio.done":
                            collecting_audio = False
                            print(
                                f"\n[OK] Collected {len(audio_buffer)} bytes of audio"
                            )

                            # Send audio back through WebSocket
                            if len(audio_buffer) > 0 and stream_sid:
                                import base64

                                # Clear any outbound audio first
                                try:
                                    ws.send(
                                        json.dumps(
                                            {"event": "clear", "streamSid": stream_sid}
                                        )
                                    )
                                    print("[OK] Cleared outbound buffer")
                                except Exception as e:
                                    print(f"[X] Error clearing: {e}")

                                # Send audio in 160-byte chunks (20ms of ulaw audio)
                                CHUNK_SIZE = 160
                                chunks_sent = 0

                                for i in range(0, len(audio_buffer), CHUNK_SIZE):
                                    chunk = audio_buffer[i : i + CHUNK_SIZE]

                                    # Pad last chunk if needed
                                    if len(chunk) < CHUNK_SIZE:
                                        chunk += b"\xff" * (CHUNK_SIZE - len(chunk))

                                    # Base64 encode and send
                                    encoded = base64.b64encode(chunk).decode("utf-8")
                                    media_msg = {
                                        "event": "media",
                                        "streamSid": stream_sid,
                                        "media": {"payload": encoded},
                                    }

                                    try:
                                        ws.send(json.dumps(media_msg))
                                        chunks_sent += 1
                                    except Exception as e:
                                        print(f"[X] Error sending chunk: {e}")
                                        break

                                print(f"[OK] Sent {chunks_sent} audio chunks to caller")

                                # Send mark to indicate playback complete
                                try:
                                    ws.send(
                                        json.dumps(
                                            {
                                                "event": "mark",
                                                "streamSid": stream_sid,
                                                "mark": {"name": "audio_complete"},
                                            }
                                        )
                                    )
                                except Exception as e:
                                    print(f"[X] Error sending mark: {e}")

                        elif event_type == "response.audio_transcript.done":
                            transcript = data.get("transcript", "")
                            if transcript:
                                log_conversation("AI", transcript)
                        elif (
                            event_type
                            == "conversation.item.input_audio_transcription.completed"
                        ):
                            transcript = data.get("transcript", "")
                            if transcript:
                                log_conversation("Restaurant", transcript)
                        elif event_type == "error":
                            print(f"[X] OpenAI error: {data.get('error')}")

                except Exception as e:
                    print(f"[X] OpenAI event error: {e}")

            # Start OpenAI event handler
            openai_task = asyncio.create_task(handle_openai_events())

            # Handle Twilio messages
            while True:
                message = ws.receive(timeout=0.1)
                if message is None:
                    await asyncio.sleep(0.01)
                    continue

                data = json.loads(message)
                event = data.get("event")

                if event == "start":
                    stream_sid = data["start"]["streamSid"]
                    call_sid = data["start"]["callSid"]
                    active_call_sid = call_sid
                    print(f"[OK] Stream started: {stream_sid}")
                    print(f"[OK] Call SID: {call_sid}")

                elif event == "media":
                    # Forward audio to OpenAI
                    audio_append = {
                        "type": "input_audio_buffer.append",
                        "audio": data["media"]["payload"],
                    }
                    await openai_ws.send(json.dumps(audio_append))

                elif event == "stop":
                    print("[STOP] Stream stopped")
                    break

        except Exception as e:
            print(f"[X] Relay error: {e}")
            import traceback

            traceback.print_exc()
        finally:
            if openai_ws:
                await openai_ws.close()
            print("[OK] Relay closed")

    try:
        loop.run_until_complete(handle_call())
    finally:
        loop.close()


# NEW: Properly configured OpenAI relay for Connect+Stream
@sock.route("/openai-configured-relay")
def openai_configured_relay(ws):
    """
    Relay for Connect+Stream with proper OpenAI configuration
    This is the FINAL attempt - uses Connect+Stream bidirectional audio
    """
    print("\n" + "=" * 70)
    print("[RELAY] OpenAI Configured Relay Connected")
    print("=" * 70 + "\n")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def handle_relay():
        openai_ws = None
        twilio_stream_sid = None

        try:
            # Connect to OpenAI
            print("[OPENAI] Connecting to Realtime API...")
            openai_ws = await websockets.connect(
                "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17",
                additional_headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "OpenAI-Beta": "realtime=v1",
                },
            )
            print("[OK] Connected to OpenAI")

            # Wait for session.created and configure
            first_msg = await openai_ws.recv()
            session_data = json.loads(first_msg)
            print(f"[OK] Session created: {session_data.get('session', {}).get('id')}")

            # Send session configuration
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": RESERVATION_SYSTEM_PROMPT,
                    "voice": "alloy",
                    "input_audio_format": "g711_ulaw",
                    "output_audio_format": "g711_ulaw",
                    "input_audio_transcription": {"model": "whisper-1"},
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.3,
                        "prefix_padding_ms": 100,
                        "silence_duration_ms": 300,
                    },
                    "temperature": 0.8,
                },
            }
            await openai_ws.send(json.dumps(session_config))
            print("[OK] Session configured")

            # Handle bidirectional relay
            async def twilio_to_openai():
                """Forward audio from Twilio to OpenAI"""
                nonlocal twilio_stream_sid
                while True:
                    try:
                        message = ws.receive(timeout=0.1)
                        if not message:
                            await asyncio.sleep(0.01)
                            continue

                        data = json.loads(message)
                        event = data.get("event")

                        if event == "start":
                            twilio_stream_sid = data["start"]["streamSid"]
                            print(f"[OK] Twilio stream started: {twilio_stream_sid}")
                        elif event == "media":
                            # Forward to OpenAI
                            await openai_ws.send(
                                json.dumps(
                                    {
                                        "type": "input_audio_buffer.append",
                                        "audio": data["media"]["payload"],
                                    }
                                )
                            )
                        elif event == "stop":
                            print("[STOP] Twilio stream stopped")
                            break
                    except Exception as e:
                        if "timeout" not in str(e).lower():
                            print(f"[X] Twilio->OpenAI error: {e}")
                            break

            async def openai_to_twilio():
                """Forward audio and events from OpenAI back to Twilio"""
                nonlocal twilio_stream_sid
                audio_chunks_sent = 0
                import time

                response_start_time = None

                try:
                    async for message in openai_ws:
                        data = json.loads(message)
                        event_type = data.get("type")

                        # Log ALL events for debugging
                        if event_type not in ["response.audio.delta"]:
                            print(f"[OPENAI] {event_type}")

                        if event_type == "session.updated":
                            print("[OK] Session updated with config")
                        elif event_type == "input_audio_buffer.speech_started":
                            print("[SPEECH] Restaurant speaking!")
                        elif event_type == "input_audio_buffer.speech_stopped":
                            print("[QUIET] Restaurant stopped speaking")
                        elif event_type == "response.created":
                            response_start_time = time.time()
                            audio_chunks_sent = 0
                            print("[AI] Response generation started...")
                        elif event_type == "response.audio.delta":
                            if twilio_stream_sid:
                                # Send audio back to Twilio via WebSocket
                                ws.send(
                                    json.dumps(
                                        {
                                            "event": "media",
                                            "streamSid": twilio_stream_sid,
                                            "media": {"payload": data.get("delta", "")},
                                        }
                                    )
                                )
                                audio_chunks_sent += 1
                                if audio_chunks_sent == 1:
                                    elapsed = (
                                        time.time() - response_start_time
                                        if response_start_time
                                        else 0
                                    )
                                    print(
                                        f"[AUDIO] First audio chunk sent to Twilio! (after {elapsed:.2f}s)"
                                    )
                                elif audio_chunks_sent % 50 == 0:
                                    print(
                                        f"[AUDIO] Sent {audio_chunks_sent} chunks...",
                                        end="\r",
                                    )
                            else:
                                print("[WARNING] Got audio but no stream_sid!")
                        elif event_type == "response.audio.done":
                            elapsed = (
                                time.time() - response_start_time
                                if response_start_time
                                else 0
                            )
                            print(
                                f"\n[OK] Audio complete: {audio_chunks_sent} chunks sent in {elapsed:.2f}s"
                            )
                        elif event_type == "response.audio_transcript.done":
                            transcript = data.get("transcript", "")
                            if transcript:
                                log_conversation("AI", transcript)
                        elif (
                            event_type
                            == "conversation.item.input_audio_transcription.completed"
                        ):
                            transcript = data.get("transcript", "")
                            if transcript:
                                log_conversation("Restaurant", transcript)

                except Exception as e:
                    print(f"[X] OpenAI->Twilio error: {e}")

            # Run both directions concurrently
            await asyncio.gather(twilio_to_openai(), openai_to_twilio())

        except Exception as e:
            print(f"[X] Relay error: {e}")
            import traceback

            traceback.print_exc()
        finally:
            if openai_ws:
                await openai_ws.close()
            print("[OK] Relay closed")

    try:
        loop.run_until_complete(handle_relay())
    finally:
        loop.close()


# WebSocket relay handler for Connect+Stream (bidirectional audio)
@sock.route("/openai-relay")
def openai_relay(ws):
    """
    Relay audio between Twilio Connect+Stream and OpenAI Realtime API
    Connect+Stream properly supports bidirectional audio unlike Start+Stream
    """
    print("\n" + "=" * 70)
    print("[RELAY] Twilio Connect+Stream connected")
    print("=" * 70 + "\n")

    # Flask-Sock handles WebSocket synchronously, but we need async for OpenAI
    # We'll use a thread to run the async relay
    import threading
    import queue

    twilio_queue = queue.Queue()
    openai_queue = queue.Queue()

    def async_relay_thread():
        """Run the async relay in a separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def relay_audio():
            openai_ws = None
            stream_sid = None
            try:
                # Connect to OpenAI
                print("[OPENAI] Connecting to Realtime API...")
                openai_ws = await websockets.connect(
                    "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17",
                    additional_headers={
                        "Authorization": f"Bearer {openai_api_key}",
                        "OpenAI-Beta": "realtime=v1",
                    },
                )
                print("[OK] Connected to OpenAI")

                # Configure session with input transcription enabled
                session_config = {
                    "type": "session.update",
                    "session": {
                        "modalities": ["text", "audio"],
                        "instructions": RESERVATION_SYSTEM_PROMPT,
                        "voice": "alloy",
                        "input_audio_format": "g711_ulaw",
                        "output_audio_format": "g711_ulaw",
                        "input_audio_transcription": {"model": "whisper-1"},
                        "turn_detection": {
                            "type": "server_vad",
                            "threshold": 0.5,
                            "prefix_padding_ms": 300,
                            "silence_duration_ms": 500,
                        },
                        "temperature": 0.8,
                    },
                }
                await openai_ws.send(json.dumps(session_config))
                print("[OK] Session configured")

                # Handle incoming from Twilio (via queue)
                async def twilio_to_openai():
                    """Forward audio from Twilio to OpenAI"""
                    nonlocal stream_sid
                    audio_count = 0
                    while True:
                        try:
                            # Check queue non-blocking
                            await asyncio.sleep(0.01)
                            try:
                                message = twilio_queue.get_nowait()
                                data = json.loads(message)
                                event_type = data.get("event")

                                if event_type == "start":
                                    stream_sid = data["start"]["streamSid"]
                                    print(f"[OK] Stream started: {stream_sid}")
                                elif event_type == "media":
                                    # Forward audio to OpenAI
                                    audio_append = {
                                        "type": "input_audio_buffer.append",
                                        "audio": data["media"]["payload"],
                                    }
                                    await openai_ws.send(json.dumps(audio_append))
                                    audio_count += 1
                                    if audio_count % 100 == 0:
                                        print(
                                            f"[>] Forwarded {audio_count} audio packets to OpenAI"
                                        )
                                elif event_type == "stop":
                                    print("[STOP] Twilio stream stopped")
                                    break
                            except queue.Empty:
                                pass
                        except Exception as e:
                            print(f"[X] Twilio->OpenAI error: {e}")
                            break

                async def openai_to_twilio():
                    """Forward audio from OpenAI to Twilio"""
                    audio_count = 0
                    while True:
                        try:
                            message = await openai_ws.recv()
                            data = json.loads(message)
                            event_type = data.get("type")

                            # Log important events
                            if event_type == "session.created":
                                print(
                                    f"[OK] OpenAI session created: {data.get('session', {}).get('id', 'unknown')}"
                                )
                            elif event_type == "session.updated":
                                print("[OK] OpenAI session updated")
                            elif event_type == "input_audio_buffer.speech_started":
                                print("[SPEECH] Restaurant speaking detected!")
                            elif event_type == "input_audio_buffer.speech_stopped":
                                print("[QUIET] Restaurant speech stopped")
                            elif event_type == "response.created":
                                print("[AI] OpenAI generating response...")
                            elif event_type == "response.audio.delta":
                                # Send audio back to Twilio
                                audio_delta = data.get("delta", "")
                                if audio_delta:
                                    media_message = {
                                        "event": "media",
                                        "media": {"payload": audio_delta},
                                    }
                                    openai_queue.put(json.dumps(media_message))
                                    audio_count += 1
                                    if audio_count % 50 == 0:
                                        print(
                                            f"[<] Sent {audio_count} audio packets to Twilio",
                                            end="\r",
                                        )
                            elif event_type == "response.audio.done":
                                print(
                                    f"\n[OK] Audio response complete ({audio_count} packets)"
                                )
                                audio_count = 0
                            elif event_type == "response.audio_transcript.done":
                                transcript = data.get("transcript", "")
                                if transcript:
                                    log_conversation("AI", transcript)
                            elif (
                                event_type
                                == "conversation.item.input_audio_transcription.completed"
                            ):
                                transcript = data.get("transcript", "")
                                if transcript:
                                    log_conversation("Restaurant", transcript)
                            elif event_type == "error":
                                print(f"[X] OpenAI error: {data.get('error', {})}")
                        except Exception as e:
                            print(f"\n[X] OpenAI->Twilio error: {e}")
                            break

                # Run both directions concurrently
                await asyncio.gather(twilio_to_openai(), openai_to_twilio())

            except Exception as e:
                print(f"[X] Relay error: {e}")
                import traceback

                traceback.print_exc()
            finally:
                if openai_ws:
                    await openai_ws.close()
                print("[OK] Relay closed")

        try:
            loop.run_until_complete(relay_audio())
        finally:
            loop.close()

    # Start async relay in background thread
    relay_thread = threading.Thread(target=async_relay_thread, daemon=True)
    relay_thread.start()

    # Handle Twilio WebSocket messages synchronously
    try:
        while True:
            message = ws.receive()
            if message is None:
                break

            # Put message in queue for async processing
            twilio_queue.put(message)

            # Check if OpenAI has messages to send back
            try:
                while True:
                    openai_message = openai_queue.get_nowait()
                    ws.send(openai_message)
            except queue.Empty:
                pass

    except Exception as e:
        print(f"[X] WebSocket error: {e}")
    finally:
        print("[OK] Twilio WebSocket closed")


# WebSocket handler for media streaming with OpenAI Realtime API
@sock.route("/media-stream")
def media_stream(ws):
    """
    Handle bidirectional audio streaming between Twilio and OpenAI Realtime API
    This creates a conversational AI that can speak and listen in real-time
    """
    print("\n" + "=" * 70)
    print("[WEBSOCKET] Connection established from Twilio")
    print("=" * 70 + "\n")

    stream_sid = None
    openai_ws = None
    global active_call_sid, server_host

    # Store the server host for later use
    server_host = request.host

    # Use asyncio event loop for WebSocket communication
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def handle_openai_connection():
        nonlocal openai_ws, stream_sid
        is_responding = False  # Track if AI is currently responding

        try:
            # Connect to OpenAI Realtime API
            openai_ws = await websockets.connect(
                "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17",
                additional_headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "OpenAI-Beta": "realtime=v1",
                },
            )

            print("[OK] Connected to OpenAI Realtime API")

            # Handle incoming messages from OpenAI
            async def receive_from_openai():
                nonlocal stream_sid, is_responding
                audio_packets_sent = 0
                try:
                    async for message in openai_ws:
                        data = json.loads(message)
                        event_type = data.get("type", "")

                        # Debug: print all events (including speech detection)
                        if event_type not in [
                            "response.audio.delta",
                            "response.audio_transcript.delta",
                        ]:
                            print(f"[MSG] OpenAI Event: {event_type}")

                        # Log speech detection
                        if event_type == "input_audio_buffer.speech_started":
                            print(f"[SPEECH]  Speech detected!")
                            audio_packets_sent = 0  # Reset counter for new response
                        elif event_type == "input_audio_buffer.speech_stopped":
                            print(f"[QUIET] Speech stopped")

                        if event_type == "response.audio.delta" and data.get("delta"):
                            # Send audio back to Twilio
                            if stream_sid:
                                audio_payload = {
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {"payload": data["delta"]},
                                }
                                try:
                                    ws.send(json.dumps(audio_payload))
                                    audio_packets_sent += 1
                                    if audio_packets_sent % 50 == 0:
                                        print(
                                            f"[SOUND] Sent {audio_packets_sent} audio packets to Twilio"
                                        )
                                except Exception as e:
                                    print(f"[X] Error sending to Twilio: {e}")
                                    break

                        elif event_type == "response.audio.done":
                            print(
                                f"[OK] Total audio packets sent to Twilio: {audio_packets_sent}"
                            )

                        elif event_type == "response.text.done":
                            # Get the full text response
                            text_content = data.get("text", "")
                            if text_content:
                                # Log the AI's response
                                log_conversation("AI", text_content)

                                # Generate audio with ElevenLabs and stream it back through Twilio WebSocket
                                if stream_sid and ws:
                                    import time as time_mod

                                    audio_start = time_mod.time()

                                    try:
                                        print(
                                            f"[ELEVENLABS] Generating audio: {text_content[:50]}..."
                                        )

                                        # Generate with ElevenLabs in ulaw format for Twilio
                                        audio_response = (
                                            elevenlabs_client.text_to_speech.convert(
                                                voice_id=elevenlabs_voice_id,
                                                text=text_content,
                                                model_id="eleven_multilingual_v2",
                                                output_format="ulaw_8000",
                                            )
                                        )

                                        # Collect audio data
                                        audio_data = b""
                                        for chunk in audio_response:
                                            if chunk:
                                                audio_data += chunk

                                        gen_time = (
                                            time_mod.time() - audio_start
                                        ) * 1000
                                        print(
                                            f"[OK] Generated {len(audio_data)} bytes in {gen_time:.0f}ms"
                                        )

                                        # Clear outbound audio buffer first
                                        clear_msg = {
                                            "event": "clear",
                                            "streamSid": stream_sid,
                                        }
                                        ws.send(json.dumps(clear_msg))
                                        print("[OK] Cleared audio buffer")

                                        # Send mark to indicate audio start
                                        mark_msg = {
                                            "event": "mark",
                                            "streamSid": stream_sid,
                                            "mark": {"name": "audio_start"},
                                        }
                                        ws.send(json.dumps(mark_msg))

                                        # Send audio in 160-byte chunks through Media Stream
                                        import base64

                                        CHUNK_SIZE = 160
                                        sent_count = 0

                                        for i in range(0, len(audio_data), CHUNK_SIZE):
                                            chunk_data = audio_data[i : i + CHUNK_SIZE]
                                            if len(chunk_data) < CHUNK_SIZE:
                                                chunk_data += b"\xff" * (
                                                    CHUNK_SIZE - len(chunk_data)
                                                )

                                            encoded = base64.b64encode(
                                                chunk_data
                                            ).decode("utf-8")
                                            media_msg = {
                                                "event": "media",
                                                "streamSid": stream_sid,
                                                "media": {"payload": encoded},
                                            }
                                            ws.send(json.dumps(media_msg))
                                            sent_count += 1

                                        total_time = (
                                            time_mod.time() - audio_start
                                        ) * 1000
                                        print(
                                            f"[OK] Sent {sent_count} packets in {total_time:.0f}ms total"
                                        )

                                    except Exception as e:
                                        print(
                                            f"[X] Error generating/sending audio: {e}"
                                        )
                                        import traceback

                                        traceback.print_exc()

                        elif (
                            event_type
                            == "conversation.item.input_audio_transcription.completed"
                        ):
                            transcript = data.get("transcript", "")
                            if transcript:
                                # Log the restaurant's response
                                log_conversation("Restaurant", transcript)

                        elif event_type == "error":
                            error_info = data.get("error", {})
                            print(f"[X] OpenAI error: {error_info}")

                        elif event_type == "session.created":
                            print(
                                f"[OK] Session created: {data.get('session', {}).get('id', 'unknown')}"
                            )

                        elif event_type == "input_audio_buffer.committed":
                            print(f"[OK] Audio buffer committed")

                        elif event_type == "conversation.item.created":
                            print(f"[OK] Conversation item created")

                        elif event_type == "response.created":
                            print(f"[START] Response created")

                        elif event_type == "response.done":
                            print(f"[OK] Response completed")
                            is_responding = False  # Allow new commits

                        elif event_type == "response.audio.done":
                            print(f"[SOUND] Audio response completed")

                except Exception as e:
                    print(f"[X] Error receiving from OpenAI: {e}")

            # Start receiving from OpenAI in background
            receive_task = asyncio.create_task(receive_from_openai())
            print("[OK] Started OpenAI event receiver task")

            # Now send the session configuration
            print("[SEND] Sending session configuration...")
            session_update = {
                "type": "session.update",
                "session": {
                    "modalities": [
                        "text"
                    ],  # Only text - we'll use ElevenLabs for audio output
                    "instructions": RESERVATION_SYSTEM_PROMPT,
                    "input_audio_format": "g711_ulaw",
                    "input_audio_transcription": {"model": "whisper-1"},
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.3,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 200,
                    },
                    "temperature": 0.8,
                },
            }

            await openai_ws.send(json.dumps(session_update))
            print("[OK] Session configuration sent")

            # Wait for session to be configured
            await asyncio.sleep(1.0)
            print("[OK] Ready for conversation")

            # Handle incoming messages from Twilio
            media_count = 0
            import time

            last_commit_time = time.time()
            first_audio_received = False

            while True:
                try:
                    # Rely on OpenAI's server VAD to automatically detect speech and respond
                    # No manual commits needed - VAD will handle it
                    pass

                    message = ws.receive(timeout=0.1)
                    if message is None:
                        await asyncio.sleep(0.01)
                        continue

                    data = json.loads(message)
                    event = data.get("event", "")

                    if event == "start":
                        stream_sid = data["start"]["streamSid"]
                        active_call_sid = data["start"]["callSid"]
                        print(f"[OK] Media stream started: {stream_sid}")
                        print(f"  Stream details: {data['start']}")
                        print(f"  Call SID: {active_call_sid}")
                        print("[MIC] Listening to conversation...")
                        last_commit_time = time.time()

                    elif event == "media":
                        # Forward audio to OpenAI
                        if not first_audio_received:
                            first_audio_received = True
                            last_commit_time = time.time()
                            print("[AUDIO]  First audio packet received, timer started")
                            # Log first packet details for debugging
                            payload = data["media"]["payload"]
                            print(f"   First payload length: {len(payload)} chars")
                            print(f"   First 50 chars: {payload[:50]}")

                        media_count += 1
                        if media_count % 100 == 0:  # Log every 100 packets
                            print(
                                f"[CALL] Received {media_count} audio packets from Twilio"
                            )

                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data["media"]["payload"],
                        }
                        await openai_ws.send(json.dumps(audio_append))

                    elif event == "stop":
                        print(
                            f"[STOP]  Media stream stopped (received {media_count} audio packets)"
                        )
                        break

                    else:
                        print(f"[MSG] Twilio Event: {event}")

                except Exception as e:
                    if "timed out" not in str(e):
                        print(f"[X] Error processing Twilio message: {e}")
                    await asyncio.sleep(0.01)

            # Cancel the receive task
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass

        except Exception as e:
            print(f"WebSocket error: {e}")

        finally:
            if openai_ws:
                await openai_ws.close()
            print("[OK] OpenAI connection closed")

            # Print conversation summary
            print("\n" + "=" * 70)
            print("CONVERSATION TRANSCRIPT SUMMARY")
            print("=" * 70)
            if conversation_transcript:
                for entry in conversation_transcript:
                    speaker_label = (
                        "[AI]" if entry["speaker"] == "AI" else "[RESTAURANT]"
                    )
                    print(f"{entry['timestamp']} {speaker_label}: {entry['message']}")
                print("=" * 70)
                print(f"Total exchanges: {len(conversation_transcript)}")

                # Save to file
                from datetime import datetime
                import json as json_lib

                filename = (
                    f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                with open(filename, "w", encoding="utf-8") as f:
                    json_lib.dump(
                        conversation_transcript, f, ensure_ascii=False, indent=2
                    )
                print(f"Transcript saved to: {filename}")
            else:
                print("No conversation recorded")
            print("=" * 70 + "\n")

    # Run the async handler
    try:
        loop.run_until_complete(handle_openai_connection())
    except Exception as e:
        print(f"Error in event loop: {e}")
    finally:
        loop.close()


@app.route("/status", methods=["POST"])
def status():
    """Handle call status callbacks"""
    call_status = request.values.get("CallStatus", "unknown")
    call_sid = request.values.get("CallSid", "unknown")

    print(f"\n{'='*70}")
    print(f"[CALL STATUS] Call {call_sid}: {call_status}")

    if call_status == "completed":
        print("[CALL] Call ended by restaurant")
        print("=" * 70 + "\n")
    elif call_status == "failed":
        print("[CALL] Call failed")
        print("=" * 70 + "\n")
    elif call_status == "busy":
        print("[CALL] Restaurant line is busy")
        print("=" * 70 + "\n")
    elif call_status == "no-answer":
        print("[CALL] Restaurant did not answer")
        print("=" * 70 + "\n")
    else:
        print("=" * 70 + "\n")

    return "", 200


def start_flask():
    """Start Flask server in a separate thread"""
    app.run(port=8080, debug=False, use_reloader=False, host="0.0.0.0")


def make_reservation_call():
    """Initiate a call to the restaurant"""
    import time
    import requests

    # Start Flask server in background thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    print("Starting Flask server on port 8080...")
    time.sleep(2)

    # Wait for Flask to be ready
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8080/")
            print("OK - Flask server is ready!")
            break
        except requests.exceptions.ConnectionError:
            if i < max_retries - 1:
                time.sleep(1)
            else:
                print("WARN - Flask server might not be ready")
                break

    # Set ngrok auth token
    ngrok_auth_token = os.getenv("NGROK_AUTH_TOKEN")
    if ngrok_auth_token:
        ngrok.set_auth_token(ngrok_auth_token)
        print("[OK] ngrok authenticated successfully")
    else:
        print("[WARN] Warning: NGROK_AUTH_TOKEN not found in .env file")

    # Start ngrok tunnel
    print("Starting ngrok tunnel...")
    tunnel = ngrok.connect("8080")

    # Extract the public URL
    public_url_str = str(tunnel.public_url) if tunnel.public_url else ""

    # Convert http to https for WebSocket support
    if public_url_str.startswith("http://"):
        public_url_str = public_url_str.replace("http://", "https://")

    print(f"[OK] ngrok tunnel URL: {public_url_str}")

    # Ensure the URL doesn't have a trailing slash
    public_url_str = public_url_str.rstrip("/")

    # Construct webhook URLs
    voice_url = f"{public_url_str}/voice"
    status_url = f"{public_url_str}/status"

    print(f"  Voice webhook: {voice_url}")
    print(f"  Status webhook: {status_url}")

    # Test the ngrok tunnel
    print("\nTesting ngrok tunnel...")
    try:
        test_response = requests.get(voice_url, timeout=10)
        if test_response.status_code == 200:
            print("[OK] ngrok tunnel is working correctly")
        else:
            print(
                f"[WARN] ngrok tunnel returned status code: {test_response.status_code}"
            )
    except Exception as e:
        print(f"[ERR] Error testing ngrok tunnel: {e}")
        print("  Continuing anyway...")

    # Update Twilio phone number webhook configuration
    print("\nUpdating Twilio webhook configuration...")
    try:
        incoming_phone_numbers = twilio_client.incoming_phone_numbers.list(
            phone_number=twilio_phone
        )

        if incoming_phone_numbers:
            phone_number_sid = incoming_phone_numbers[0].sid
            if phone_number_sid:
                twilio_client.incoming_phone_numbers(phone_number_sid).update(
                    voice_url=voice_url,
                    voice_method="POST",
                    status_callback=status_url,
                    status_callback_method="POST",
                )
                print(f"[OK] Webhook updated for {twilio_phone}")
            else:
                print(f"[ERR] Could not get SID for phone number")
        else:
            print(f"[ERR] Phone number {twilio_phone} not found in your account")
    except Exception as e:
        print(f"[ERR] Error updating webhook: {e}")

    # Make the reservation call
    print("\n" + "=" * 70)
    print("[FOOD]  MAKING RESTAURANT RESERVATION CALL")
    print("=" * 70)
    print(f"  From: {twilio_phone}")
    print(f"  To: {to_phone}")
    print(f"  AI Persona: Friendly customer making a reservation")
    print("=" * 70 + "\n")

    try:
        call = twilio_client.calls.create(
            to=to_phone,
            from_=twilio_phone,
            url=voice_url,
            status_callback=status_url,
            status_callback_method="POST",
        )
        print(f"[OK] Call initiated: {call.sid}")
        print(f"  The AI is now calling the restaurant...")
        print(f"  Listen to the conversation - transcripts will appear below:")
        print("-" * 70)
    except Exception as e:
        print(f"[ERR] Error making call: {e}")

    print("\n" + "=" * 70)
    print("Server is running. Press Ctrl+C to stop.")
    print("=" * 70)

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        ngrok.disconnect(public_url_str)
        print("[OK] ngrok tunnel closed.")


if __name__ == "__main__":
    make_reservation_call()
