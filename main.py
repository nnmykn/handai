import threading
import wave

import pyaudio
import replicate
from dotenv import load_dotenv
from pynput import keyboard

load_dotenv()

def whisper(file):
    output = replicate.run(
        "openai/whisper:91ee9c0c3df30478510ff8c8a3a545add1ad0259ad3a9f78fba57fbc05ee64f7",
        input={"audio": open(file, "rb")}
    )
    print(output["transcription"])
    return output["transcription"]

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
                whisper("./output.wav")
        except AttributeError:
            pass

    def stop_listener(self):
        self.listener.stop()

    def start(self):
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as self.listener:
            self.listener.join()

listener = AKeyListener()
listener.start()
