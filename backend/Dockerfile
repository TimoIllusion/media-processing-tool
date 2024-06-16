# Use the official Python image
FROM python:3.8-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Fix for missing libGL.so.1
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install libgl1 libglib2.0-0 -y

# Run the application
CMD ["python", "app.py"]
