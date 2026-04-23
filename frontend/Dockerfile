FROM node:20-alpine

WORKDIR /app

COPY package.json /app/package.json
COPY package-lock.json* /app/

RUN npm install

COPY . /app

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "-p", "3000"]

