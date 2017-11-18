import math
import numpy as np

class GameState(object):
    """
    GameState represent current state of the game. Game logic is implemented
    here.
    """
    RADIUS = 0.01
    PROGRESS_MARGIN = 20

    def __init__(self, player_a_pos, player_b_pos, shape):
        """ 
        The player list will consist of a position tuple and progress index
        """
        
        self.player_dict = {"a": [player_a_pos, 0], "b": [player_b_pos, 0]}
        self.shape = shape

    def update(self, player_name, position):
        player = self.player_dict[player_name]
        player[0] = position

        if player[1] < len(self.shape) and self.check_radius(self.shape[player[1]], position):
            player[1] += 1

        if self.check_progress(self.player_dict["a"][1], self.player_dict["b"][1]):
            print("Players exceeded progress margin!")
        
    def check_radius(self, checkpoint, position):
        dist = np.linalg.norm(np.array(checkpoint) - np.array(position))
        return dist <= self.RADIUS

    def check_progress(self, progress_a, progress_b):
        return abs((progress_a - progress_b)) > self.PROGRESS_MARGIN

    def check_victory_condition(self):
        return self.player_dict["a"] == len(self.shape) and self.player_dict["b"] == len(self.shape)

