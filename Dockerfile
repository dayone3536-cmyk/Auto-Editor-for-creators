FROM python:3.11-slim

# Install system dependencies (FFmpeg)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Start the Flask app using Gunicorn with threads enabled
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--threads", "4", "app:app"]
