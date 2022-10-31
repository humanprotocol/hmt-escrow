FROM ubuntu:jammy
ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED True

WORKDIR /work

RUN apt-get update -y && \
    apt-get install -y automake bash black build-essential curl git jq libffi-dev libgmp-dev libtool nodejs npm \
	pandoc pkg-config python3-boto python3-dev python3-pip libsnappy-dev node-gyp python-is-python3

ENV PYTHONPATH "$PYTHONPATH:/work:/work/banhammer:/work/hmt-servers"

RUN pip3 install git+https://chromium.googlesource.com/external/gyp
# Downgrading npm version to install old packages gyp
RUN npm install -g npm@6.14.17

COPY package.json /work/
RUN cd /work && npm install
ENV PATH="/work/node_modules/.bin/:${PATH}"

COPY Pipfile Pipfile.lock /work/
RUN pip3 install pipenv mypy types-requests types-setuptools
RUN pipenv install --system --deploy --pre

ENV SOLC_VERSION="v0.6.2"
RUN python3 -m solcx.install ${SOLC_VERSION}
ENV SOLC_BINARY="/root/.py-solc-x/solc-${SOLC_VERSION}/bin/solc"

# Necessary files for smart contract compilation, migration and testing
COPY . /work/
