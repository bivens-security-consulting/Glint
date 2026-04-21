# Use official Playwright Python image which includes system deps and browsers
FROM mcr.microsoft.com/playwright/python:v1.44.0-focal

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (already in base image, but ensure they are ready)
RUN playwright install chromium

# Copy application code
COPY . .

# Expose port 8000
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GLINT_DOCKER=1

# Run the dashboard by default
CMD ["python", "glint.py", "dash", "--host", "0.0.0.0", "--port", "8000"]
