# Stage 1: Build Frontend React
FROM node:20-slim AS build-stage
WORKDIR /app

# Copy package files and install dependencies
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install

# Copy source and build
COPY frontend/ ./frontend/
RUN cd frontend && npm run build

# Stage 2: Runtime Python Backend
FROM python:3.11-slim
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model to be baked into the image (Instant Startup on HF Spaces)
ENV HF_HOME=/app/.cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy all project files
COPY . .

# Copy built frontend from Stage 1 to the location FastAPI expects
COPY --from=build-stage /app/frontend/dist ./frontend/dist

# EXPOSE port for HuggingFace / Cloud
EXPOSE 7860

# Run FastAPI using uvicorn
CMD ["uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "7860"]
