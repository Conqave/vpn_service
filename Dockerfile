# Use an official Python 3.14 runtime as a parent image
FROM python:3.14-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 1080 available to the world outside this container
EXPOSE 1080

# Define environment variable
ENV NAME VPN

# Run vpn_tun.py when the container launches
CMD ["python", "vpn_tun.py"]
