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
        alive = False
        if self.conf["host"] is None:
            print("%s - ERROR - ElasticSearch host is not defined" % datetime.now())
        else:
            while not alive:
                try:
                    self.es = Elasticsearch(hosts=self.conf["host"].split(','))
                    alive = True
                except:
                    print("Could not reach Elastic Searh. Will retry in 5 seconds ...")
                    time.sleep(5)


    def register(self, message):
        # print( json.dumps(self.conf) )
        if self.conf["host"] is not None:
            res = self.es.index(index=self.conf["name"], doc_type=self.conf["type"], body=message)
            # print( "ElasticSearch result : %s" % res )