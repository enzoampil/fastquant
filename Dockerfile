# Set base image (host OS)
FROM python:3.7

# Set the working directory in the container
WORKDIR /fastquant

# Copy the dependencies file to the working directory
COPY python/requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy the content of the python directory to the working directory
COPY python/ .
