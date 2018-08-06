from abc import ABC, abstractmethod
from datetime import datetime
from helper.date_helper import *
from helper.es_helper import ElasticHelper
from threading import Thread, RLock
import docker
import json
import logging
import re

lock = RLock()

class ContainerHelper(Thread):
    def __init__(self, container, client=docker.from_env()):
        Thread.__init__(self)
        self.logger = logging.getLogger("logpycker")
        self.client = client
        self.container = container
        self.previousLog = None
        self.logs = []
        self.skeleton = self.build_skeleton()

    def is_multiline_enabled(self):
        self.container.reload()
        self.labels = self.container.labels
        if "log.pycker.multiline.enabled" in self.labels:
            return json.loads( self.labels["log.pycker.multiline.enabled"] )
        else:
            return False

    def build_skeleton(self):
        logSkeleton = {}
        self.labels = self.container.labels

        # Identify networks
        logSkeleton["networks"] = [ network for network in self.container.attrs["NetworkSettings"]["Networks"] ]

        # Identify compose services
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
    def parse_log_pattern(self, formattedLog):
        if "log.pycker.pattern" in self.labels:
            try:
                pattern = re.compile( self.labels["log.pycker.pattern"] )
                matches = pattern.search( formattedLog["message"] )
                if matches is not None:
                    for name, value in matches.groupdict().items():
                        formattedLog[name] = value
                        formattedLog["message"] = pattern.sub("", formattedLog["message"])
            except:
                self.logger.exception( "Error using log pattern : %s" % self.labels["log.pycker.pattern"] )

        return formattedLog

    def parse_multiline_log(self, message):
        if not has_date(message) and self.previousLog is not None:
            formattedLog = self.previousLog["entry"]
            formattedLog["message"] += message
            if not ElasticHelper().delete( self.previousLog["id"] ):
                raise
            return formattedLog
        else:
            return self.parse_log(message)

    def parse_log(self, message):
        formattedLog = dict(self.skeleton)
        formattedLog["date"] = parse_date(message)
        formattedLog["message"] = clean_date(message)
        formattedLog = self.parse_log_pattern(formattedLog)

        return formattedLog

    def run(self):
        try:
            self.logs = self.container.logs(stream=True, tail=0)
        except:
            self.logger.error( "Unable to get logs for %s" % self.container.name )
            
        for log in self.logs:
            try:
                es = ElasticHelper()
                message = log.decode("utf-8")
                labels = self.container.labels
                if self.is_multiline_enabled():
                    formattedLog = self.parse_multiline_log( message )
                else:
                    formattedLog = self.parse_log( message )

                # TODO : Save to queue ?
                result = es.register(formattedLog)
                if result is not None and result["result"] == "created":
                    self.previousLog = {
                        "id": result["_id"],
                        "entry": formattedLog
                    }
            except:
                self.logger.exception("Container Exception")
