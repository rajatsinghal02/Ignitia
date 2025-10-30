import os
import asyncio
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile
from groq import Groq
import edge_tts   # ✅ multilingual + fast TTS

# --- CONFIG ---
RECORD_SECONDS = 6   # small chunks = lower latency
SAMPLE_RATE = 16000
CHANNELS = 1

# --- INIT GROQ ---
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
print("Groq client initialized.")

# --- RECORD ---
def record_audio(duration, rate):
    print(f"Recording {duration}s...")
    recording = sd.rec(int(duration * rate), samplerate=rate, channels=CHANNELS, dtype='int16')
    sd.wait()
    return recording

def save_audio(recording, rate):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    wav.write(tmp.name, rate, recording)
    return tmp.name

# --- TRANSCRIBE ---
def transcribe_audio(path):
    print("Transcribing...")
    with open(path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=(path, f.read())
        )
    os.remove(path)
    text = result.text.strip()
    print(f"You said: {text}")
    return text

# --- AI RESPONSE ---
def get_ai_response(user_text, history):
    print("Thinking...")
    messages = history + [{"role": "user", "content": user_text}]
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",   # ✅ multilingual + fast
        messages=messages,
        temperature=0.3
    )
    reply = completion.choices[0].message.content.strip()
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": reply})
    print(f"AI: {reply}")
    return reply

# --- MULTILINGUAL TTS (EDGE) ---
async def speak_text(text, lang="en-IN"):
    """Use Microsoft Edge-TTS for multilingual speech output."""
    try:
        tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        # auto-detect language for TTS
        if any("\u0900" <= c <= "\u097F" for c in text):  # Hindi Devanagari check
            lang = "hi-IN"
            voice = "hi-IN-MadhurNeural"
        else:
            voice = "en-IN-NeerjaNeural"
        
        communicate = edge_tts.Communicate(text, voice=voice)
        await communicate.save(tmpfile)
        os.system(f"afplay {tmpfile}" if os.name == "posix" else f"start {tmpfile}")
        os.remove(tmpfile)
    except Exception as e:
        print(f"TTS error: {e}")

# --- MAIN LOOP ---
def main():
    history = [
        {"role": "system", "content": 
         "You are a disaster-response assistant. "
         "Be extremely concise. Respond in the same language the user speaks and be very concise and to the point and clear speak in same language as user"}
    ]
    print("\n--- Real-Time AI Assistant Ready ---")
    print("Listening in short loops (press Ctrl+C to quit).")
    
    while True:
        rec = record_audio(RECORD_SECONDS, SAMPLE_RATE)
        path = save_audio(rec, SAMPLE_RATE)
        user_text = transcribe_audio(path)
        
        if not user_text:
            print("No speech detected.")
            continue

        reply = get_ai_response(user_text, history)
        asyncio.run(speak_text(reply))
        print("-"*30)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting.")

