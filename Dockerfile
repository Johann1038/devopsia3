# ════════════════════════════════════════════════════════════
# Stage 1 — Builder: install Python deps into a virtual env
# ════════════════════════════════════════════════════════════
FROM python:3.12-slim AS builder

WORKDIR /build

# Copy only the requirements first to leverage Docker layer cache
COPY backend/requirements.txt .

# Create a virtual environment and install dependencies
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip --no-cache-dir && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ════════════════════════════════════════════════════════════
# Stage 2 — Runtime: lean final image (~130 MB vs ~900 MB)
# ════════════════════════════════════════════════════════════
FROM python:3.12-slim AS runtime

# Security: run as non-root user
RUN groupadd --gid 1001 appgroup && \
    useradd  --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application source code
COPY backend/  ./backend/
COPY frontend/ ./frontend/

# Make the venv python the default for this image
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1   \
    PYTHONUNBUFFERED=1          \
    FLASK_ENV=production        \
    PORT=5000

# Drop to non-root
USER appuser

EXPOSE 5000

# Healthcheck — matches the /health route in app.py
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Use gunicorn for production; chdir into backend/ so app.py is found as app:app
CMD ["gunicorn", "--chdir", "backend", "--workers", "2", "--bind", "0.0.0.0:5000", "--timeout", "60", "app:app"]
