FROM python:3.6-slim-stretch
LABEL developer="Wes Young <wes@csirtgadgets.com>"

ENV DEBIAN_FRONTEND=noninteractive

RUN echo "deb http://http.debian.net/debian/ stretch main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://http.debian.net/debian/ stretch-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://security.debian.org/ stretch/updates main contrib non-free" >> /etc/apt/sources.list

RUN echo "resolvconf resolvconf/linkify-resolvconf boolean false" | debconf-set-selections

# https://hackernoon.com/tips-to-reduce-docker-image-sizes-876095da3b34
RUN apt-get update \
    && apt-get install -y --no-install-recommends geoipupdate resolvconf sqlite3 libmagic-dev build-essential
#RUN apt-get install htop tcpdump curl vim mlocate git
RUN pip3 install pip --upgrade

COPY docker/GeoIP.conf /etc/

COPY dist/*.tar.gz /tmp/verbose-robot.tar.gz
RUN mkdir /tmp/verbose-robot \
    && cd /tmp \
    && tar -zxvf /tmp/verbose-robot.tar.gz --strip-components=1 -C /tmp/verbose-robot

WORKDIR /tmp/verbose-robot

RUN easy_install distribute
RUN pip3 install https://github.com/Supervisor/supervisor/archive/85558b4c86b4d96bd47e267489c208703f110f0f.zip
RUN pip3 install -r requirements.txt
RUN CIF_ENABLE_INSTALL=1 python3 setup.py install

RUN rm -rf /tmp/verbose-robot

RUN useradd cif

VOLUME /etc/cif/rules/default
VOLUME /var/lib/cif
VOLUME /var/lib/fm
VOLUME /var/log/cif
VOLUME /home/cif

COPY rules/* /etc/cif/rules/default/

WORKDIR /home/cif

COPY docker/tokens.sh /home/cif/
COPY docker/stage.sh /home/cif/
COPY helpers/test.sh /home/cif/

EXPOSE 5000
COPY docker/supervisord.conf /usr/local/etc/supervisord.conf
COPY docker/entrypoint /

#RUN apt-get clean && dpkg -r build-essential && rm -rf /root/.cache && rm -rf /var/lib/apt/lists/*

ENTRYPOINT /entrypoint -n