import math


class GameState(object):
    """
    GameState represent current state of the game. Game logic is implemented
    here.
    """
    RADIUS = 0.04
    PROGRESS_MARGIN = 0.2

    def __init__(self, shape_a, shape_b, use_margin=True):
        """
        The player list consists of a position tuple and progress index
        """
        self.shapes = (self.interpolate_shape(shape_a),
                       self.interpolate_shape(shape_b))
        self.players = ([self.shapes[0][0], 0], [self.shapes[1][0], 0])
        self.use_margin = use_margin

    def dist(self, a, b):
        return ((a[0]-b[0])**2+(a[1]-b[1])**2)**0.5

    def interpolate_shape(self, verts, density=0.01):
        points = []

        for i in range(len(verts)):
            cv, nv = verts[i], verts[(i+1) % len(verts)]
            points.append(cv)
            split_number = math.floor(self.dist(cv, nv) / density)
            if (split_number == 0):
                continue

            x, y = cv
            x_delta = (nv[0] - cv[0]) / split_number
            y_delta = (nv[1] - cv[1]) / split_number
            for _ in range(split_number):
                x += x_delta
                y += y_delta
                points.append((x, y))

        return points

    def update(self, player_id, position):
        player = self.players[player_id]
        shape = self.shapes[player_id]
        player[0] = position

        # Is next point visited?
        if (player[1] < len(shape)
                and self.dist(shape[player[1]], position) <= self.RADIUS):
            player[1] += 1

        # Is distance exceeded?
        if self.use_margin and (abs(self.players[0][1]/len(self.shapes[0])
                                - self.players[1][1]/len(self.shapes[1]))
                                > self.PROGRESS_MARGIN):
            self.players[0][1] = 0
            self.players[1][1] = 0

        # Do both players finished?
        return (self.players[0][1] == len(self.shapes[0])
                and self.players[1][1] == len(self.shapes[1]))
