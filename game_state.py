import math
import numpy as np

class GameState(object):
    """
    GameState represent current state of the game. Game logic is implemented
    here.
    """

    RADIUS = 10

    def __init__(self):
        self.player_a = (0, 0)
        self.player_b = (0, 0)
        self.interaction = False

    def update(self, player_name, move):
        if player_name == "a":
            self.player_a = move
        else:
            self.player_b = move

        self.interaction = (math.sqrt((self.player_a[0] - self.player_b[0])**2 +
                                      (self.player_a[1] - self.player_b[1])**2)
                            < self.RADIUS)
