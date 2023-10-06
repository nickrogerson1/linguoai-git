FROM python:3.11

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libffi-dev \
    libglib2.0-dev

WORKDIR /app

COPY requirements.txt ./

RUN pip install -r requirements.txt

RUN apt-get purge -y --auto-remove gcc

COPY . ./

CMD celery -A linguoai worker --loglevel=info & python manage.py migrate && python manage.py collectstatic && daphne --bind 0.0.0.0 --port $PORT linguoai.asgi:application