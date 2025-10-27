# Dockerfile - production build for a small Flask app
FROM python:3.13-slim

# Install system deps required by some packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user
ENV APP_HOME=/app
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

# Copy and install dependencies first (cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Use PORT env var (Cloud Run sets PORT to 8080 by default)
ENV PORT=8080

# Expose port (informational)
EXPOSE 8080

# Use gunicorn for production; 2 workers is enough for small apps
CMD ["gunicorn", "app:app", "-w", "2", "--bind", "0.0.0.0:8080", "--timeout", "30"]
