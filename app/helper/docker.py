from abc import ABC, abstractmethod
from datetime import datetime
from helper.elasticsearch import ElasticHelper
from threading import Thread, RLock
import docker
import re
import traceback


class DockerHelper:
    client = docker.from_env()
    date_pattern = re.compile('^\[?(\d{4}[-/]\d{2}[-/]\d{2})?T?\s*((?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})(?:[,.]+(?P<microsecond>\d{3}(?:\d{3})?))?)(\s*\+\d{4})?Z?\]?\s*')

    def __init__(self, client=docker.from_env()):
        self.client = client

    # Return container list
    @staticmethod
    def get_containers():
        return DockerHelper.client.containers.list()

    # Extract date from message
    @staticmethod
    def parse_date(message):
        date = datetime.today()
        matches = DockerHelper.date_pattern.search(message)
        if matches is not None:
            date.replace(hour=int(matches.group('hour')))\
                .replace(minute=int(matches.group('minute')))\
                .replace(second=int(matches.group('second')))
            if matches.group('microsecond'):
                date = date.replace(microsecond=int(matches.group('microsecond'))*1000 if len(matches.group('microsecond')) == 3 else int(matches.group('microsecond')))
        
        return date.strftime("%Y-%m-%dT%H:%M:%S.%f%Z")

    # Delete date from message
    @staticmethod
    def clean_date(message):
        return DockerHelper.date_pattern.sub("", message)


class ContainerHelper(Thread):
    def __init__(self, container, client=docker.from_env()):
        # DockerHelper.__init__(self, client)
        Thread.__init__(self)
        self.client = client
        self.container = container
        self.skeleton = self.build_sekeleton() 

    def build_sekeleton(self):
        logSkeleton = {}
        labels = self.container.labels
        # print( json.dumps( labels, ensure_ascii=False, indent=4 ) )
        if "com.docker.compose.project" in labels: 
            logSkeleton["project"] = labels["com.docker.compose.project"]
        if "com.docker.compose.service" in labels: 
            logSkeleton["service"] = labels["com.docker.compose.service"]
        if "com.docker.compose.container-number" in labels: 
            logSkeleton["number"] = labels["com.docker.compose.container-number"]

        return logSkeleton

    def run(self):
        print("%s : Start following logs" % self.container.name)
        self.logs = self.container.logs(stream=True, tail=0)
        for log in self.logs:
            try:
                formattedLog = dict(self.skeleton)
                formattedLog["date"] = DockerHelper.parse_date(log.decode("utf-8"))
                formattedLog["message"] = DockerHelper.clean_date(log.decode("utf-8")).strip()

                # TODO : Save to queue
                es = ElasticHelper()
                es.register(formattedLog)
                # with lock:
                #     print( json.dumps( formattedLog, ensure_ascii=False, indent=4 ) )
            except:
                print("Container Exception :")
                traceback.print_exc()
                print("=============================================")


    # def stop(self):
    #     self.logs.close()