FROM python:3.14-slim

# Set work directory
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose the port
EXPOSE 4000

# Set environment variables (optional, can be overridden in docker-compose)
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "run.py"]
