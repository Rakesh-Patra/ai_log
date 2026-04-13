FROM node:18-slim

# add curl for healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl tini && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/local/app

# have nodemon available for local dev use (file watching)
RUN npm install -g nodemon

COPY package*.json ./

# Minor optimization: ensure node_modules are handled correctly
RUN npm ci && \
    npm cache clean --force && \
    mv /usr/local/app/node_modules /node_modules

# Create a non-root user and group
RUN groupadd -r app && useradd -r -g app app

COPY . .

# Set ownership to the non-root user
RUN chown -R app:app /usr/local/app

# Switch to the non-root user
USER app

ENV PORT 80
EXPOSE 80

CMD ["node", "server.js"]
