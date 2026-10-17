FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt requirements-docker.txt ./
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY . .

RUN python manage.py test

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "ms_contable.wsgi:application", "--bind", "0.0.0.0:8000", "--access-logfile", "-"]
