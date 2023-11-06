FROM python:3.11

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    parallel \
    gcc \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libffi-dev \
    libglib2.0-dev \
    pandoc

WORKDIR /app

COPY requirements.txt ./

RUN pip install -r requirements.txt

RUN apt-get purge -y --auto-remove gcc

COPY . ./

CMD parallel --ungroup --halt now,fail=1 ::: \
    "celery -A linguoai worker -l info -B" \
    "python manage.py migrate && python manage.py collectstatic && daphne --bind 0.0.0.0 --port $PORT linguoai.asgi:application"
