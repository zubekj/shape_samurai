from kivy.graphics.vertex_instructions import Line, Ellipse
from kivy.support import install_twisted_reactor
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.widget import Widget

install_twisted_reactor()

from twisted.internet import reactor, protocol

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle

import pickle
import zlib

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
        pass

    def clientConnectionFailed(self, connector, reason):
        msg = 'Connection failed: server is not responding.'



class RootLayout(BoxLayout):
    """
    RootLayout is the main widget of game window. Sprites are drawn here.
    It captures user input.
    """

    label = Label(text='Waiting for server...')
    top_layout = AnchorLayout(size_hint=(1, 0.1))
    bottom_layout = AnchorLayout(size_hint=(1, 0.8))
    drawing_container = Widget(size_hint=(0.8, 0.8))

    def __init__(self, app, **kwargs):
        self.app = app
        self.shape = None
        self.finger = None
        self.finger1 = None
        super(RootLayout, self).__init__(**kwargs)

        self.add_widget(self.top_layout)
        self.add_widget(self.bottom_layout)
        self.top_layout.add_widget(self.label)
        self.bottom_layout.add_widget(self.drawing_container)

        color = (232.0 / 255.0, 234.0 / 255.0, 246.0 / 255.0)
        color_a = (255.0 / 255.0, 0 / 255.0, 0 / 255.0)
        color_b = (0.0 / 255.0, 255.0 / 255.0, 0.0 / 255.0)
        with self.canvas:
            Color(*color, mode='rgb')
            self.line = Line(width=5)
            self.line.cap = 'round'
            self.line.joint = 'round'
            self.line.joint_precision = 100

        with self.canvas.after:
            Color(*color_b, mode='rgb')
            self.line_green = Line(width=5)
            self.line_green.cap = 'round'
            self.line_green.joint = 'round'
            self.line_green.joint_precision = 100
            Color(*color_a, mode='rgb')
            self.line_red = Line(width=5)
            self.line_red.cap = 'round'
            self.line_red.joint = 'round'
            self.line_red.joint_precision = 100

        with self.label.canvas:
            Color(*color, mode='rgb')

        color = (26.0 / 255.0, 35.0 / 255.0, 126.0 / 255.0)
        with self.top_layout.canvas.before:
            Color(*color, mode='rgb')
            self.top_ = Rectangle(size=self.top_layout.size,
                                  pos=self.top_layout.pos)

        color = (40.0 / 255.0, 53.0 / 255.0, 147.0 / 255.0)
        with self.bottom_layout.canvas.before:
            Color(*color, mode='rgb')
            self.bottom_ = Rectangle(size=self.bottom_layout.size,
                                     pos=self.bottom_layout.pos)

        self.top_layout.height = 200
        self.drawing_container.bind(size=self._update_rect, pos=self._update_rect)

    def on_touch_down(self, touch):
        pos = ((touch.x - self.drawing_container.pos[0]) / self.drawing_container.width,
               (touch.y - self.drawing_container.pos[1]) / self.drawing_container.height)
        if 0 <= pos[0] <= 1 and 0 <= pos[1] <= 1 and self.shape:
            touch.grab(self)
            self.app.connection.write(zlib.compress(pickle.dumps(pos)))

        return True

    def on_touch_move(self, touch):
        pos = ((touch.x - self.drawing_container.pos[0]) / self.drawing_container.width,
               (touch.y - self.drawing_container.pos[1]) / self.drawing_container.height)
        if 0 <= pos[0] <= 1 and 0 <= pos[1] <= 1 and self.shape:
            self.app.connection.write(zlib.compress(pickle.dumps(pos)))

    def on_touch_up(self, touch):
        if self.finger:
            self.drawing_container.canvas.remove(self.finger)
            self.finger = None

    def refresh(self, value):
        self.line.points = []
        self.line_red.points = []
        self.line_green.points = []
        if self.shape:
            for index, point in enumerate(self.shape.shape):
                pos = [self.drawing_container.pos[0] + point[0] * self.drawing_container.width,
                       self.drawing_container.pos[1] + point[1] * self.drawing_container.height]
                self.line.points += pos
                if index <= self.shape.player_dict['a'][1]:
                    self.line_red.points += pos
                if index <= self.shape.player_dict['b'][1]:
                    self.line_green.points += pos

            a_pos = (self.drawing_container.pos[0] + self.shape.player_dict['a'][0][0] * self.drawing_container.width,
                     self.drawing_container.pos[1] + self.shape.player_dict['a'][0][1] * self.drawing_container.height)

            b_pos = (self.drawing_container.pos[0] + self.shape.player_dict['b'][0][0] * self.drawing_container.width,
                     self.drawing_container.pos[1] + self.shape.player_dict['b'][0][1] * self.drawing_container.height)

            if self.finger:
                self.finger.pos = (a_pos[0] - 10, a_pos[1] - 10)
                if self.finger1:
                    self.finger1.pos = (b_pos[0] - 10, b_pos[1] - 10)
            else:
                color = (255.0 / 255.0, 0 / 255.0, 0 / 255.0)
                with self.drawing_container.canvas:
                    Color(*color, mode='rgb', group='group')
                    self.finger = Ellipse(size=(20, 20), pos=(a_pos[0] - 10, a_pos[1] - 10), group='group')

                if not self.finger1:
                    color = (0.0 / 255.0, 255.0 / 255.0, 0.0 / 255.0)
                    with self.drawing_container.canvas:
                        Color(*color, mode='rgb', group='group')
                        self.finger1 = Ellipse(size=(20, 20), pos=(b_pos[0] - 10, b_pos[1] - 10), group='group')

        self.top_.size = self.top_layout.size
        self.top_.pos = self.top_layout.pos

        self.bottom_.size = self.bottom_layout.size
        self.bottom_.pos = self.bottom_layout.pos

    def _update_rect(self, instance, value):
        self.refresh(value)


class GameClientApp(App):
    """
    Game client application with GUI.
    """
    connection = None
    popup = None

    def build(self):
        self.title = 'Shape Samurai'
        root = self.setup_gui()
        self.connect_to_server()
        return root

    def setup_gui(self):
        self.root = RootLayout(self, orientation='vertical')
        return self.root

    def connect_to_server(self):
        reactor.connectTCP('localhost', 8000, GameClientFactory(self))

    def on_connection(self, connection):
        self.connection = connection
        self.connection.write(zlib.compress(pickle.dumps("login")))
        RootLayout.label.text = "Connected"

    def update_game(self, game_state):
        RootLayout.label.text = "Game Started"
        if game_state == "victory":
            RootLayout.label.text = "Victory!"
            self.connection.write(zlib.compress(pickle.dumps("login")))
            return
        self.root.shape = game_state
        self.root.refresh(game_state)

    def on_stop(self):
        if self.connection is not None:
            self.connection.loseConnection()
        return True


if __name__ == '__main__':
    GameClientApp().run()
