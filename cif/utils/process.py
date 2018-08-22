from multiprocessing import Process, Event


class MyProcess(Process):

    def __init__(self, **kwargs):
        Process.__init__(self)
        self.exit = Event()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        return self

    def terminate(self):
        self.exit.set()

    def stop(self):
        self.terminate()
