class RocketMQClient:
    def __init__(self, name_server: str):
        self.name_server = name_server
        self.producer = self.create_producer()
        self.consumer = self.create_consumer()

    def create_producer(self):
        return Producer(self.name_server)

    def create_consumer(self):
        return Consumer(self.name_server)