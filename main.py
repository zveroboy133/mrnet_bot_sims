# https://ru.stackoverflow.com/questions/1340031/buildozer-%D0%BD%D0%B5-%D1%80%D0%B0%D0%B1%D0%BE%D1%82%D0%B0%D0%B5%D1%82

from kivy.app import App
from kivy.uix.button import Button


class MyApp(App):
    def build(self):
        return Button(text='Hello, World!')


if __name__ == '__main__':
    MyApp().run()
