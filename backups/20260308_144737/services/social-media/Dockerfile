FROM python:3.11-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install gRPC for Lightning (optional)
RUN pip install grpcio grpcio-tools lnd-grpc 2>/dev/null || true

# Copy application
COPY src/ /app/src/
COPY frontend/ /app/frontend/

# Expose custom port (configurable)
ENV SERVICE_PORT=10500
EXPOSE 10500

# Run with custom port
CMD ["python", "-m", "src.main"]
