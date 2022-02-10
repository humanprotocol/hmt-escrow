FROM node:16.13-buster

WORKDIR /usr/src/app

COPY package.json yarn.lock ./

RUN yarn

COPY ./public ./public
COPY ./src ./src

RUN yarn build