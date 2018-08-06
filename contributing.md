# Contributing

Use the following  instructions and guidelines to contribute to the log-pycker project.

## Requirements

Ensure you have [Docker](https://docs.docker.com/engine/installation/) and [python](https://www.python.org/) >=3.7 installed.\
If you intend to run the program from you local machine, you may need those software running too :
- [Elastic Search](https://www.elastic.co/guide/en/elasticsearch/reference/current/_installation.html)
- [Kibana](https://www.elastic.co/guide/en/kibana/current/setup.html)

## Running the project
### Run the project from your machine

Checkout the project and go in the root directory :
```bash
$ git clone https://github.com/xylphid/log-pycker.git
$ cd log-pycker
```

Install dependencies :
```bash
$ pip3 install --user -r requirements
```

Start watching you container logs :
```bash
$ python3 app/app.py
```

### Run the project from docker

Customize the `docker-compose.yml` file and execute the following command :
```bash
$ docker-compose up --build
```

## Contribute

Just submit your pull-request ;-)