import math
import numpy as np

class GameState(object):
    """
    GameState represent current state of the game. Game logic is implemented
    here.
    """
    RADIUS = 0.01

    def __init__(self):
        self.player_a = (0, 0)
        self.player_b = (0, 0)
        self.shape = [[0,0], [0.5, 1], [1,0], [0, 0]]
        self.player_a_progress = 0
        self.player_b_progress = 0

    def update(self, player_name, position):
        if player_name == "a":
            self.player_a = position
            if self.check_progress(self.shape[self.player_a_progress], self.player_a):
                self.player_a_progress += 1

        else:
            self.player_b = position
            if self.check_progress(self.shape[self.player_b_progress], self.player_b):
                self.player_b_progress += 1

    def check_progress(self, checkpoint, position):
        dist = np.linalg.norm(np.array(checkpoint) - np.array(position))
        return dist <= self.RADIUS