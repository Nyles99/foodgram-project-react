FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt --no-cache-dir
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0:8000" ]