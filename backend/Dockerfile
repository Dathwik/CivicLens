FROM python:3.11-slim

# System deps for GeoDjango (GDAL, GEOS, PostGIS client)
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    binutils \
    libproj-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/local.txt

COPY . .

ENV DJANGO_SETTINGS_MODULE=config.settings.local
ENV PYTHONUNBUFFERED=1
