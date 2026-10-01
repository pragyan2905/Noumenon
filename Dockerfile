# Stage 1: Build the React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
# Copy only package.json first for cache efficiency
COPY frontend/package*.json ./
RUN npm install
# Copy the rest of the frontend code and build
COPY frontend/ .
RUN npm run build

# Stage 2: Setup the Python backend
FROM python:3.13-slim
WORKDIR /app

# Install system dependencies (ffmpeg, libgl1, and image libraries for Pillow)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libwebp-dev \
    libfreetype6-dev \
    libtiff5-dev \
    libopenjp2-7-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend source code
COPY . .

# Copy the compiled static frontend from Stage 1 into the final image
# This ensures FastAPI can find it when looking at frontend/dist
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expose the port Uvicorn will listen on
EXPOSE 10000

# Start the unified FastAPI server
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "10000"]
