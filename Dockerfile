# Base image with Python and Chrome
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    chromium-driver \
    chromium

# Set display to avoid errors with headless Chrome
ENV DISPLAY=:99

# Create app directory
WORKDIR /app
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit app
CMD ["streamlit", "run", "trial.py", "--server.port=8501", "--server.enableCORS=false"]
