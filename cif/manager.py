
import multiprocessing as mp


class Manager(object):

    def __init__(self, target, threads=1):
        self.workers = []
        self.target = target
        self.threads = int(threads)

    def start(self):
        for n in range(self.threads):
            p = mp.Process(target=self.target().start)
            p.start()
            self.workers.append(p)

        return self.workers

    def stop(self):

        if hasattr(self, 'teardown'):
            self.teardown()

        for p in self.workers:
            p.terminate()

