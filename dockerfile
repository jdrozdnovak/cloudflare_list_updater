# Use an official Python runtime as a parent image
FROM python:3.12-slim-bookworm

# Set the working directory
WORKDIR /usr/src/app

# Install dependencies and cron
RUN apt-get update && apt-get install -y cron && pip install requests

# Copy the current directory contents into the container
COPY . .

# Create the log file to be able to run tail and ensure correct permissions
RUN touch /var/log/cron.log && chmod 0644 /var/log/cron.log

# Dump the environment variables to a file
RUN printenv > /etc/environment

# Set environment variables (can be overridden by Docker Compose)
ENV CLOUDFLARE_API_EMAIL=""
ENV CLOUDFLARE_API_KEY=""
ENV ACCOUNT_ID=""
ENV LIST_ID=""
ENV COMMENT=""
ENV CRON_SCHEDULE="*/5 * * * *"

# Write the cron schedule into the cron.d file and redirect both stdout and stderr to /var/log/cron.log
CMD echo "$CRON_SCHEDULE /usr/local/bin/python /usr/src/app/update_ip.py >> /var/log/cron.log 2>&1" > /etc/cron.d/update_ip_cron && \
    chmod 0644 /etc/cron.d/update_ip_cron && \
    crontab /etc/cron.d/update_ip_cron && \
    cron && tail -f /var/log/cron.log