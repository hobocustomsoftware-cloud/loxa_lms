# syntax=docker/dockerfile:1.6
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies, then install runtime dependencies, and finally clean up
# 🛑 FIX: Change Debian mirror to a more reliable one to solve network issues
# and combine all apt commands into a single layer. Use a different mirror if connectivity is an issue.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    # Clean up to reduce image size
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


WORKDIR /app

# If you use requirements.txt
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Or if you use pyproject.toml (Poetry), copy & install instead.
# COPY pyproject.toml poetry.lock* ./
# RUN pip install --no-cache-dir poetry && poetry config virtualenvs.create false \
#     && poetry install --no-interaction --no-ansi

# Copy project
COPY . .

CMD ["gunicorn", "loxa.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
