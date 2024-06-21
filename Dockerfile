# Use an official Python 3.11 runtime as a parent image
FROM python:3.11-slim

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Clone the repository and copy its contents into the working directory
RUN git clone https://github.com/Conqave/vpn_service.git /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 1080 available to the world outside this container
EXPOSE 1080

# Define environment variable
ENV NAME VPN

# Run vpn_tun.py when the container launches
CMD ["python", "vpn_tun.py"]
