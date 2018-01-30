import logging
import logging.handlers
import queue


class Logger(object):

    def __init__(self):
        log_format = logging.Formatter('[%(asctime)s] %(levelname)-4s '
                                       '%(name)-4s %(message)s')
        log_format_default = ('[%(asctime)s] %(levelname)-4s %(name)-4s '
                              '%(message)s')
        logging.basicConfig(filename='joint_action_game.log',
                            format=log_format_default,
                            level=logging.INFO)

        que = queue.Queue(-1)  # no limit on size
        handler = logging.FileHandler('joint_action_game.log')
        handler.setFormatter(log_format)
        handler.setLevel(logging.INFO)

        self.listener = logging.handlers.QueueListener(que, handler)
        self.listener.start()

        queue_handler = logging.handlers.QueueHandler(que)

        self.root = logging.getLogger()
        self.root.addHandler(queue_handler)

    def log_info(self, info):
        self.root.info(info)

    def stop(self):
        self.listener.stop()
