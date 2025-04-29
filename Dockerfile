# Use official Python image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app ./app

# Expose port
EXPOSE 4000

# Add a non-root user for security
RUN adduser --disabled-password --no-create-home appuser
USER appuser

# Healthcheck (optional, for production)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl --fail http://localhost:4000/docs || exit 1

# Run the app with gunicorn for production
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:4000"]
