FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY telegram-bot/requirements.txt ./telegram-bot/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r telegram-bot/requirements.txt

# Copy telegram bot code
COPY telegram-bot/ ./telegram-bot/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the bot
CMD ["python", "telegram-bot/main.py"]
