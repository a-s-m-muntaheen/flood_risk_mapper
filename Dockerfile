FROM ghcr.io/osgeo/gdal:ubuntu-small-3.8.5

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-dev \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip

WORKDIR /app

# Use a Docker-specific requirements file (Python 3.10 compatible versions)
COPY requirements.docker.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.docker.txt

RUN python3 -c "import django; print('Django OK:', django.__version__)"

COPY . .
EXPOSE 8000
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]