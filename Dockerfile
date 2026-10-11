FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libcairo2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN DJANGO_SECRET_KEY=build-only-not-for-runtime python manage.py test

RUN DJANGO_SECRET_KEY=build-only-not-for-runtime python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "ms_contable.wsgi:application", "--bind", "0.0.0.0:8000", "--access-logfile", "-"]
