FROM python:3.6-slim

RUN apt-get update && \
    apt-get -y install build-essential && \
    pip3 install uwsgi && \
    apt-get purge -y build-essential && \
    apt -y autoremove

WORKDIR /app
ADD . /app

RUN pip3 install -r requirements.txt

CMD ["uwsgi", "app.ini"]
