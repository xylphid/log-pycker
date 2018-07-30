#!/usr/local/bin/python

# from abc import ABC, abstractmethod
# from datetime import datetime
import docker
from helper.docker import DockerHelper, ContainerHelper
from helper.elasticsearch import ElasticHelper
from threading import RLock
# import json
import logging
import os
# import pika # RabbitMQ
# import re
import signal
import sys
import time
# import traceback
# import urllib3

lock = RLock()

# class DateHelper:
#     @staticmethod
#     def parse_date(self, message):
#         date = datetime.today()
#         matches = DockerHelper.date_pattern.search(message)
#         if matches is not None:
#             date.replace(hour=int(matches.group('hour')))\
#                 .replace(minute=int(matches.group('minute')))\
#                 .replace(second=int(matches.group('second')))
#             if matches.group('microsecond'):
#                 date = date.replace(microsecond=int(matches.group('microsecond'))*1000 if len(matches.group('microsecond')) == 3 else int(matches.group('microsecond')))
        
#         return date.strftime("%Y-%m-%dT%H:%M:%S.%f%Z")

#     @staticmethod
#     def clean_date(self, message):
#         return DockerHelper.date_pattern.sub("", message)

# class DockerHelper(Thread, ABC):
#     date_pattern = re.compile('^\[?(\d{4}[-/]\d{2}[-/]\d{2})?T?\s*((?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})(?:[,.]+(?P<microsecond>\d{3}(?:\d{3})?))?)(\s*\+\d{4})?Z?\]?\s*')

#     def __init__(self, client=docker.from_env()):
#         Thread.__init__(self)
#         self.client = client

#     @abstractmethod
#     def run(self):
#         pass

#     def parse_date(self, message):
#         date = datetime.today()
#         matches = DockerHelper.date_pattern.search(message)
#         if matches is not None:
#             date.replace(hour=int(matches.group('hour')))\
#                 .replace(minute=int(matches.group('minute')))\
#                 .replace(second=int(matches.group('second')))
#             if matches.group('microsecond'):
#                 date = date.replace(microsecond=int(matches.group('microsecond'))*1000 if len(matches.group('microsecond')) == 3 else int(matches.group('microsecond')))
        
#         return date.strftime("%Y-%m-%dT%H:%M:%S.%f%Z")

#     def clean_date(self, message):
#         return DockerHelper.date_pattern.sub("", message)

# class ContainerHelper(DockerHelper):

#     def __init__(self, container, client=docker.from_env()):
#         DockerHelper.__init__(self, client)
#         self.container = container
#         self.skeleton = self.build_sekeleton() 

#     def build_sekeleton(self):
#         logSkeleton = {}
#         labels = self.container.labels
#         # print( json.dumps( labels, ensure_ascii=False, indent=4 ) )
#         if "com.docker.compose.project" in labels: 
#             logSkeleton["project"] = labels["com.docker.compose.project"]
#         if "com.docker.compose.service" in labels: 
#             logSkeleton["service"] = labels["com.docker.compose.service"]
#         if "com.docker.compose.container-number" in labels: 
#             logSkeleton["number"] = labels["com.docker.compose.container-number"]

#         return logSkeleton

#     def run(self):
#         print("%s : Start following logs" % self.container.name)
#         self.logs = self.container.logs(stream=True, tail=0)
#         for log in self.logs:
#             try:
#                 formattedLog = dict(self.skeleton)
#                 formattedLog["date"] = self.parse_date(log.decode("utf-8"))
#                 formattedLog["message"] = self.clean_date(log.decode("utf-8")).strip()

#                 # TODO : Save to queue
#                 es = ElasticHelper()
#                 es.register(formattedLog)
#                 # with lock:
#                 #     print( json.dumps( formattedLog, ensure_ascii=False, indent=4 ) )
#             except:
#                 print("Exception caught")
#                 # traceback.print_exc()
#                 print("=============================================")


#     def stop(self):
#         self.logs.close()


class LogAggregator:
    docker = DockerHelper()
    excludes = ['pyckerlogs_logger:latest', 'xylphid/log-pycker:latest', 'docker.elastic.co/elasticsearch/elasticsearch:6.3.1']
    threads = {}

    def __init__(self):
        while 1:
            self.browseContainers()
            self.cleanThreads()
            with lock:
                print( 'Threads : %s' % len(LogAggregator.threads) )
            time.sleep(5)

    def browseContainers(self):
        for container in DockerHelper.get_containers():
            # Ignore container ?
            tags = [value for value in container.image.attrs["RepoTags"] if value in self.excludes]
            if len(tags):
                pass
            elif container.status == "exited":
                with lock:
                    print( "Cleaning : %s" % container.name )
                LogAggregator.threads[container.name].logs.close()
                LogAggregator.threads[container.name].join()
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
        self.threads = { name:self.threads[name] for name in self.threads if self.threads[name].is_alive() }
        with lock:
            print( 'Threads : %s' % len(LogAggregator.threads) )

    @staticmethod
    def terminate():
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
        print( "\nClosing threads : ")
        LogAggregator.terminate()
        sys.exit(0)
    except:
        pass

def kill(signal, frame):
    print( "Kill program...")
    sys.exit(0)

if __name__ == "__main__":
    main()