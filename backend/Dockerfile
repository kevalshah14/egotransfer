# Custom Dockerfile for Railway deployment
# This gives us full control over OpenCV installation

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
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install opencv-python-headless FIRST to prevent other variants
RUN pip install --no-cache-dir opencv-python-headless==4.8.1.78

# Install all other dependencies
# Use --no-deps for packages that might try to install opencv variants
RUN pip install --no-cache-dir -r requirements.txt

# Remove any non-headless OpenCV packages if they snuck in
RUN pip uninstall -y opencv-python opencv-contrib-python opencv-contrib-python-headless 2>/dev/null || true

# Reinstall opencv-python-headless to ensure it's present
RUN pip install --no-cache-dir --force-reinstall opencv-python-headless==4.8.1.78

# Verify only headless version is installed
RUN pip list | grep opencv

# Copy application code
COPY . .

# Set environment variables for headless operation
ENV OPENCV_VIDEOIO_PRIORITY_MSMF=0
ENV OPENCV_VIDEOIO_DEBUG=0

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

