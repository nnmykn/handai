from pynput import keyboard

class AKeyListener:
    def __init__(self):
        self.key_pressed = False

    def on_press(self, key):
        if key == keyboard.Key.a:
            self.key_pressed = True
            print("Aキーを押しています")

    def on_release(self, key):
        if key == keyboard.Key.a:
            self.key_pressed = False
            print("Aキーを離しました")
            # Aキーを離したときの処理を以下に追加
            self.stop_listener()

    def stop_listener(self):
        self.listener.stop()

    def start(self):
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as self.listener:
            self.listener.join()

listener = AKeyListener()
listener.start()
