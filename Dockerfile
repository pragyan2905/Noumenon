# Use an official lightweight Python runtime
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# - ffmpeg: Required for video/audio media conversions
# - libgl1: Sometimes required by image processing libraries
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port that Uvicorn will listen on
EXPOSE 10000

# Start the unified FastAPI server (serves both the API and the React frontend)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "10000"]
