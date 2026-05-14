FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System libraries needed for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv==0.11.12

# Copy dependency files from project root
COPY pyproject.toml uv.lock requirements.txt ./

# Install dependencies using pip as fallback due to uv lock format issues
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]