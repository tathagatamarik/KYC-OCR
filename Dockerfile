# Use a lightweight Python image from the official Docker repository
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory (where the Dockerfile resides) into the container's working directory
COPY . /app
# Copy .env file if present
COPY .env.example /app/.env.example

# Install the system dependencies needed for the FastAPI app
RUN apt-get update && apt-get install -y \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install Redis
RUN apt-get update && apt-get install -y redis-server libmagic1

# Expose the port FastAPI will run on
EXPOSE 8000

# Create a startup script
RUN echo '#!/bin/bash\nservice redis-server start\ncelery -A celery_app worker --loglevel=info &\npython app.py' > /app/start.sh
RUN chmod +x /app/start.sh

# Command to run the startup script
CMD ["/app/start.sh"]
