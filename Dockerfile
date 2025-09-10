FROM python:3.12-slim
# Keep Python from writing .pyc files & ensure unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Create and switch to app directory
WORKDIR /app
# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy the rest of the source
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
