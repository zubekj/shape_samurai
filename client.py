from kivy.graphics.vertex_instructions import Line, Ellipse
from kivy.properties import NumericProperty, Clock
from kivy.support import install_twisted_reactor
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.widget import Widget
from kivy.core.window import Window

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
    top_layout = BoxLayout(size_hint=(1, 0.1), orientation="horizontal")
    bottom_layout = AnchorLayout(size_hint=(1, 0.8))
    drawing_container = Widget(size_hint=(0.8, 0.8))
    clock_display = Label(text='00',
                          font_size=50)


    def __init__(self, app, **kwargs):
        self.app = app
        self.shape = None
        self.finger = None
        self.finger1 = None
        super(RootLayout, self).__init__(**kwargs)

        self._keyboard = Window.request_keyboard(
            self._keyboard_closed, self, 'text')

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

        
        color = (237.0 / 255.0, 212.0 / 255.0, 157.0 / 255.0, 1)
        color_a = (3.0 / 255.0, 164.0 / 255.0, 119 / 255.0, 0.5)
        color_b = (172.0 / 255.0, 2 / 255.0, 183.0 / 255.0, 0.5)
        color_start_point = (255.0 / 255.0, 0 / 255.0, 0 / 255.0)
        #color_start = (255.0 / 255.0, 0 / 255.0, 0 / 255.0)


        with self.canvas:
            Color(*color, mode='rgb')
            self.line = Line(width=5)
            self.line.cap = 'round'
            self.line.joint = 'round'
            self.line.joint_precision = 100
            Color(*color_start_point, mode='rgb')
            self.start_point = Ellipse(size=(15, 15), pos=(0, 0), group='group')
        

        with self.canvas.after:
            Color(*color_b, mode='rgba')
            self.line_green = Line(width=5)
            self.line_green.cap = 'round'
            self.line_green.joint = 'round'
            self.line_green.joint_precision = 100
            Color(*color_a, mode='rgba')
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

        #color = (40.0 / 255.0, 53.0 / 255.0, 147.0 / 255.0)
        color = (150.0 / 255.0, 150.0 / 255.0, 150.0 / 255.0)
        with self.bottom_layout.canvas.before:
            Color(*color, mode='rgb')
            self.bottom_ = Rectangle(size=self.bottom_layout.size,
                                      pos=self.bottom_layout.pos,
                                      source='Samurai.png')

        self.top_layout.height = 200
        self.drawing_container.bind(size=self._update_rect, pos=self._update_rect)
        self._keyboard.bind(on_key_down=self.key_down)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def key_down(self, keyboard, keycode, text, modifiers):
        self.app.key_pressed()

    def on_touch_down(self, touch):
        self.app.key_pressed()
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
            self.start_point.pos = (self.drawing_container.pos[0] + self.shape.shape[0][0] * self.drawing_container.width - 6,
                                    self.drawing_container.pos[1] + self.shape.shape[0][1] * self.drawing_container.height - 6)
            if self.finger:
                self.finger.pos = (a_pos[0] - 10, a_pos[1] - 10)
                if self.finger1:
                    self.finger1.pos = (b_pos[0] - 10, b_pos[1] - 10)
            else:
                color = (3.0 / 255.0, 164.0 / 255.0, 119 / 255.0)
                with self.drawing_container.canvas:
                    Color(*color, mode='rgb', group='group')
                    self.finger = Ellipse(size=(20, 20), pos=(a_pos[0] - 10, a_pos[1] - 10), group='group')

                if not self.finger1:
                    color = (172.0 / 255.0, 2 / 255.0, 183.0 / 255.0)
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
    should_restart = True
    in_game = False

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

    def key_pressed(self):
        if self.should_restart:
            self.should_restart = False
            self.connection.write(zlib.compress(pickle.dumps("login")))

    def counting(self, value):
        current_count = int(self.root.clock_display.text)
        current_count = current_count + 1
        self.root.clock_display.text = str(current_count)

    def on_connection(self, connection):
        self.connection = connection
        self.should_restart = True
        RootLayout.label.text = "Connected. Press any key to start the game..."

    def update_game(self, game_state):
        RootLayout.label.text = "Game Started"
        if not self.in_game:
            self.in_game = True
            Clock.unschedule(self.counting)
            Clock.schedule_interval(self.counting, 1.)

        if game_state == "victory":
            RootLayout.label.text = "Victory! Press any key to restart..."
            Clock.unschedule(self.counting)
            self.root.clock_display.text = "00"
            self.should_restart = True
            self.in_game = False
            #self.connection.write(zlib.compress(pickle.dumps("login")))
            return
        self.root.shape = game_state
        self.root.refresh(game_state)


    def on_stop(self):
        if self.connection is not None:
            self.connection.loseConnection()
        return True


if __name__ == '__main__':
    GameClientApp().run()
