from elasticsearch import Elasticsearch
from datetime import datetime
import logging
import os
import time

logger = logging.getLogger("logpycker")

class Singleton(object):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        else:
            cls._instances[cls].__init__(*args, **kwargs)
        return cls._instances[cls]

    def __new__(class_, *args, **kwargs):
        if class_ not in class_._instances:
            class_._instances[class_] = super(Singleton, class_).__new__(class_, *args, **kwargs)
        else:
            class_._instances[class_].__init__(*args, **kwargs)
        return class_._instances[class_]


class ElasticHelper(Singleton):
    conf = {
        "host": os.getenv("elastic.url", None),
        "name": "pycker-" + datetime.now().strftime("%Y-%m-%d"),
        "type": "docker-log"
    }
    es = None

    def __init__(self):
        self.checkHosts()


    def register(self, message):
        self.waitUntilAlive()
        if self.checkHosts():
            try:
                return self.es.index(index=self.conf["name"], doc_type=self.conf["type"], body=message)
            except:
                logger.exception( "Unable to index the following log :\n%s" % message )
                return None
        else:
            return None

    def delete(self, id):
        self.waitUntilAlive()
        if self.checkHosts():
            try:
                res = self.es.delete(index=self.conf["name"], doc_type=self.conf["type"], id=id)
                return True
            except:
                logger.exception( "Unable to delete the following index : %s" % id )
                return False


    def checkHosts(self):
        if self.conf["host"] is None:
            logger.error("ElasticSearch host is not defined")
            return False
        else:
            return True

    def waitUntilAlive(self):
        if not self.checkHosts():
            return False
        else:
            alive = False
            while not alive:
                try:
                    self.es = Elasticsearch(hosts=self.conf["host"].split(','))
                    alive = self.es.ping()
                    if not alive:
                        raise
                except:
                    logger.info("Could not reach Elastic Searh. Will retry in 5 seconds ...")
                    time.sleep(5)

            return True