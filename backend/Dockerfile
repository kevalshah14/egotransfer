# Custom Dockerfile for Railway deployment
# This gives us full control over OpenCV installation
# Updated: 2025-11-17 06:25 - Force rebuild

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV/MediaPipe (Ubuntu 24.04 compatible)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglx0 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgthread-2.0-0 \
    libice6 \
    libx11-6 \
    libfontconfig1 \
    libxcb1 \
    ffmpeg \
    libx264-dev \
    libx264-164 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install pinned NumPy FIRST (required for MediaPipe compatibility)
RUN pip install --no-cache-dir "numpy==1.26.4"

# Install opencv-python-headless to prevent other variants
RUN pip install --no-cache-dir opencv-python-headless==4.8.1.78

# Install all other dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Remove any non-headless OpenCV packages if they snuck in
RUN pip uninstall -y opencv-python opencv-contrib-python opencv-contrib-python-headless 2>/dev/null || true

# Reinstall opencv-python-headless to ensure it's present
RUN pip install --no-cache-dir --force-reinstall opencv-python-headless==4.8.1.78

# Force NumPy back to 1.26.x in case any dependency upgraded it
RUN pip install --no-cache-dir --force-reinstall "numpy==1.26.4"

# Verify only headless OpenCV and correct NumPy are installed
RUN pip list | grep -E "opencv|numpy"

# Copy application code
COPY . .

# Set environment variables for headless operation
ENV OPENCV_VIDEOIO_PRIORITY_MSMF=0
ENV OPENCV_VIDEOIO_DEBUG=0

# Expose port (Railway sets this dynamically)
EXPOSE ${PORT:-8080}

# Run the application
# Use shell form to allow environment variable expansion
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}

