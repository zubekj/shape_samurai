from kivy.support import install_twisted_reactor

install_twisted_reactor()

from twisted.internet import reactor
from twisted.internet import protocol
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

import pickle
import zlib
import datetime

from game_state import GameState
from logger import Logger

class GameServer(protocol.Protocol):
    """
    GameServer manages single client connection.

    Posible states:
        * WAITLOGIN -- connection established, waiting for "login" message
        * READY -- client ready for game start
        * GAME -- client during gameplay
    """

    def __init__(self, factory):
        self.factory = factory
        self.name = None
        self.state = "WAITLOGIN"

    def dataReceived(self, data):
        """
        Main protocol logic. In state WAITLOGIN server accepts only "login"
        message. After two players login game starts. Messages from client
        after login are interpreted as compressed objects representing player
        moves.
        """
        data = pickle.loads(zlib.decompress(data))
        if self.state == "WAITLOGIN" and data == "login":
            if len(self.factory.clients) < 2:
                if "a" not in self.factory.clients:
                    self.factory.clients["a"] = self
                    self.name = "a"
                else:
                    self.factory.clients["b"] = self
                    self.name = "b"
            elif self not in self.factory.clients.values():
                self.transport.loseConnection()
                return

            self.state = "READY"
            # No game state should be broadcasted until start_game() is called!
            #self.factory.broadcast_object(self.factory.app.game_state)
            #self.factory.app.label.text = "First client connected"
            if (len(self.factory.clients) == 2
                    and self.factory.clients["a"].state == "READY"
                    and self.factory.clients["b"].state == "READY"):
                self.factory.app.start_game()
        elif self.state == "GAME":
            self.factory.app.player_move(self.name, data)

    def connectionLost(self, reason):
        self.factory.reset_connections()

    def send_object(self, obj):
        """
        Sends pickled and compressed object to the client.
        """
        self.transport.write(zlib.compress(pickle.dumps(obj)))


class GameServerFactory(protocol.Factory):
    """
    GameServerFactory keeps track of active connections and creates
    new GameServer object for each new connection.
    """

    def __init__(self, app):
        self.app = app
        self.clients = {}

    def buildProtocol(self, addr):
        return GameServer(self)

    def broadcast_object(self, obj):
        """
        Broadcasts a Python object to all active clients.
        """
        for name in self.clients:
            self.clients[name].send_object(obj)

    def reset_connections(self, *args):
        """
        Disconnects all clients, resets server to an initial state.
        """
        for client in self.clients:
            self.clients[client].transport.loseConnection()
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
        reactor.listenTCP(8000, self.server_factory)
        self.logger = Logger()
        self.logger.log_info("Building server")
        return layout

    def start_game(self):
        self.label.text = "Game started\n"
        player_a_pos = (0, 0)
        player_b_pos = (0, 0)
        self.game_state = GameState(player_a_pos, player_b_pos)
        for client in self.server_factory.clients.values():
            client.state = "GAME"
        self.server_factory.broadcast_object(self.game_state)
        self.logger.log_info("Game started")

    def player_move(self, player_name, move):
        if self.game_state is None:
            return

        self.game_state.update(player_name, move)
        if self.game_state.check_victory_condition():
            self.game_victory()
        self.server_factory.broadcast_object(self.game_state)
        self.logger.log_info("player: {0}, "
                             "move: {1}".format(player_name, move))

    def game_victory(self):
        for client in self.server_factory.clients.values():
            client.state = "WAITLOGIN"
        self.server_factory.broadcast_object("victory")

    def on_stop(self):
        self.server_factory.reset_connections()
        self.logger.stop()
        return True

if __name__ == '__main__':
    GameServerApp().run()
