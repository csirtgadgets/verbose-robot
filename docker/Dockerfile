FROM python:3.6-slim-stretch
LABEL developer="Wes Young <wes@csirtgadgets.com>"

ENV DEBIAN_FRONTEND=noninteractive

RUN echo "deb http://http.debian.net/debian/ stretch main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://http.debian.net/debian/ stretch-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://security.debian.org/ stretch/updates main contrib non-free" >> /etc/apt/sources.list

RUN echo "resolvconf resolvconf/linkify-resolvconf boolean false" | debconf-set-selections

# https://hackernoon.com/tips-to-reduce-docker-image-sizes-876095da3b34
RUN apt-get update \
    && apt-get install -y --no-install-recommends geoipupdate resolvconf sqlite3 libmagic-dev build-essential procps \
    cron bind9

RUN echo 'cif             soft    nofile            90000' >> /etc/security/limits.conf
RUN echo 'cif             hard    nofile            100000' >> /etc/security/limits.conf

RUN useradd cif

COPY docker/cron_restart.sh /etc/cron.weekly/cif_restart.sh
COPY docker/cron_geoip.sh /etc/cron.monthly/geoip_update.sh
COPY dev_requirements.txt /tmp/
COPY requirements.txt /tmp/

COPY docker/supervisord.conf /usr/local/etc/supervisord.conf
COPY docker/entrypoint /

COPY rules/* /etc/cif/rules/default/

RUN easy_install distribute
RUN pip3 install -r /tmp/dev_requirements.txt

RUN pip3 install https://github.com/Supervisor/supervisor/archive/85558b4c86b4d96bd47e267489c208703f110f0f.zip
RUN pip3 install csirtgsdk==1.1.5

COPY dist/*.tar.gz /tmp/verbose-robot.tar.gz
RUN mkdir /tmp/verbose-robot \
    && cd /tmp \
    && tar -zxvf /tmp/verbose-robot.tar.gz --strip-components=1 -C /tmp/verbose-robot

WORKDIR /tmp/verbose-robot

RUN DISABLE_PREDICT_IPV4=1 python3 setup.py test
RUN CIF_ENABLE_INSTALL=1 python3 setup.py install

RUN rm -rf /tmp/verbose-robot

RUN pip3 install 'elasticsearch-dsl>=6.3,<7.0'
RUN pip3 install https://github.com/csirtgadgets/verbose-robot-elasticsearch/archive/4.0.tar.gz

VOLUME /etc/cif/rules/default
VOLUME /var/lib/cif
VOLUME /var/lib/fm
VOLUME /var/log/cif
VOLUME /home/cif

WORKDIR /home/cif

EXPOSE 5000

RUN apt-get clean && dpkg -r build-essential && rm -rf /root/.cache && rm -rf /var/lib/apt/lists/*

ENTRYPOINT /entrypoint -n
