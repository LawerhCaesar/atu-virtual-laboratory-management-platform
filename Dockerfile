FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN DJANGO_DEBUG=true python manage.py collectstatic --noinput --settings=config.build_settings \
    && groupadd --gid 10001 atu \
    && useradd --uid 10001 --gid atu --no-create-home atu \
    && mkdir -p /app/media \
    && chown atu:atu /app/media \
    && chmod 700 /app/media

USER atu

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
