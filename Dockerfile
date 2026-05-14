FROM python:3.11-slim

WORKDIR /app

# System dependencies for psycopg2 + playwright
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy app code
COPY . .

EXPOSE 8000

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
