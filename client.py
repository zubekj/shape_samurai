from kivy.support import install_twisted_reactor

install_twisted_reactor()

from twisted.internet import reactor, protocol

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.properties import ListProperty
from kivy.graphics import Color, Rectangle

import sys
import pickle
import zlib

from game_state import GameState


class GameClient(protocol.Protocol):
    """
    GameClient manages active connection to the server.
    """

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.app.on_connection(self.transport)

    def dataReceived(self, data):
        self.factory.app.update_game(pickle.loads(zlib.decompress(data)))


class GameClientFactory(protocol.ClientFactory):
    """
    GameClientFactory opens new connection to the server.
    """

    def __init__(self, app):
        self.app = app

    def buildProtocol(self, addr):
        return GameClient(self)

    def clientConnectionLost(self, connector, reason):
        msg = 'Connection was dropped by the server.'
        self.app.popup = Popup(title='Connection lost',
                               content=Label(text=msg),
                               auto_dismiss=False)
        self.app.popup.open()

    def clientConnectionFailed(self, connector, reason):
        msg = 'Connection failed: server is not responding.'
        self.app.popup = Popup(title='Connection failed',
                               content=Label(text=msg),
                               auto_dismiss=False)
        self.app.popup.open()


class RootLayout(FloatLayout):
    """
    RootLayout is the main widget of game window. Sprites are drawn here.
    It captures user input.
    """

    background_color = ListProperty([0, 0, 0, 1])

    def __init__(self, app, **kwargs):
        self.app = app
        super(RootLayout, self).__init__(**kwargs)
        self._update_color()
        self.bind(background_color=self._update_color)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_color(self, *args):
        with self.canvas.before:
            Color(*self.background_color)
            self.rect = Rectangle(size=self.size, pos=self.pos)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_touch_move(self, touch):
        self.app.connection.write(zlib.compress(pickle.dumps(touch.pos)))

    def on_touch_down(self, touch):
        self.app.connection.write(zlib.compress(pickle.dumps(touch.pos)))


class GameClientApp(App):
    """
    Game client application with GUI.
    """
    connection = None
    popup = None

    def build(self):
        root = self.setup_gui()
        self.connect_to_server()
        return root

    def setup_gui(self):
        self.player_a = Image(source="a.png")
        self.player_b = Image(source="b.png")
        self.root = RootLayout(self)
        self.root.add_widget(self.player_a)
        self.root.add_widget(self.player_b)
        return self.root

    def connect_to_server(self):
        msg = 'Waiting for connection.'
        self.popup = Popup(title='Waiting',
                           content=Label(text=msg),
                           auto_dismiss=False)
        self.popup.open()
        reactor.connectTCP('localhost', 8000, GameClientFactory(self))

    def on_connection(self, connection):
        self.popup.dismiss()
        self.connection = connection
        self.connection.write("login".encode('utf-8'))
        msg = 'Waiting for the second player.'
        self.popup = Popup(title='Waiting',
                           content=Label(text=msg),
                           auto_dismiss=False)
        self.popup.open()

    def update_game(self, game_state):
        if self.popup is not None:
            self.popup.dismiss()
            self.popup = None

        self.player_a.center = game_state.player_a
        self.player_b.center = game_state.player_b
        if game_state.interaction:
            self.root.background_color = [1, 0, 0, 1]
        else:
            self.root.background_color = [0, 0, 0, 1]

    def on_stop(self):
        if self.connection is not None:
            self.connection.loseConnection()
        return True

if __name__ == '__main__':
    GameClientApp().run()
