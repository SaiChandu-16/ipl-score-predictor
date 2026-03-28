FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source — everything lands directly in /app
COPY backend/ .

# /app is the working dir, so Python can find main.py and app/ package
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# ✅ Fixed: was "backend.main:app" — no "backend." prefix needed
#    because WORKDIR is already /app (inside the backend folder)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]