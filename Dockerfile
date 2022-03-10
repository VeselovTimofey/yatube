FROM python:3.9-slim
RUN mkdir /app
COPY requirements.txt /app
RUN pip3 install -r /app/requirements.txt --no-cache-dir
COPY . /app
WORKDIR /app
CMD ["gunicorn", "yatube.wsgi:application", "--bind", "0:8000", "--timeout", "60", "--worker-class", "gevent"]