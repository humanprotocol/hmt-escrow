FROM ubuntu:artful
RUN sed -i 's/archive/us-west-2\.ec2\.archive/' /etc/apt/sources.list
RUN apt-get update -y && apt-get install -y python3-dev python3-pip postgresql-client python-virtualenv git curl wget bash pandoc pkg-config libffi-dev build-essential autoconf libtool jq
RUN pip3 install pipenv
WORKDIR /work

ENV LANG C.UTF-8

COPY Pipfile Pipfile.lock /work/
RUN pipenv install --system --deploy

RUN python3 -m solc.install v0.4.24
ENV SOLC_BINARY="/root/.py-solc/solc-v0.4.24/bin/solc"

COPY contracts /work/
COPY *.py /work/
COPY api /work/api/
COPY basemodels /work/basemodels
COPY bin /work/bin
ENV HET_ETH_SERVER http://localhost:7545
RUN python3 setup.py install


CMD ./test.py
