FROM python:3.7-slim

ENV	VERSION 	1.0.0

LABEL maintainer.name="Anthony PERIQUET"
LABEL maintainer.email="anthony@periquet.net"
LABEL version=${VERSION}
LABEL description="Log Pycker"

# RUN apk add --no-cache py3-openssl

ADD app /opt/log-pycker
RUN pip install --upgrade pip && \
	pip install -r /opt/log-pycker/requirements

ENTRYPOINT [ "python", "/opt/log-pycker/app.py" ]