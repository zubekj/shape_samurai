import json
from datetime import datetime
from math import ceil

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.support import install_twisted_reactor

# fix for pyinstaller packages app to avoid ReactorAlreadyInstalledError
import sys
if 'twisted.internet.reactor' in sys.modules:
    del sys.modules['twisted.internet.reactor']
install_twisted_reactor()

from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver

from game_state import GameState
from logger import Logger


class GameServerProtocol(LineReceiver):
    """
    GameServerProtocol manages a single client connection.

    Posible states:
        * WAITLOGIN -- connection established, waiting for "login" message
        * READY -- client ready for game start
        * GAME -- client during gameplay
    """

    def __init__(self):
        super(LineReceiver, self).__init__()

    def connectionMade(self):
        # Do not accept connections from more than 2 clients.
        if len(self.factory.clients) >= 2:
            if self.transport is not None:
                self.transport.loseConnection()
            return

        self.id = len(self.factory.clients)
        self.factory.clients.append(self)
        self.state = "WAIT"

    def lineReceived(self, line):
        """
        Main protocol logic. In state WAITLOGIN server accepts only "ready"
        message. After two players login game starts. Messages from client
        after login are interpreted as compressed objects representing player
        moves.
        """
        line = line.decode("utf-8")
        if self.state == "WAIT":
            if line[:5] == "ready":
                self.set_ready()
                self.name = line[6:]
                #self.factory.app.label.text = "First client connected"
                if (len(self.factory.clients) == 2
                        and self.factory.clients[0].state == "READY"
                        and self.factory.clients[1].state == "READY"):
                    self.factory.app.start_game()
        elif self.state == "GAME":
            pos = [float(x) for x in line.split(",")]
            self.factory.app.player_move(self.id, self.name, pos)

    def sendLine(self, line):
        super(self.__class__, self).sendLine(line.encode('utf-8'))

    def send_game_state(self, game_state):
        msg = json.dumps(game_state)
        for i in range(ceil(float(len(msg))/self.MAX_LENGTH)):
            self.sendLine(msg[i*self.MAX_LENGTH:(i+1)*self.MAX_LENGTH])
        self.sendLine("json_end")

    def connectionLost(self, reason):
        self.factory.reset_connections()

    def set_ready(self):
        self.state = "READY"

    def set_wait(self):
        self.state = "WAIT"
        self.sendLine("reset")

    def set_game(self):
        self.state = "GAME"
        self.sendLine("start {0}".format(self.id))

    def set_finished(self):
        self.state = "FINISHED"
        self.sendLine("finish")


class GameServerFactory(Factory):
    """
    GameServerFactory keeps track of active connections and creates
    new GameServer object for each new connection.
    """

    def __init__(self, app):
        self.app = app
        self.clients = []

    def buildProtocol(self, addr):
        protocol = GameServerProtocol()
        protocol.factory = self
        return protocol

    def broadcast_game_state(self, game_state):
        """
        Broadcasts a game state to all active clients.
        """
        for client in self.clients:
            client.send_game_state(game_state)

    def reset_connections(self, *args):
        """
        Disconnects all clients, resets server to an initial state.
        """
        for client in self.clients:
            client.transport.loseConnection()
        self.clients = []
        self.app.label.text = "Server started"


class GameServerApp(App):
    """
    Game server application with simple GUI.
    """
    label = None
    button = None

    def build_config(self, config):
        config.setdefaults('config',
                           {'port': 8000,
                            'shapes_file': 'shape_library.json'})

    def build(self):
        self.layout = BoxLayout(orientation="vertical")
        self.label = Label(text="Enter session name", size=(100, 50),
                           size_hint=(1, None))
        self.session_text = TextInput(text='XXX', multiline=False,
                                      size=(100, 50), size_hint=(.8, None),
                                      pos_hint={"center_x": 0.5})
        self.button = Button(text="Start server", size=(200, 50),
                             size_hint=(None, None), pos_hint={"center_x": 0.5})
        self.layout.add_widget(Widget(size_hint=(1, 1)))
        self.layout.add_widget(self.label)
        self.layout.add_widget(self.session_text)
        self.layout.add_widget(self.button)
        self.layout.add_widget(Widget(size_hint=(1, 1)))
        self.server_factory = GameServerFactory(self)
        self.button.bind(on_press=self.start_server)
        self.logger = None

        return self.layout

    def start_server(self, *args):
        session_name = self.session_text.text
        if len(session_name) == 0:
            return

        self.label.text = "Server started"
        self.layout.remove_widget(self.session_text)
        self.button.text = "Reset connections"
        self.button.unbind(on_press=self.start_server)
        self.button.bind(on_press=self.server_factory.reset_connections)

        try:
            with open(self.config.get("config", "shapes_file")) as f:
                self.shapes = json.load(f)
        except FileNotFoundError:
            self.shapes = []
        self.current_shape = 0
        log_name = "{0}.txt".format(session_name)
        self.logger = Logger(log_name)
        self.logger.log_info("Building server, shape file {0}".format(
            self.config.get("config", "shapes_file")))

        reactor.listenTCP(self.config.getint("config", "port"),
                          self.server_factory)

    def start_game(self):
        clients = self.server_factory.clients
        if self.current_shape >= len(self.shapes):
            for client in clients:
                client.set_finished()
            self.logger.log_info("Game finished")
            return

        if (clients[0].name > clients[1].name):
            clients[0], clients[1] = clients[1], clients[0]
            clients[0].id = 0
            clients[1].id = 1

        shape_a, shape_b = self.shapes[self.current_shape]
        self.current_shape += 1
        self.game_state = GameState(shape_a, shape_b)

        for client in clients:
            client.set_game()
        self.server_factory.broadcast_game_state(
                {"shapes": self.game_state.shapes,
                 "players": self.game_state.players})

        text = "Game started, shape {0}/{1}".format(self.current_shape,
                                                    len(self.shapes))
        self.logger.log_info(text)
        self.label.text = text

    def player_move(self, player_id, player_name, move):
        if self.game_state is None:
            return
        if self.game_state.update(player_id, move):
            self.game_victory()
            return
        self.server_factory.broadcast_game_state(
                {"players": self.game_state.players})
        self.logger.log_info("player: {0}-{1}, "
                             "move: {2}".format(player_id, player_name, move))

    def game_victory(self):
        for client in self.server_factory.clients:
            client.set_wait()

    def on_stop(self):
        self.server_factory.reset_connections()
        if self.logger is not None:
            self.logger.stop()
        return True

if __name__ == '__main__':
    GameServerApp().run()
