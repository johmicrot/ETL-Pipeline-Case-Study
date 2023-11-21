# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY inference.py .


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy the config.py file from the parent directory into the /app directory in the container.
COPY ../config.py /app/config.py


# Run your application
CMD ["python", "inference.py"]