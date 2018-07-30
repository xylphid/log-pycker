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


class LogAggregator:
    docker = DockerHelper()
    excludes = ['pyckerlogs_logger:latest', 'xylphid/log-pycker:latest', 'docker.elastic.co/elasticsearch/elasticsearch:6.3.1']
    threads = {}
    status = "running"

    def __init__(self):
        while LogAggregator.status == 'running':
            self.cleanThreads()
            self.browseContainers()
            with lock:
                print( 'Threads : %s' % len(LogAggregator.threads) )
            time.sleep(5)

    def browseContainers(self):
        for container in DockerHelper.get_containers():
            # Ignore container ?
            tags = [value for value in container.image.attrs["RepoTags"] if value in self.excludes]
            if len(tags):
                pass
            elif container.name not in LogAggregator.threads:
                with lock:
                    print( "Attaching to : %s" % container.name )
                helper = ContainerHelper(container)
                LogAggregator.threads[container.name] = helper
                LogAggregator.threads[container.name].start()

    def cleanThreads(self):
        for name in LogAggregator.threads:
            if not LogAggregator.threads[name].is_alive():
                with lock:
                    print( "Releasing : %s" % name )
                LogAggregator.threads[name].logs.close()
                LogAggregator.threads[name].join()

        # Reduce threads dict
        LogAggregator.threads = { name:LogAggregator.threads[name] for name in LogAggregator.threads if LogAggregator.threads[name].is_alive() }
        with lock:
            print( 'Threads : %s' % len(LogAggregator.threads) )

    @staticmethod
    def terminate():
        LogAggregator.status = 'terminated'
        for name in LogAggregator.threads:
            with lock:
                print("- %s :" % name, end='')
                LogAggregator.threads[name].logs.close()
                LogAggregator.threads[name].join()
                while (LogAggregator.threads[name].is_alive()):
                    print( ".", end='')
                print(" Done")




class QueueHelper:
    queue = {
        'host': os.getenv("QUEUE_HOST", "queue"),
        'name': os.getenv("pycker")
    }

    def __init__(seld):
        self.connection = pika.BlockingConnection(pika.ConnectioParameters( self.queue.host ))
        self.channel = connection.channel
        self.channel.queue_declare( queue=self.queue.name )

    @staticmethod
    def save(self, message):
        self.connection = pika.BlockingConnection(pika.ConnectioParameters( self.queue.host ))
        self.channel = connection.channel
        self.channel.queue_declare( queue=self.queue.name )
        self.basic_publish(exchange='', routing_key=self.queue.name, body=message)
        self.connection.close()


def main():
    # React on signal
    signal.signal(signal.SIGINT, terminate)
    signal.signal(signal.SIGTERM, kill)

    # Set ES logs to critical only
    logging.getLogger("elasticsearch").setLevel(logging.CRITICAL)
    # Start aggregator
    watcher = LogAggregator()

def terminate(signal, frame):
    try:
        print( "\nGracefully stopping threads : ")
        LogAggregator.terminate()
        sys.exit(0)
    except:
        pass

def kill(signal, frame):
    print( "Program terminated !")
    sys.exit(0)

if __name__ == "__main__":
    main()