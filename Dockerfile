# Stage 1: Builder
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Stage 2: Final image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create directories for static and media files
RUN mkdir -p /app/static /app/media

# Copy and set permissions for wait-for-it.sh
COPY ./scripts/wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Create non-root user
RUN useradd -m django && chown -R django:django /app
USER django

# Expose port (for web service)
EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]