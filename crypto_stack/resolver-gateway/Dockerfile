FROM node:18-alpine

WORKDIR /app

RUN apk add --no-cache python3 make g++

COPY package.json package-lock.json* ./
RUN npm install --production

COPY index.js ./

EXPOSE 8080

CMD ["node", "index.js"]
