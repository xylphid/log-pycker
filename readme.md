# Log Pycker

Aggregate your docker logs and format them on the fly if needed

## About

Log Pycker is a docker log aggregator which can be deployed on local machine as well as swarm architecture.

## Supported tags

- `1`, `1-python3.7`, `1-slim`, `1.0.0`, `1.0.0-slim`, `1.0.0-slim-python3.7`, `latest`

## Environments

Here are supported environments variable and its definition :
- `elastic.url` : URL of Elastic Search
- `tags.ignore` : Coma separated list of image tags to be ignored

## Availables container labels

* `log.pycker.pattern` : Parse message using the defined pattern. Match groups will be extracted and message cleaned. (ex : `(?P<level>(?:[[])?(?:INFO|DEBUG|ERROR)(?:[]])?)\s*` will extact INFO, DEBUG or ERROR from any message)
* `log.pycker.multiline.enabled` : Detect multiline message using datetime as delimiter

**Caution :** Those are container labels. In swarm, you must use the `--container-label` option to declare them using command line or the `labels` section (not `deploy/labels`) in compose files.

## Persistent data

Persistence is managed on Elastic Search service.
Please refer to its [documentation](https://www.elastic.co/guide/en/elasticsearch/reference/6.3/docker.html)

## How to use this image

This image require an Elastic Search to save logs.
You can use the following compose :

```yml
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
    depends_on:
      - elastic
    environment:
      elastic.url: http://elastic
    image: xylphid/log-pycker:latest
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

Use the image from Docker Hub :
```bash
$ docker-compose up -d
```

Re-build the log-pycker image :
```
docker-compose up --build -d
```

## Reporting bugs and contributing

- Want to report a bug or request a feature ? Please open [an issue](https://github.com/xylphid/log-pycker/issues/new)
- Want to contribute ? Please refer to the [contributing guidelines](contributing.md) to run the project locally and make a pull request.

## Image inheritance

This docker image inherits from [python:3.7-slim](https://hub.docker.com/_/python/) image.