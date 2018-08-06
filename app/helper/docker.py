from abc import ABC, abstractmethod
from datetime import datetime
from helper.elasticsearch import ElasticHelper
from threading import Thread, RLock
import docker
import json
import logging
import re

lock = RLock()
logger = logging.getLogger("logpycker")

class DockerHelper:
    client = docker.from_env()
    date_pattern = re.compile('\[?(\d{4}[-/]\d{2}[-/]\d{2})?T?\s*((?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})(?:[,.]+(?P<microsecond>\d{3}(?:\d{3})?))?)(\s*\+\d{4})?Z?\]?\s*')


    # Return container list
    @staticmethod
    def getContainers():
        try:
            return DockerHelper.client.containers.list()
        except docker.errors.APIError:
            return []

    @staticmethod
    def hasDate(message):
        matches = DockerHelper.date_pattern.search( message )
        return False if matches is None else True

    # Extract date from message
    @staticmethod
    def parseDate(message):
        date = datetime.today()
        matches = DockerHelper.date_pattern.search( message )
        if matches is not None:
            date.replace(hour=int(matches.group('hour')))\
                .replace(minute=int(matches.group('minute')))\
                .replace(second=int(matches.group('second')))
            if matches.group('microsecond'):
                date = date.replace(microsecond=int(matches.group('microsecond'))*1000 if len(matches.group('microsecond')) == 3 else int(matches.group('microsecond')))
        
        return date.strftime("%Y-%m-%dT%H:%M:%S.%f%Z")

    # Delete date from message
    @staticmethod
    def cleanDate(message):
        return DockerHelper.date_pattern.sub("", message)


class ContainerHelper(Thread):
    def __init__(self, container, client=docker.from_env()):
        Thread.__init__(self)
        self.client = client
        self.container = container
        self.previousLog = None
        self.logs = []
        self.skeleton = self.buildSkeleton()

    def isMultilineEnabled(self):
        self.container.reload()
        self.labels = self.container.labels
        if "log.pycker.multiline.enabled" in self.labels:
            return json.loads( self.labels["log.pycker.multiline.enabled"] )
        else:
            return False

    def buildSkeleton(self):
        logSkeleton = {}
        self.labels = self.container.labels

        # Identify networks
        logSkeleton["networks"] = [ network for network in self.container.attrs["NetworkSettings"]["Networks"] ]

        # Identify compose services
        # logger.debug( json.dumps( self.container.attrs, ensure_ascii=False, indent=4 ) )
        if "com.docker.compose.project" in self.labels: 
            logSkeleton["project"] = self.labels["com.docker.compose.project"]
        if "com.docker.compose.service" in self.labels: 
            logSkeleton["service"] = self.labels["com.docker.compose.service"]
        if "com.docker.compose.container-number" in self.labels: 
            logSkeleton["task"] = self.labels["com.docker.compose.container-number"]

        # Identify stack services
        if "com.docker.swarm.service.name" in self.labels:
            logSkeleton["service"] = self.labels["com.docker.swarm.service.name"]
        if "com.docker.stack.namespace" in self.labels:
            logSkeleton["project"] = self.labels["com.docker.stack.namespace"]
            logSkeleton["service"] = logSkeleton["service"].replace(logSkeleton["project"] + "_", "")
        if "com.docker.swarm.task.id" in self.labels:
            logSkeleton["task"] = self.labels["com.docker.swarm.task.id"]

        return logSkeleton


    # https://regex101.com/
    def parseLogPattern(self, formattedLog):
        if "log.pycker.pattern" in self.labels:
            try:
                pattern = re.compile( self.labels["log.pycker.pattern"] )
                matches = pattern.search( formattedLog["message"] )
                if matches is not None:
                    for name, value in matches.groupdict().items():
                        formattedLog[name] = value
                        formattedLog["message"] = pattern.sub("", formattedLog["message"])
            except:
                logger.exception( "Error using log pattern : %s" % self.labels["log.pycker.pattern"] )

        return formattedLog

    def parseMultilineLog(self, message):
        if not DockerHelper.hasDate(message) and self.previousLog is not None:
            formattedLog = self.previousLog["entry"]
            formattedLog["message"] += message
            if not ElasticHelper().delete( self.previousLog["id"] ):
                raise
            return formattedLog
        else:
            return self.parseLog(message)

    def parseLog(self, message):
        formattedLog = dict(self.skeleton)
        formattedLog["date"] = DockerHelper.parseDate(message)
        formattedLog["message"] = DockerHelper.cleanDate(message)
        formattedLog = self.parseLogPattern(formattedLog)

        return formattedLog

    def run(self):
        try:
            self.logs = self.container.logs(stream=True, tail=0)
        except:
            logger.error( "Unable to get logs for %s" % self.container.name )
            
        for log in self.logs:
            try:
                es = ElasticHelper()
                message = log.decode("utf-8")
                labels = self.container.labels
                if self.isMultilineEnabled():
                    formattedLog = self.parseMultilineLog( message )
                else:
                    formattedLog = self.parseLog( message )

                # TODO : Save to queue ?
                result = es.register(formattedLog)
                if result is not None and result["result"] == "created":
                    self.previousLog = {
                        "id": result["_id"],
                        "entry": formattedLog
                    }
            except:
                logger.exception("Container Exception")
