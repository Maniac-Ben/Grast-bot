FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app
COPY . .

# Bake the screp binary into the image at build time
RUN python screp_setup.py

# Worker process: connects out to Discord, no port needed
CMD ["python", "-u", "bot.py"]

#End
