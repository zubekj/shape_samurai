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
    PROGRESS_MARGIN = 0.1

    def __init__(self):
        """
        The player list will consist of a position tuple and progress index
        """
        self.shapes = [generate_shape(), generate_shape()]
        self.players = ([self.shapes[0][0], 0], [self.shapes[1][0], 0])

    def update(self, player_id, position):
        player = self.players[player_id]
        shape = self.shapes[player_id]
        player[0] = position

        if (player[1] < len(shape)
                and np.linalg.norm(np.array(shape[player[1]])
                                   - np.array(position)) <= self.RADIUS):
            player[1] += 1

        if abs(self.players[0][1]/len(self.shapes[0])
               - self.players[1][1]/len(self.shapes[1])) > self.PROGRESS_MARGIN:
            self.players[0][1] = 0
            self.players[1][1] = 0

        return (self.players[0][1] == len(self.shapes[0])
                and self.players[1][1] == len(self.shapes[1]))
