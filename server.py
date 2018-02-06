from kivy.support import install_twisted_reactor

install_twisted_reactor()

from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

import pickle
import zlib
import datetime
import json

from game_state import GameState
from logger import Logger

class GameServerProtocol(LineReceiver):
    """
    GameServer manages single client connection.

    Posible states:
        * WAITLOGIN -- connection established, waiting for "login" message
        * READY -- client ready for game start
        * GAME -- client during gameplay
    """

    def __init__(self, factory):
        self.factory = factory
        # Do not accept connections from more than 2 clients.
        if len(self.factory.clients) >= 2:
            self.transport.loseConnection()
            return

        self.name = len(self.factory.clients)
        self.factory.clients[self.name] = self
        self.state = "WAIT"

    def lineReceived(self, line):
        """
        Main protocol logic. In state WAITLOGIN server accepts only "login"
        message. After two players login game starts. Messages from client
        after login are interpreted as compressed objects representing player
        moves.
        """
        line = line.decode("utf-8")
        if self.state == "WAIT":
            if line == "ready":
                self.set_ready()
                #self.factory.app.label.text = "First client connected"
                if (len(self.factory.clients) == 2
                        and self.factory.clients[0].state == "READY"
                        and self.factory.clients[1].state == "READY"):
                    self.factory.app.start_game()
        elif self.state == "GAME":
            pos = [float(x) for x in line.split(",")]
            self.factory.app.player_move(self.name, pos)

    def sendLine(self, line):
        super(self.__class__, self).sendLine(line.encode('utf-8'))

    def send_game_state(self, game_state):
        self.sendLine(json.dumps(game_state))

    def connectionLost(self, reason):
        self.factory.reset_connections()

    def set_ready(self):
        self.state = "READY"

    def set_wait(self):
        self.state = "WAIT"
        self.sendLine("reset")

    def set_game(self):
        self.state = "GAME"
        self.sendLine("start")


class GameServerFactory(Factory):
    """
    GameServerFactory keeps track of active connections and creates
    new GameServer object for each new connection.
    """

    def __init__(self, app):
        self.app = app
        self.clients = {}

    def buildProtocol(self, addr):
        return GameServerProtocol(self)

    def broadcast_game_state(self, game_state):
        """
        Broadcasts a game state to all active clients.
        """
        for client in self.clients.values():
            client.send_game_state(game_state)

    def reset_connections(self, *args):
        """
        Disconnects all clients, resets server to an initial state.
        """
        for client in self.clients.values():
            client.transport.loseConnection()
        self.clients = {}
        self.app.label.text = "Server started\n"


class GameServerApp(App):
    """
    Game server application with simple GUI.
    """
    label = None
    button = None

    def build(self):
        layout = BoxLayout(orientation="vertical")
        self.label = Label(text="Server started\n")
        self.button = Button(text="Reset", size=(100, 50), size_hint=(1, None))
        layout.add_widget(self.label)
        layout.add_widget(self.button)
        self.server_factory = GameServerFactory(self)
        self.button.bind(on_press=self.server_factory.reset_connections)

        with open("server_config.json") as f:
            config = json.load(f)
        reactor.listenTCP(config["listenPort"], self.server_factory)

        self.logger = Logger()
        self.logger.log_info("Building server")
        return layout

    def start_game(self):
        self.label.text = "Game started\n"
        player_a_pos = (0, 0)
        player_b_pos = (0, 0)
        self.game_state = GameState(player_a_pos, player_b_pos)
        for client in self.server_factory.clients.values():
            client.set_game()
        self.server_factory.broadcast_game_state(
                {"shape": self.game_state.shape,
                 "players": self.game_state.players})
        self.logger.log_info("Game started")

    def player_move(self, player_name, move):
        if self.game_state is None:
            return

        self.game_state.update(player_name, move)
        if self.game_state.check_victory_condition():
            self.game_victory()
        self.server_factory.broadcast_game_state(
                {"players": self.game_state.players})
        self.logger.log_info("player: {0}, "
                             "move: {1}".format(player_name, move))

    def game_victory(self):
        for client in self.server_factory.clients.values():
            client.set_wait()

    def on_stop(self):
        self.server_factory.reset_connections()
        self.logger.stop()
        return True

if __name__ == '__main__':
    GameServerApp().run()
