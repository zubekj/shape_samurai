#
#   Hello World server in Python
#   Binds REP socket to tcp://*:5555
#   Expects b"Hello" from client, replies with b"World"
#

import time
import zmq
import pickle
import zlib
import threading


class BroadcastUpdatesTask(threading.Thread):
    """ClientTask"""
    def __init__(self, socket):
        self.socket = socket
        self.active = True
        threading.Thread.__init__(self)

    def run(self):
        while self.active:
            p = pickle.dumps(game_state)
            z = zlib.compress(p)
            for ident in clients:
                socket.send_multipart((ident, z))
            time.sleep(1)


game_state = {"a": (0, 0), "b": (1, 1)}

clients = set()

context = zmq.Context()
socket = context.socket(zmq.ROUTER)
socket.bind("tcp://*:5555")

bc = BroadcastUpdatesTask(socket)
bc.start()

print("Starting server")
try:
    while True:
        ident, message = socket.recv_multipart()
        print("Received request: {0} from {1}".format(message, ident))
        clients.add(ident)

except KeyboardInterrupt:
    print("Interrupted")
finally:
    bc.active = False
    bc.join()
    socket.close()
    context.term()
