FROM ubuntu:focal
ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED True

WORKDIR /work

RUN apt-get update -y && \
    apt-get install -y automake bash black build-essential curl git jq libffi-dev libgmp-dev libtool mypy nodejs npm \
	pandoc pkg-config python3-boto python3-dev python3-pip libsnappy-dev

ENV PYTHONPATH "/usr/lib/python3.8/:/usr/local/lib/python3.8/dist-packages/:/work:/work/banhammer:/work/hmt-servers"

COPY package.json package-lock.json /work/
RUN cd /work && npm install
ENV PATH="/work/node_modules/.bin/:${PATH}"

RUN pip3 install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

ENV SOLC_VERSION="v0.6.2"
RUN python3 -m solcx.install ${SOLC_VERSION}
ENV SOLC_BINARY="/root/.py-solc-x/solc-${SOLC_VERSION}/bin/solc"

# Necessary files for smart contract compilation, migration and testing
COPY . /work/
