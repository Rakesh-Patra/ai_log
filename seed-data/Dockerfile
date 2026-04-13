FROM python:3.9-slim

# add apache bench (ab) tool
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    apache2-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /seed

COPY . .

# create POST data files with ab friendly formats
RUN python make-data.py

# Create a non-root user and group
RUN groupadd -r app && useradd -r -g app app && chown -R app:app /seed
USER app

CMD /seed/generate-votes.sh