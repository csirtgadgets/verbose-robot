
import multiprocessing as mp


class Manager(object):

    def __init__(self, target, threads=1, **kwargs):
        self.workers = []
        self.target = target
        self.threads = int(threads)

    def start(self, **kwargs):
        for n in range(self.threads):
            p = mp.Process(target=self.target(**kwargs).start)
            p.start()
            self.workers.append(p)

        return self.workers

    def stop(self):

        if hasattr(self, 'teardown'):
            self.teardown()

        for p in self.workers:
            p.terminate()
