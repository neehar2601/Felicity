# Use the slim version of Python to reduce image size
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy only necessary files first (improves caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose port 5000 for Flask
EXPOSE 5000

# Command to run the application
CMD ["python3", "app.py"]

