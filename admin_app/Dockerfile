# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Set work directory to project root
WORKDIR /app

# Install dependencies
# Copy only requirements first to leverage Docker cache
COPY admin_app/requirements.txt ./admin_app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r ./admin_app/requirements.txt

# Copy the entire project
COPY . .

# Expose port (same as in docker-compose.yml and .env)
# The default is 8000, matching uvicorn default
EXPOSE ${ADMIN_APP_PORT:-8000}

# Run the application from project root, referencing the package
CMD ["uvicorn", "admin_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 