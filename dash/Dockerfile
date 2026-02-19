FROM node:20-alpine

# Install ADB and required tools
RUN apk add --no-cache android-tools docker-cli curl

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --omit=dev

# Copy source
COPY . .

# Create data directory
RUN mkdir -p data

EXPOSE 3000

CMD ["node", "src/index.js"]
