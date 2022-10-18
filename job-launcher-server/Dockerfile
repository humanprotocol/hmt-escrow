FROM node:14-alpine

RUN apk add g++ make py3-pip


WORKDIR /app

COPY ./package.json ./package-lock.json /app/

RUN npm install

COPY . /app/

EXPOSE 3000
CMD ["npm", "run", "build"]
