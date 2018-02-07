from kivy.graphics.vertex_instructions import Line, Ellipse, SmoothLine
from kivy.properties import NumericProperty, Clock, ObjectProperty, ListProperty, StringProperty
from kivy.support import install_twisted_reactor
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.widget import Widget
from kivy.uix.effectwidget import EffectWidget, FXAAEffect
from kivy.core.window import Window

install_twisted_reactor()

from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle

import json

class GameClientProtocol(LineReceiver):
    """
    GameClient manages active connection to the server.
    """

    def __init__(self, factory):
        self.factory = factory
        self.state = "WAIT"
        self.msg_buffer = ""

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
            elif line == "json_end":
                state = json.loads(self.msg_buffer)
                self.msg_buffer = ""
                self.factory.app.update_game(state)
            else:
                self.msg_buffer += line

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
        self.app.root.msg_text = msg


class RootLayout(BoxLayout):
    """
    RootLayout is the main widget of game window. Sprites are drawn here.
    It captures user input.
    """
    drawing_container = ObjectProperty(None)
    clock_time = NumericProperty(0)
    score = NumericProperty(0)
    msg_text = StringProperty("Waiting for server")
    line_a = ListProperty([])
    line_b = ListProperty([])
    progress_a = NumericProperty(0)
    progress_b = NumericProperty(0)
    line_green = ListProperty([])
    cursor_a = ListProperty((0, 0))
    cursor_b = ListProperty((0, 0))
    distance = NumericProperty(0)

    def __init__(self, **kwargs):
        self.app = App.get_running_app()
        self.players = None
        self.shapes = None
        super(RootLayout, self).__init__(**kwargs)

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
        if 0 <= pos[0] <= 1 and 0 <= pos[1] <= 1 and self.shapes:
            self.app.connection.send_player_position(pos)

    def refresh_shapes(self):
        if self.shapes is None:
            self.line_a = []
            self.line_b = []
            return
        line_a = []
        for point in self.shapes[0]:
            line_a += self.to_screen_coords(point)
        self.line_a = line_a
        line_b = []
        for point in self.shapes[1]:
            line_b += self.to_screen_coords(point)
        self.line_b = line_b

    def refresh_players(self):
        if self.shapes is None:
            self.cursor_a = (0, 0)
            self.cursor_b = (0, 0)
            self.distance = 0
            return
        self.progress_a = self.players[0][1]
        self.progress_b = self.players[1][1]
        a_pos = self.to_screen_coords(self.players[0][0])
        b_pos = self.to_screen_coords(self.players[1][0])
        self.cursor_a = (a_pos[0] - 10, a_pos[1] - 10)
        self.cursor_b = (b_pos[0] - 10, b_pos[1] - 10)
        self.distance = (self.players[0][1]/len(self.shapes[0]) - self.players[1][1]/len(self.shapes[1]))

    def _update_rect(self, instance, value):
        self.refresh_shapes()
        self.refresh_players()


class GameClientApp(App):
    """
    Game client application with GUI.
    """
    connection = None
    should_restart = False

    def __init__(self, **kwargs):
        super(GameClientApp, self).__init__(**kwargs)
        self.title = 'Shape Samurai'

    def on_start(self):
        with open("client_config.json") as f:
            config = json.load(f)
        self.connect_to_server(config["host"], config["port"])

    def connect_to_server(self, host, port):
        reactor.connectTCP(host, port, GameClientFactory(self))

    def key_pressed(self):
        if self.should_restart:
            self.should_restart = False
            self.connection.set_ready()

    def counting(self, value):
        self.root.clock_time += 1

    def on_connection(self, connection):
        self.connection = connection
        self.should_restart = True
        self.root.msg_text = "Connected. Press any key to start the game..."

    def on_connection_lost(self):
        self.root.shapes = None
        self.root.players = None
        self.root.msg_text = "Connection lost"
        self.root.refresh_shapes()
        self.root.refresh_players()
        self.root.clock_time = 0
        Clock.unschedule(self.counting)

    def update_game(self, game_state):
        if "shapes" in game_state:
            self.root.shapes = game_state["shapes"]
            self.root.refresh_shapes()
        if "players" in game_state:
            self.root.players = game_state["players"]
            self.root.refresh_players()

    def on_game_start(self):
        self.root.msg_text = "Game started"
        Clock.unschedule(self.counting)
        Clock.schedule_interval(self.counting, 1.)

    def on_reset(self):
        self.root.msg_text = "Victory! Press any key to restart..."
        Clock.unschedule(self.counting)
        self.root.clock_time = 0
        self.should_restart = True

    def on_stop(self):
        if self.connection is not None:
            self.connection.transport.loseConnection()
        return True


if __name__ == '__main__':
    GameClientApp().run()
