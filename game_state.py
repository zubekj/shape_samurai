import math
import numpy as np

from shape_generator import generatePolygon, generatePolygonShapePoints

def generate_shape():
    verts_array = generatePolygon(aveRadius=0.6, irregularity=0.5, spikeyness=0.4, numVerts=7)
    shape = generatePolygonShapePoints(verts=verts_array, density=0.01)
    return shape


class GameState(object):
    """
    GameState represent current state of the game. Game logic is implemented
    here.
    """
    RADIUS = 0.04
    PROGRESS_MARGIN = 20

    def __init__(self, player_a_pos, player_b_pos):
        """
        The player list will consist of a position tuple and progress index
        """
        self.shape = generate_shape()
        self.progress_goal = len(self.shape)
        self.player_dict = {"a": [self.shape[0], 0], "b": [self.shape[0], 0]}

    def update(self, player_name, position):
        player = self.player_dict[player_name]
        player[0] = position

        if player[1] < self.progress_goal and self.check_radius(self.shape[player[1]], position):
            player[1] += 1

        if self.check_progress(self.player_dict["a"][1], self.player_dict["b"][1]):
            self.reset_progress()

    def reset_progress(self):
        self.player_dict["a"][1] = 0
        self.player_dict["b"][1] = 0

    def check_radius(self, checkpoint, position):
        dist = np.linalg.norm(np.array(checkpoint) - np.array(position))
        return dist <= self.RADIUS

    def check_progress(self, progress_a, progress_b):
        return abs((progress_a - progress_b)) > self.PROGRESS_MARGIN

    def check_victory_condition(self):
        return (self.player_dict["a"][1] == self.progress_goal) and (self.player_dict["b"][1] == self.progress_goal)

