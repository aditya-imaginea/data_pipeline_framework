FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV STATE_LOG_PATH=/app/state_transitions.jsonl

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e .

# Default command
CMD ["pytest", "tests/"]
