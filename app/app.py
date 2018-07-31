#!/usr/local/bin/python

import docker
from helper.docker import DockerHelper, ContainerHelper
from helper.elasticsearch import ElasticHelper
from threading import RLock
import logging
import os
import signal
import sys
import time

lock = RLock()

# Configure logging
logger = logging.getLogger("logpycker")
logger.setLevel(logging.DEBUG)

# Create console handler and set formatter
handler = logging.StreamHandler()
handler.setFormatter( logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s") )

# Add handler to logegr
logger.addHandler( handler )

class LogAggregator:
    docker = DockerHelper()
    excludes = ['pyckerlogs_logger:latest', 'xylphid/log-pycker:latest', 'docker.elastic.co/elasticsearch/elasticsearch:6.3.1']
    threads = {}
    status = "running"

    def __init__(self):
        while LogAggregator.status == 'running':
            self.cleanThreads()
            self.browseContainers()
            time.sleep(5)

    def browseContainers(self):
        for container in DockerHelper.get_containers():
            # Ignore container ?
            tags = [value for value in container.image.attrs["RepoTags"] if value in self.excludes]
            if len(tags):
                pass
            elif container.name not in LogAggregator.threads:
                with lock:
                    logger.info( "Attaching to : %s" % container.name )
                    # print( "Attaching to : %s" % container.name )
                helper = ContainerHelper(container)
                LogAggregator.threads[container.name] = helper
                LogAggregator.threads[container.name].start()

    def cleanThreads(self):
        for name in LogAggregator.threads:
            if not LogAggregator.threads[name].is_alive():
                with lock:
                    logger.info( "Releasing : %s" % name )
                LogAggregator.threads[name].logs.close()
                LogAggregator.threads[name].join()

        # Reduce threads dict
        LogAggregator.threads = { name:LogAggregator.threads[name] for name in LogAggregator.threads if LogAggregator.threads[name].is_alive() }

    @staticmethod
    def terminate():
        LogAggregator.status = 'terminated'
        for name in LogAggregator.threads:
            with lock:
                LogAggregator.threads[name].logs.close()
                LogAggregator.threads[name].join()
                while (LogAggregator.threads[name].is_alive()):
                    time.sleep(1)
                logger.info("- %s : Done", name)


def main():
    # React on signal
    signal.signal(signal.SIGINT, terminate)
    signal.signal(signal.SIGTERM, terminate)

    # Set ES logs to critical only
    logging.getLogger("elasticsearch").setLevel(logging.CRITICAL)
    # Start aggregator
    watcher = LogAggregator()

def terminate(signal, frame):
    logging.info( "Gracefully stopping threads : ")
    LogAggregator.terminate()
    kill(signal, frame)

def kill(signal, frame):
    logging.info( "Program terminated !")
    sys.exit(0)

if __name__ == "__main__":
    main()