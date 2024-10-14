# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the dependencies using requirements.txt
RUN pip install -r requirements.txt

# Command to run your Python script when the container starts
CMD ["python", "dns_export.py"]
