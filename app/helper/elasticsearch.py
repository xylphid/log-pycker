from elasticsearch import Elasticsearch
from datetime import datetime
import json
import os
import time

class ElasticHelper:
    conf = {
        "host": os.getenv("elastic.url", None),
        "name": "pycker-" + datetime.now().strftime("%Y-%m-%d"),
        "type": "docker-log"
    }
    es = None

    def __init__(self):
        self.checkHosts()


    def register(self, message):
        # print( json.dumps(self.conf) )
        self.waitUntilAlive()
        if self.conf["host"] is not None:
            res = self.es.index(index=self.conf["name"], doc_type=self.conf["type"], body=message)
            # print( "ElasticSearch result : %s" % res )

    def checkHosts(self):
        if self.conf["host"] is None:
            print("%s - ERROR - ElasticSearch host is not defined" % datetime.now())
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
                    print("Could not reach Elastic Searh. Will retry in 5 seconds ...")
                    time.sleep(5)

            return True