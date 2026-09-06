FROM python:3.10-slim

WORKDIR /app

# Install system utilities for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies manifest and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service source files
COPY . .

# Expose backend API and frontend UI ports
EXPOSE 8000 8501

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
