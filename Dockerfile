FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- cache-bust marker: bump this string to force a clean rebuild ---
# build: 2026-06-27-v2
COPY . .

# Bake the screp binary into the image at build time
RUN python screp_setup.py

# Worker process: connects out to Discord, no port needed
CMD ["python", "-u", "bot.py"]
