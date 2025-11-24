# Description: 
#     Docker image configuration for the PAKTON API service.
#     Sets up a Python environment with system dependencies (Tesseract, Poppler)
#     and installs local PAKTON packages (Archivist, Researcher, Interrogator).
#     
# Author: Raptopoulos Petros [petrosrapto@gmail.com]
# Date  : 2025/03/10

# Use Python base image (will match build platform automatically)
FROM python:3.11.11-slim

WORKDIR /app

# Install system dependencies (Tesseract and Poppler)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libgl1 \
    build-essential \
    zlib1g-dev \
    curl \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# If requirements.txt is in "API/", use the *relative path from the build context*
COPY API/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for the packages
RUN mkdir -p /app/packages/Archivist /app/packages/Researcher /app/packages/Interrogator

# OPTIMIZATION: Copy only requirements.txt files first for better caching
# These rarely change, so Docker can cache this expensive layer
COPY Researcher/requirements.txt /app/packages/Researcher/requirements.txt
COPY Interrogator/requirements.txt /app/packages/Interrogator/requirements.txt
COPY Archivist/requirements.txt /app/packages/Archivist/requirements.txt

# Install dependencies separately (cached unless requirements.txt changes)
# This is the slow part - will be cached if requirements don't change
RUN pip install --no-cache-dir -r /app/packages/Researcher/requirements.txt
RUN pip install --no-cache-dir -r /app/packages/Interrogator/requirements.txt
RUN pip install --no-cache-dir -r /app/packages/Archivist/requirements.txt

# Now copy the actual package code (changes frequently, but installs fast)
COPY Researcher /app/packages/Researcher/
COPY Interrogator /app/packages/Interrogator/
COPY Archivist /app/packages/Archivist/

# Install packages in editable mode (very fast, no dependency reinstall)
RUN pip install --no-deps /app/packages/Researcher/
RUN pip install --no-deps /app/packages/Interrogator/
RUN pip install --no-deps /app/packages/Archivist/

# Copy everything else in API/
COPY API /app/API

# Copy and set up entrypoint script
COPY API/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set the entrypoint to run migrations before starting the app
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (assuming 'api.py' is in API/ and has "app" in it)
CMD ["uvicorn", "API.api:app", "--host", "0.0.0.0", "--port", "5001", "--log-level", "debug"]