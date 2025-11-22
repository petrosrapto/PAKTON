# Dockerfile for web-app
FROM node:20-slim

WORKDIR /app

# Copy package files
COPY package.json yarn.lock ./
COPY turbo.json ./

# Copy the entire project
COPY . .

# Install dependencies
RUN yarn install --frozen-lockfile

# Set working directory to web app
WORKDIR /app/apps/web

# Expose the web app port
EXPOSE 3000

# Start the web app in development mode (since we have volume mounts)
CMD ["yarn", "dev"]