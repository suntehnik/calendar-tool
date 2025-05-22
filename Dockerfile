# Use official Python image
FROM python:3.9-slim

# Set work directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies using setup.py
RUN pip install --upgrade pip \
    && pip install .

# Default entrypoint passes arguments to calendar-tool
ENTRYPOINT ["calendar-tool"]
