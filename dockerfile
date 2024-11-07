# Use Python's official lightweight image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the project files into the container
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

# Run the main script
CMD ["python", "main.py"]
