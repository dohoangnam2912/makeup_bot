FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install -r requirements.txt

EXPOSE 8000

HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

# Assuming your FastAPI app is in main.py with the FastAPI instance named "app"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]