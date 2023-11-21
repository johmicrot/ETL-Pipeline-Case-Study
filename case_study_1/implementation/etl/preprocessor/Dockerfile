FROM python:3.9-slim
WORKDIR /app
COPY preprocessor.py .

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy the config.py file from the parent directory into the /app directory in the container.
COPY ../config.py /app/config.py


CMD ["python", "preprocessor.py"]