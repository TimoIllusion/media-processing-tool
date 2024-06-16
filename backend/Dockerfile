FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory
WORKDIR /app

# Copy the rest of the application code
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Fix for missing libGL.so.1
RUN apt-get update && apt-get install libgl1 libglib2.0-0 -y

# Run the application
CMD ["python", "app.py"]
