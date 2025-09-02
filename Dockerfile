FROM python:3.10-slim

# Install ffmpeg and build tools
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

# Set up working directory
WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

CMD ["python", "app.py"]
