# Dockerfile for Duka DAO Node.js app
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (use install --omit=dev to avoid needing lockfile; generates one if missing)
RUN npm install --omit=dev && npm cache clean --force

# Copy app source
COPY . .

# Expose port
EXPOSE 3000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000', (res) => { if (res.statusCode !== 200) throw new Error(); })"

# Start app
CMD ["npm", "start"]
