FROM python:3.9-buster

RUN pip install -U pip wheel setuptools

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD . .

CMD python app.py

