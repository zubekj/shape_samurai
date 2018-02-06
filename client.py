from kivy.graphics.vertex_instructions import Line, Ellipse
from kivy.properties import NumericProperty, Clock
from kivy.support import install_twisted_reactor
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.widget import Widget
from kivy.core.window import Window

install_twisted_reactor()

from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle

import pickle
import zlib
import json

class GameClientProtocol(LineReceiver):
    """
    GameClient manages active connection to the server.
    """

    def __init__(self, factory):
        self.factory = factory
        self.state = "WAIT"

    def connectionMade(self):
        self.factory.app.on_connection(self)

    def lineReceived(self, line):
        line = line.decode('utf-8')
        if self.state == "READY":
            if line == "start":
                self.set_game()
        elif self.state == "GAME":
            if line == "reset":
                self.set_wait()
            else:
                state = json.loads(line)
                self.factory.app.update_game(state)

    def sendLine(self, line):
        super(self.__class__, self).sendLine(line.encode('utf-8'))

    def send_player_position(self, pos):
        self.sendLine("{0},{1}".format(*pos))

    def set_ready(self):
        self.state = "READY"
        self.sendLine("ready")

    def set_wait(self):
        self.state = "WAIT"
        self.factory.app.on_reset()

    def set_game(self):
        self.state = "GAME"
        self.factory.app.on_game_start()


class GameClientFactory(ClientFactory):
    """
    GameClientFactory opens new connection to the server.
    """

    def __init__(self, app):
        self.app = app

    def buildProtocol(self, addr):
        return GameClientProtocol(self)

    def clientConnectionLost(self, connector, reason):
        self.app.on_connection_lost()

    def clientConnectionFailed(self, connector, reason):
        msg = 'Connection failed: server is not responding.'
        self.app.label.text = msg


class RootLayout(BoxLayout):
    """
    RootLayout is the main widget of game window. Sprites are drawn here.
    It captures user input.
    """

    label = Label(text='Waiting for server...')
    top_layout = BoxLayout(size_hint=(1, 0.1), orientation="horizontal")
    bottom_layout = AnchorLayout(size_hint=(1, 0.8))
    drawing_container = Widget(size_hint=(0.8, 0.8))
    clock_display = Label(text='00', font_size=50)

    color_line = (237.0 / 255.0, 212.0 / 255.0, 157.0 / 255.0, 1)
    color_a = (3.0 / 255.0, 164.0 / 255.0, 119 / 255.0, 0.5)
    color_b = (172.0 / 255.0, 2 / 255.0, 183.0 / 255.0, 0.5)
    color_start_point = (255.0 / 255.0, 0 / 255.0, 0 / 255.0)
    color_top = (26.0 / 255.0, 35.0 / 255.0, 126.0 / 255.0)
    color_bottom = (150.0 / 255.0, 150.0 / 255.0, 150.0 / 255.0)

    line_width = 5
    cursor_size = 20
    spoint_size = 15

    def __init__(self, app, **kwargs):
        self.app = app
        self.shape = None
        self.players = None
        self.cursor_a = None
        self.cursor_b = None
        super(RootLayout, self).__init__(**kwargs)

        self.add_widget(self.top_layout)
        self.add_widget(self.bottom_layout)
        self.top_layout.add_widget(Widget(size_hint=(0.33, 1.0)))
        anchor_label = AnchorLayout(size_hint=(0.33, 1.0))
        anchor_label.add_widget(self.label)
        self.top_layout.add_widget(anchor_label)
        counter = AnchorLayout(anchor_x="right", size_hint=(0.34, 1.0))
        counter.add_widget(self.clock_display)
        self.top_layout.add_widget(counter)
        self.bottom_layout.add_widget(self.drawing_container)

        self.top_layout.height = 200
        self.drawing_container.bind(size=self._update_rect, pos=self._update_rect)
        self.initialize_shapes()

    def initialize_shapes(self):

        with self.drawing_container.canvas:
            # Shape line
            Color(*self.color_line, mode='rgb')
            self.line = Line(width=self.line_width)
            self.line.cap = 'round'
            self.line.joint = 'round'
            self.line.joint_precision = 100
            # Starting point
            Color(*self.color_start_point, mode='rgb')
            s = self.spoint_size
            self.start_point = Ellipse(size=(s, s), pos=(0, 0))
            # Cursors
            s = self.cursor_size
            Color(*self.color_a, mode='rgb', group='group')
            self.cursor_a = Ellipse(size=(s, s), pos=(0, 0))
            Color(*self.color_b, mode='rgb', group='group')
            self.cursor_b = Ellipse(size=(s, s), pos=(0, 0))

        with self.drawing_container.canvas.after:
            # Progress lines
            Color(*self.color_b, mode='rgba')
            self.line_green = Line(width=self.line_width)
            self.line_green.cap = 'round'
            self.line_green.joint = 'round'
            self.line_green.joint_precision = 100
            Color(*self.color_a, mode='rgba')
            self.line_red = Line(width=self.line_width)
            self.line_red.cap = 'round'
            self.line_red.joint = 'round'
            self.line_red.joint_precision = 100

        with self.label.canvas:
            Color(*self.color_line, mode='rgb')

        with self.top_layout.canvas.before:
            Color(*self.color_top, mode='rgb')
            self.top_ = Rectangle(size=self.top_layout.size,
                                  pos=self.top_layout.pos)

        with self.bottom_layout.canvas.before:
            Color(*self.color_bottom, mode='rgb')
            self.bottom_ = Rectangle(size=self.bottom_layout.size,
                                     pos=self.bottom_layout.pos,
                                     source='Samurai.png')

    def to_screen_coords(self, pos, shift_x=0, shift_y=0):
        x, y = self.drawing_container.pos
        w, h = self.drawing_container.size
        return (x + pos[0] * w + shift_x), (y + pos[1]*h + shift_y)

    def from_screen_coords(self, sx, sy):
        x, y = self.drawing_container.pos
        w, h = self.drawing_container.size
        return (sx - x) / w, (sy-y) / h

    def on_touch_down(self, touch):
        self.app.key_pressed()
        self.on_touch_move(touch)
        return True

    def on_touch_move(self, touch):
        pos = self.from_screen_coords(touch.x, touch.y)
        if 0 <= pos[0] <= 1 and 0 <= pos[1] <= 1 and self.shape:
            self.app.connection.send_player_position(pos)

    def refresh_shape(self):
        self.line.points = []
        if self.shape is None:
            self.start_point.pos = (0, 0)
            return
        for point in self.shape:
            self.line.points += self.to_screen_coords(point)
        s = self.line_width
        self.start_point.pos = self.to_screen_coords(self.shape[0], -s-1, -s-1)

    def refresh_players(self):
        if self.shape is None:
            self.line_red.points = []
            self.line_green.points = []
            self.cursor_a.pos = (0, 0)
            self.cursor_b.pos = (0, 0)
            return
        self.line_red.points = self.line.points[:self.players[0][1]*2]
        self.line_green.points = self.line.points[:self.players[1][1]*2]
        a_pos = self.to_screen_coords(self.players[0][0])
        b_pos = self.to_screen_coords(self.players[1][0])
        s = self.cursor_size / 2
        self.cursor_a.pos = (a_pos[0] - s, a_pos[1] - s)
        self.cursor_b.pos = (b_pos[0] - s, b_pos[1] - s)

    def _update_rect(self, instance, value):
        self.top_.size = self.top_layout.size
        self.top_.pos = self.top_layout.pos
        self.bottom_.size = self.bottom_layout.size
        self.bottom_.pos = self.bottom_layout.pos
        self.refresh_shape()
        self.refresh_players()

class GameClientApp(App):
    """
    Game client application with GUI.
    """
    connection = None
    should_restart = False

    def build(self):
        self.title = 'Shape Samurai'
        root = RootLayout(self, orientation='vertical')

        with open("client_config.json") as f:
            config = json.load(f)
        self.connect_to_server(config["host"], config["port"])

        return root

    def connect_to_server(self, host, port):
        reactor.connectTCP(host, port, GameClientFactory(self))

    def key_pressed(self):
        if self.should_restart:
            self.should_restart = False
            self.connection.set_ready()

    def counting(self, value):
        current_count = int(self.root.clock_display.text)
        current_count = current_count + 1
        self.root.clock_display.text = str(current_count)

    def on_connection(self, connection):
        self.connection = connection
        self.should_restart = True
        RootLayout.label.text = "Connected. Press any key to start the game..."

    def on_connection_lost(self):
        self.root.shape = None
        self.root.players = None
        self.root.label.text = "Connection lost"
        self.root.refresh_shape()
        self.root.refresh_players()
        self.root.clock_display.text = "00"
        Clock.unschedule(self.counting)

    def update_game(self, game_state):
        if "shape" in game_state:
            self.root.shape = game_state["shape"]
            self.root.refresh_shape()
        if "players" in game_state:
            self.root.players = game_state["players"]
            self.root.refresh_players()

    def on_game_start(self):
        RootLayout.label.text = "Game Started"
        Clock.unschedule(self.counting)
        Clock.schedule_interval(self.counting, 1.)

    def on_reset(self):
        RootLayout.label.text = "Victory! Press any key to restart..."
        Clock.unschedule(self.counting)
        self.root.clock_display.text = "00"
        self.should_restart = True

    def on_stop(self):
        if self.connection is not None:
            self.connection.transport.loseConnection()
        return True


if __name__ == '__main__':
    GameClientApp().run()
