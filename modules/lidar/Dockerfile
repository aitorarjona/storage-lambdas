FROM python:3.9-buster

RUN apt update \
    && apt upgrade -y \
    && apt install --no-install-recommends -y \
    glibc-source \
    gcc \
    git

RUN git clone https://github.com/LAStools/LAStools.git \
    && cd LAStools \
    && make \
    && cp bin/las2las bin/lasindex bin/lasinfo bin/laszip /usr/local/bin/ \
    && cd .. \
    && rm -rf LAStools

WORKDIR lastools

RUN pip install -U pip wheel setuptools

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt && rm requirements.txt

ADD app.py lidar.py ./
COPY pys3proxy pys3proxy

CMD python app.py

