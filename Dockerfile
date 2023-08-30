FROM python:3.11-slim

# Copies code to /code directory, change working directory
WORKDIR /code
COPY . /code

# # Install python deps, run gunicorn
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

EXPOSE 8000
CMD ["gunicorn", "--access-logfile", "-", "--bind", "0.0.0.0:8080", "app:app"]