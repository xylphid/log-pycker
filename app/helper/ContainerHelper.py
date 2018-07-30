import DockerHelper
import ElasticHelper

class ContainerHelper(DockerHelper):

    def __init__(self, container, client=docker.from_env()):
        DockerHelper.__init__(self, client)
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
                formattedLog["date"] = self.parse_date(log.decode("utf-8"))
                formattedLog["message"] = self.clean_date(log.decode("utf-8")).strip()

                # TODO : Save to queue
                es = ElasticHelper()
                es.register(formattedLog)
                # with lock:
                #     print( json.dumps( formattedLog, ensure_ascii=False, indent=4 ) )
            except:
                print("Exception caught")
                traceback.print_exc()
                print("=============================================")


    def stop(self):
        self.logs.close()