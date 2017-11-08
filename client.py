import zmq
import sys
import time
import threading
import zlib
import pickle


class UpdateTask(threading.Thread):
    """ClientTask"""
    def __init__(self, socket):
        self.socket = socket
        threading.Thread.__init__(self)

    def run(self):
        try:
            while True:
                z = self.socket.recv()
                p = zlib.decompress(z)
                game_state = pickle.loads(p)
                print(game_state)
        except zmq.error.ContextTerminated:
            print("Stop listening for updates")


client_id = sys.argv[1]

context = zmq.Context()
socket = context.socket(zmq.DEALER)
identity = 'worker-{0}'.format(client_id)
socket.identity = identity.encode('ascii')
socket.connect('tcp://localhost:5555')
print('Client {0} started'.format(identity))

up = UpdateTask(socket)
up.start()

for i in range(5):
    print('Req #%d sent..' % (i))
    socket.send_string(u'request #%d' % (i))
    time.sleep(1)

socket.close()
context.term()
up.join()
