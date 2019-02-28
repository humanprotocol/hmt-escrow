FROM ubuntu:artful

WORKDIR /work
RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y build-essential libffi-dev autoconf libtool \
    python3-dev python3-pip \
    git curl wget bash pandoc pkg-config jq && \
    curl -sL https://deb.nodesource.com/setup_8.x | bash -  && \
    apt-get install -y nodejs && \
    npm install -g yarn && \
    yarn global add truffle

ENV LANG C.UTF-8

COPY package.json /work/
COPY yarn.lock /work/
RUN yarn

# Necessary files for smart contract compilation, migration and testing
COPY contracts /work/contracts/
COPY migrations /work/migrations/
COPY test /work/test/
COPY truffle.js /work/

COPY Pipfile Pipfile.lock /work/
RUN pip3 install pipenv
RUN pipenv install --system --deploy

RUN python3 -m solc.install v0.4.24
ENV SOLC_BINARY="/root/.py-solc/solc-v0.4.24/bin/solc"

# Necessary files for the API to function properly
COPY *.py /work/
COPY hmt_escrow /work/hmt_escrow/
COPY bin /work/bin/

CMD ./test.py
