# Multi-stage build for optimized FastAPI Docker image
FROM python:3.12-slim as builder

# Set working directory for API (not /app which is React Native!)
WORKDIR /backend

# Install system dependencies required for compilation
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Final stage - smaller image
FROM python:3.12-slim

# Set working directory for API (not /app which is React Native!)
WORKDIR /backend

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Make startup script executable
RUN chmod +x /backend/start.sh

# Set Python path to ensure modules are found
ENV PYTHONPATH=/backend

# Expose port (Railway will set PORT env variable)
EXPOSE 8000

# Note: Railway handles healthchecks via railway.toml, no need for Dockerfile HEALTHCHECK

# Use startup script to properly handle PORT variable
CMD ["/backend/start.sh"]
