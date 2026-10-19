# Use an official lightweight Python runtime
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable live output logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside the container
WORKDIR /app

# Install dependencies first (leverages Docker caching)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Expose the default Django port
EXPOSE 8000

# Start the development server bound to all network interfaces
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]