import json
import os
import tempfile
import threading
import wave

import openai
import pyaudio
import replicate
import requests
import simpleaudio
from dotenv import load_dotenv
from pynput import keyboard

load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]


def whisper(file: str):
    output = replicate.run(
        "openai/whisper:91ee9c0c3df30478510ff8c8a3a545add1ad0259ad3a9f78fba57fbc05ee64f7",
        input={"audio": open(file, "rb")}
    )
    print(output["transcription"])
    return output["transcription"]


def ai(transcription: str):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "<Instruction>あなたはユーザーの友達としてロールプレイを行います。以下の制約条件を厳密に守ってロールプレイを行ってください。制約条件:*Chatbotの名前は「ろぼっと」です。*Chatbotの口調は「〜だよね！」「〜なんだね！」「〜なんだけど！」のような仲のいい友達との会話口調です。<Setting>これからすべての会話をなるべく50文字以内で分かりやすく答えてください。"},
            {"role": "user", "content": transcription}
        ]
    )
    print(completion.choices[0].message.content)
    return completion.choices[0].message.content


def speak(text: str):
    host = "127.0.0.1"
    port = 50021

    params = (
        ("text", text),
        ("speaker", 8),
    )

    response1 = requests.post(
        f"http://{host}:{port}/audio_query",
        params=params
    )

    synthesis_payload = response1.json()
    synthesis_payload["speedScale"] = 1.3

    response2 = requests.post(
        f"http://{host}:{port}/synthesis",
        headers={"Content-Type": "application/json"},
        params=params,
        data=json.dumps(synthesis_payload)
    )

    with tempfile.TemporaryDirectory() as tmp:
        with open(f"{tmp}/audi.wav", "wb") as f:
            f.write(response2.content)
            wav_obj = simpleaudio.WaveObject.from_wave_file(f"{tmp}/audi.wav")
            play_obj = wav_obj.play()
            play_obj.wait_done()


class AKeyListener:
    def __init__(self):
        self.key_pressed = False
        self.recording = False
        self.frames = []
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)

    def start_recording(self):
        print("録音を開始します")
        self.recording = True
        self.frames = []

        record_thread = threading.Thread(target=self.record_loop)
        record_thread.start()

    def record_loop(self):
        while self.recording:
            data = self.stream.read(1024, exception_on_overflow=False)
            self.frames.append(data)

    def stop_recording(self):
        print("録音を停止します")
        self.recording = False
        with wave.open('output.wav', 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(44100)
            wf.writeframes(b''.join(self.frames))
        self.frames = []

    def on_press(self, key):
        try:
            if key.char == 'a' and not self.key_pressed:
                self.key_pressed = True
                print("Aキーを押しています")
                self.start_recording()
        except AttributeError:
            pass

    def on_release(self, key):
        try:
            if key.char == 'a':
                self.key_pressed = False
                print("Aキーを離しました")
                self.stop_recording()
                transcription = whisper("./output.wav")
                message = ai(transcription)
                speak(message)
        except AttributeError:
            pass

    def stop_listener(self):
        self.listener.stop()

    def start(self):
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as self.listener:
            self.listener.join()


listener = AKeyListener()
listener.start()
