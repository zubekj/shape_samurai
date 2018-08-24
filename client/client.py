import json

from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty, Clock, ObjectProperty,\
                            ListProperty, StringProperty
from kivy.support import install_twisted_reactor

# fix for pyinstaller packages app to avoid ReactorAlreadyInstalledError
import sys
if 'twisted.internet.reactor' in sys.modules:
    del sys.modules['twisted.internet.reactor']
install_twisted_reactor()

from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver


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
            if line[:5] == "start":
                self.factory.app.root.player_id = line[6]
                self.set_game()
            elif line == "finish":
                self.set_finished()
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
        LineReceiver.sendLine(self, line.encode('utf-8'))

    def send_player_position(self, pos):
        self.sendLine("{0},{1}".format(*pos))

    def set_ready(self):
        self.state = "READY"
        self.sendLine("ready {0}".format(self.factory.app.player_name))

    def set_wait(self):
        self.state = "WAIT"
        self.factory.app.on_reset()

    def set_game(self):
        self.state = "GAME"
        self.factory.app.on_game_start()

    def set_finished(self):
        self.state = "FINISHED"
        self.factory.app.on_connection_lost()


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
        Clock.schedule_once(lambda _: self.app.connect_to_server(), 1.)


class RootLayout(BoxLayout):
    """
    RootLayout is the main widget of game window. Sprites are drawn here.
    It captures user input.
    """
    drawing_container = ObjectProperty(None)
    clock_time = NumericProperty(0)
    score = NumericProperty(0)
    msg_text = StringProperty("Waiting for server")
    line_a = ListProperty([0, 0])
    line_b = ListProperty([0, 0])
    progress_a = NumericProperty(0)
    progress_b = NumericProperty(0)
    cursor_a = ListProperty((0, 0))
    cursor_b = ListProperty((0, 0))
    distance = NumericProperty(0)
    player_id = StringProperty("")

    def __init__(self, **kwargs):
        self.app = App.get_running_app()
        self.players = None
        self.shapes = None
        self.popup_label = Label(text="Touch to start", font_size="32sp",
                                 halign="center")
        self.popup = Popup(title="", content=self.popup_label,
                           auto_dismiss=False, size_hint=(0.5, 0.5))
        self.popup.bind(on_touch_down=lambda *args: self.app.key_pressed())
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
        super(BoxLayout, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        pos = self.from_screen_coords(touch.x, touch.y)
        mrg = 0.04
        if -mrg <= pos[0] <= 1+mrg and -mrg <= pos[1] <= 1+mrg and self.shapes:
            self.app.connection.send_player_position(pos)

    def refresh_shapes(self):
        if self.shapes is None:
            self.line_a = [0, 0]
            self.line_b = [0, 0]
            self.progress_a = 0
            self.progress_b = 0
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
        self.cursor_a = (a_pos[0], a_pos[1])
        self.cursor_b = (b_pos[0], b_pos[1])
        self.distance = (float(self.players[0][1])/len(self.shapes[0])
                         - float(self.players[1][1])/len(self.shapes[1]))

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

    def build_config(self, config):
        config.setdefaults('config', {
            'host': 'localhost',
            'port': 8000,
            'name': 'player_A'})

    def build_settings(self, settings):
        settings.add_json_panel('Shape Samurai', self.config,
                                "settings.json")

    def on_config_change(self, config, section, key, value):
        self.connect_to_server()

    def on_start(self):
        self.player_name = self.config.get("config", "name")
        self.connect_to_server()

    def connect_to_server(self):
        if self.connection is None:
            reactor.connectTCP(self.config.get("config", "host"),
                               self.config.getint("config", "port"),
                               GameClientFactory(self))

    def key_pressed(self):
        if self.should_restart:
            self.should_restart = False
            self.connection.set_ready()

    def counting(self, value):
        self.root.clock_time += 1

    def on_connection(self, connection):
        self.connection = connection
        self.should_restart = True
        self.root.msg_text = "Connected"
        self.root.popup_label.text = "Connected\nTouch to start"
        self.root.popup.open()

    def on_connection_lost(self):
        self.root.shapes = None
        self.root.players = None
        if (self.connection is not None
                and self.connection.state == "FINISHED"):
            self.root.msg_text = "Game finished"
            self.root.popup.dismiss()
        else:
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
        self.root.msg_text = "Distance"
        self.root.popup.dismiss()
        Clock.unschedule(self.counting)
        Clock.schedule_interval(self.counting, 1.)

    def on_reset(self):
        self.root.msg_text = "Victory!"
        self.root.popup_label.text = "Victory!\nTouch to start"
        self.root.popup.open()
        Clock.unschedule(self.counting)
        self.root.score += int(1.0/((self.root.clock_time/60.0)**2+1)*20)
        self.root.clock_time = 0
        self.should_restart = True

    def on_stop(self):
        if self.connection is not None:
            self.connection.transport.loseConnection()
        return True

    def on_pause(self):
        return True

    def on_resume(self):
        pass

if __name__ == '__main__':
    GameClientApp().run()
