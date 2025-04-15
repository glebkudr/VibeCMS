# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Set work directory to project root
WORKDIR /app

# -------- Frontend Build Stage --------
# Install Node.js (choose a specific LTS version)
RUN apt-get update && \
    apt-get install -y curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy frontend package file (NOT package-lock.json)
COPY admin_app/frontend/package.json ./admin_app/frontend/

# Explicitly install the optional dependency for the Linux x64 platform
# Use --no-save to avoid adding it to package.json
RUN npm install --prefix ./admin_app/frontend @rollup/rollup-linux-x64-gnu --no-save

# Use --prefix to install in the correct subfolder
# Clean cache and install dependencies based only on package.json
RUN npm cache clean --force && \
    npm install --prefix ./admin_app/frontend --no-package-lock

# Copy the rest of the frontend source code
COPY admin_app/frontend/ ./admin_app/frontend/

# Build frontend assets
# Use --prefix to run the build script in the correct subfolder
RUN npm run build --prefix ./admin_app/frontend
# --------------------------------------

# -------- Python Application Stage --------
# Install Python dependencies
# Copy only requirements first to leverage Docker cache
COPY admin_app/requirements.txt ./admin_app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r ./admin_app/requirements.txt

# Copy the entire project AFTER frontend build and AFTER Python deps
# This ensures backend changes don't invalidate frontend build cache unnecessarily
COPY . .

# Expose port (same as in docker-compose.yml and .env)
# The default is 8000, matching uvicorn default
# Use ARG for port to allow override during build if needed, though ENV is usually sufficient
ARG ADMIN_APP_PORT=8000
EXPOSE ${ADMIN_APP_PORT}

# Set the default command to run the application
# Remove --reload for production images
CMD ["uvicorn", "admin_app.main:app", "--host", "0.0.0.0", "--port", "8000"] 