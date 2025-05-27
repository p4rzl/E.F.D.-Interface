# Use a base image of python:3.9-slim
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the application code into the Docker image
COPY . /app

# Install the necessary dependencies using pip
RUN pip install --no-cache-dir -r requirements.txt

# Set the entry point to run the application using python index.py
ENTRYPOINT ["python", "index.py"]
