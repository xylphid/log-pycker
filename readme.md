# Log Pycker

Aggregate your docker logs and format them on the fly if needed

## About

Log Pycker is a docker log aggregator which can be deployed on local machine as well as swarm architecture.

## Supported tags

- `1`, `1-alpine`, `latest`

## Environments

Here are supported environments variable and its definition :
- `elastic.url` : URL of Elastic Search
- `tags.ignore` : Coma separated list of image tags to be ignored

## How to use this image

This image require an Elastic Search to save logs.
You can use the following compose :

```
version: "3.2"

networks:
  logger-net:
  docker-net:
    external: true

services:
  elastic:
    environment:
      discovery.type: single-node
    image: docker.elastic.co/elasticsearch/elasticsearch:6.3.1
    networks:
      - logger-net
    restart: always

  logger:
    build: .
    depends_on:
      - elastic
    environment:
      elastic.url: http://elastic
    links:
      - elastic
    networks:
      - logger-net
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  kibana:
    depends_on:
      - elastic
    environment:
      ELASTICSEARCH_URL: http://elastic:9200
    image: docker.elastic.co/kibana/kibana:6.3.1
    labels:
      traefik.enable: "true"
      traefik.backend: "Monitor"
      traefik.docker.network: "docker-net"
      traefik.frontend.headers.SSLRedirect: "true"
      traefik.frontend.rule: "Host: monitor.docker"
      traefik.port: "5601"
    links:
      - elastic
    networks:
      - docker-net
      - logger-net
```

## Set log pattern

You can define a log pattern for any of your running services. This pattern will be processed on each log entry caught by the daemon.\
To do so, add the `log.pycker.pattern` label with a python regex as followed :
```
docker run -d \
  --name my-awesome-project \
  --label "log.pycker.pattern=(?P<level>(?:[[])?(?:INFO|DEBUG|ERROR)(?:[]])?)\s*"
  nginx
```

Be carefull when using swarm service. You must declare a container label otherwise your pattern won't be spread to any of your tasks.
```
docker service create \
  --name my-awesome-project \
  --container-label "log.pycker.pattern=(?P<level>(?:[[])?(?:INFO|DEBUG|ERROR)(?:[]])?)\s*"
  nginx
```

This pattern will match any log level in INFO, DEBUG and ERROR in brackets or not.
- `INFO` will match and `INFO` will be captured
- `[INFO]` will match and `INFO` will be captured
- `[INFO]    ` will match and `INFO` will be captured

## Persistent data

Persistence is managed on Elastic Search service.
Please refer to its [documentation](https://www.elastic.co/guide/en/elasticsearch/reference/6.3/docker.html)

## Image inheritance

This docker image inherits from [python:3.7-slim](https://hub.docker.com/_/python/) image.
