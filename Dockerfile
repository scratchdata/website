FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "app:app", "--access-logfile", "-", "--bind", "0.0.0.0:8000"]
