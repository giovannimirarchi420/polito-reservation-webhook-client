# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
# Copy the entire 'app' directory into '/app/app' inside the container
COPY ./app /app/app

# Expose the default port the container *might* run on. K8s will manage the actual port.
EXPOSE 8080

# Run the application using the python script as a module
CMD ["python", "-m", "app.main"]