FROM node:18-alpine

WORKDIR /app

COPY dns-proxy.js entrypoint.sh ./

RUN chmod +x entrypoint.sh

EXPOSE 8053

CMD ["./entrypoint.sh"]
