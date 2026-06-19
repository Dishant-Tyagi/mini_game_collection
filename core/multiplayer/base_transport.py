class BaseTransport:
    """
    Abstract transport layer.
    LAN, Online, or future transports must inherit this.
    """

    def __init__(self, on_receive_callback):
        self.on_receive = on_receive_callback

    def start(self):
        raise NotImplementedError

    def send(self, data: dict):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError
