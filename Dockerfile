FROM python:3.10

WORKDIR /app

# Copy daftar library
COPY backend/requirements.txt .

# Install library
RUN pip install --no-cache-dir -r requirements.txt

# Copy semua file project
COPY . .

# Hugging Face Spaces WAJIB jalan di port 7860
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
