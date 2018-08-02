#!/usr/local/bin/python

from helper.docker import DockerHelper, ContainerHelper
from helper.elasticsearch import ElasticHelper
import logging
import os
import re
import signal
import sys
import time
import types


# Configure logging
logger = logging.getLogger("logpycker")
logger.setLevel(logging.DEBUG)

# Create console handler and set formatter
handler = logging.StreamHandler()
handler.setFormatter( logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s") )

# Add handler to logegr
logger.addHandler( handler )

class LogPycker:
    docker = DockerHelper()
    # excludes = ['pyckerlogs_logger:latest', 'xylphid/log-pycker:latest', 'docker.elastic.co/elasticsearch/elasticsearch:6.3.1']
    threads = {}
    status = "running"

    def __init__(self):
        while LogPycker.status == 'running':
            self.cleanThreads()
            self.browseContainers()
            time.sleep(5)

    def isIgnored(self, container):
        filters = os.getenv("tags.ignore", None)
        try:
            filters = filters.split(",")

            for pattern in filters:
                pattern = re.compile(pattern.strip())
                if len(list(filter(pattern.match, container.image.attrs["RepoTags"]))):
                    return True
        finally:
            return False

    def browseContainers(self):
        for container in DockerHelper.getContainers():
            if self.isIgnored(container):
                pass
            elif container.name not in LogPycker.threads:
                logger.info( "Attaching to : %s" % container.name )
                helper = ContainerHelper(container)
                LogPycker.threads[container.name] = helper
                LogPycker.threads[container.name].start()

    def cleanThreads(self):
        for name in LogPycker.threads:
            if not LogPycker.threads[name].is_alive():
                logger.info( "Releasing : %s" % name )
                if isinstance(LogPycker.threads[name].logs, types.GeneratorType):
                    LogPycker.threads[name].logs.close()
                LogPycker.threads[name].join()

        # Reduce threads dict
        LogPycker.threads = { name:LogPycker.threads[name] for name in LogPycker.threads if LogPycker.threads[name].is_alive() }

    @staticmethod
    def terminate():
        LogPycker.status = 'terminated'
        for name in LogPycker.threads:
            if isinstance(LogPycker.threads[name].logs, types.GeneratorType):
                LogPycker.threads[name].logs.close()
            LogPycker.threads[name].join()
            while (LogPycker.threads[name].is_alive()):
                time.sleep(1)
            logger.info("  %s : Done " % name)


def main():
    # React on signal
    signal.signal(signal.SIGINT, terminate)
    signal.signal(signal.SIGTERM, terminate)

    # Set ES logs to critical only
    logging.getLogger("elasticsearch").setLevel(logging.CRITICAL)
    # Start aggregator
    watcher = LogPycker()

def terminate(signal, frame):
    logger.info( "Gracefully stopping threads : ")
    LogPycker.terminate()
    kill(signal, frame)

def kill(signal, frame):
    logger.info( "Program terminated !")
    sys.exit(0)

if __name__ == "__main__":
    main()