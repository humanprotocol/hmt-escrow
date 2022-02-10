FROM node:16.13-alpine3.14

WORKDIR /usr/src/app

COPY package.json yarn.lock ./

RUN yarn

COPY contracts ./contracts
COPY index.js .
COPY s3.js .
