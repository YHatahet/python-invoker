# Use a slim python image to keep it small
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY server.py .

# SECURITY: Create a non-root user 'lambda_user'
# If the executed code tries to modify system files, it will fail.
RUN useradd -m lambda_user
USER lambda_user

# Expose the Flask port
EXPOSE 5000

# Run the server
CMD ["python", "server.py"]
