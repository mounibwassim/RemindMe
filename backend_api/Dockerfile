# Multi-stage build for production-grade FastAPI backend
FROM python:3.11-slim as builder

WORKDIR /app

# Install system compilation dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies in builder stage
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final production stage
FROM python:3.11-slim as runner

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy backend api application source
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV PORT=8000

# Expose server port
EXPOSE 8000

# Start server using uvicorn binding to globally-routed interface
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
