FROM python:3.13-slim-bullseye

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLOWER_UNAUTHENTICATED_API=true

# Install system dependencies for PostgreSQL, LDAP, and general builds
RUN apt-get update && \
    apt-get install -y \
        libpq-dev \
        libglib2.0-0 \
        libpango1.0-0 \
        gcc \
        postgresql-client \
        python3-dev \
        musl-dev \
        libsasl2-dev \
        libldap2-dev \
        libssl-dev \
        vim \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn

# Copy project files
COPY . .

# Expose port 8000
EXPOSE 8000

# Run Django server with Gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
