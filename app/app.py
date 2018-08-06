#!/usr/local/bin/python

from helper.docker_helper import ContainerHelper
import docker
import logging
import os
import re
import signal
import sys
import time
import types


class LogPycker:
    threads = {}

    def __init__(self):
        self.__init_signals__()
        self.set_loggers()
        self.docker = docker.from_env()

    def __init_signals__(self):
        # React on signal
        signal.signal(signal.SIGINT, self.terminate)
        signal.signal(signal.SIGTERM, self.terminate)

    def set_loggers(self):
        # Set ES logs to critical only
        logging.getLogger("elasticsearch").setLevel(logging.CRITICAL)

        # Configure logging
        self.logger = logging.getLogger("logpycker")
        self.logger.setLevel(logging.DEBUG)
        # Create console handler and set formatter
        handler = logging.StreamHandler()
        handler.setFormatter( logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s") )
        # Add handler to logegr
        self.logger.addHandler( handler )

    def run(self):
        self.status = "running"
        while self.status == 'running':
            self.clean_threads()
            self.browse_containers()
            time.sleep(5)

    def is_ignored(self, container):
        filters = os.getenv("tags.ignore", None)
        try:
            filters = filters.split(",")

            for pattern in filters:
                pattern = re.compile(pattern.strip())
                if len(list(filter(pattern.match, container.image.attrs["RepoTags"]))):
                    return True
        finally:
            return False

    def browse_containers(self):
        for container in self.docker.containers.list():
            if self.is_ignored(container):
                pass
            elif container.name not in self.threads:
                self.logger.info( "Attaching to : %s" % container.name )
                helper = ContainerHelper(container)
                self.threads[container.name] = helper
                self.threads[container.name].start()

    def clean_threads(self):
        for name in self.threads:
            if not self.threads[name].is_alive():
                self.logger.info( "Releasing : %s" % name )
                if isinstance(self.threads[name].logs, types.GeneratorType):
                    self.threads[name].logs.close()
                self.threads[name].join()

        # Reduce threads dict
        self.threads = { name:self.threads[name] for name in self.threads if self.threads[name].is_alive() }

    def terminate(self, signal, frame):
        self.status = 'terminated'
        self.logger.info( "Gracefully stopping threads : ")
        for name in self.threads:
            if isinstance(self.threads[name].logs, docker.types.daemon.CancellableStream):
                self.threads[name].logs.close()
            self.threads[name].join()
            while (self.threads[name].is_alive()):
                time.sleep(1)
            self.logger.info("  %s : Done " % name)

        self.kill(signal, frame)

    def kill(self, signal, frame):
        self.logger.info( "Program terminated !")
        sys.exit(0)


def main():
    watcher = LogPycker()
    # Start Pycker
    watcher.run()

if __name__ == "__main__":
    main()