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

from game_state import GameState


class GameServer(protocol.Protocol):
    """
    GameServer manages single client connection.
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
        if self.state == "WAITLOGIN":
            data = data.decode('utf-8')
            if len(self.factory.clients) < 2 and data == "login":
                if "a" not in self.factory.clients:
                    self.factory.clients["a"] = self
                    self.name = "a"
                else:
                    self.factory.clients["b"] = self
                    self.name = "b"
                self.state = "CONNECTED"
                self.factory.broadcast_object(self.factory.app.game_state)
                self.factory.app.label.text = "First client connected"
                if len(self.factory.clients) == 2:
                    self.factory.app.start_game()
            else:
                self.transport.loseConnection()
        else:
            data = pickle.loads(zlib.decompress(data))
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
        player_a_pos = (0, 0)
        player_b_pos = (0, 0)
        shape = [(0, 0), (0.05, 0), (0.1, 0), (0.15, 0), (0.20, 0), (0.25, 0), (0.30, 0), (0.35, 0), (0.4, 0), (0.45, 0), (0.5, 0)]
        self.game_state = GameState(player_a_pos, player_b_pos, shape)
        layout = BoxLayout(orientation="vertical")
        self.label = Label(text="Server started\n")
        self.button = Button(text="Reset", size=(100, 50), size_hint=(1, None))
        layout.add_widget(self.label)
        layout.add_widget(self.button)
        self.server_factory = GameServerFactory(self)
        self.button.bind(on_press=self.server_factory.reset_connections)
        reactor.listenTCP(8000, self.server_factory)
        return layout

    def start_game(self):
        self.label.text = "Game started\n"
        self.server_factory.broadcast_object(self.game_state)

    def player_move(self, player_name, move):
        self.game_state.update(player_name, move)
        if self.game_state.check_victory_condition():
            self.game_victory()
        self.server_factory.broadcast_object(self.game_state)

    def game_victory(self):
        print("Congratulations! Game Victory!")

    def on_stop(self):
        self.server_factory.reset_connections()
        return True

if __name__ == '__main__':
    GameServerApp().run()
