FROM ubuntu:16.04
LABEL developer="Wes Young <wes@csirtgadgets.com>"

ENV DEBIAN_FRONTEND=noninteractive

EXPOSE 5000

COPY docker/entrypoint /
COPY docker/GeoIP.conf /etc/
COPY docker/supervisord.conf /usr/local/etc/supervisord.conf
RUN echo "resolvconf resolvconf/linkify-resolvconf boolean false" | debconf-set-selections

RUN apt-get update
RUN apt-get install -y geoipupdate python3-dev python3-pip python-setuptools python-pip build-essential git sudo \
    resolvconf curl vim mlocate
RUN pip3 install pip --upgrade

RUN geoipupdate -v

RUN rm -rf /tmp/verbose-robot
COPY dist/*.tar.gz /tmp/verbose-robot.tar.gz
RUN mkdir /tmp/verbose-robot
RUN cd /tmp && tar -zxvf /tmp/verbose-robot.tar.gz --strip-components=1 -C /tmp/verbose-robot
#COPY * -R /tmp/verbose-robot
#RUN cd /tmp && git clone https://github.com/csirtgadgets/verbose-robot

WORKDIR /tmp/verbose-robot

RUN easy_install distribute
# latest master
RUN pip3 install https://github.com/Supervisor/supervisor/archive/85558b4c86b4d96bd47e267489c208703f110f0f.zip
RUN pip3 install -r requirements.txt
RUN python3 setup.py install

#RUN dpkg-remove build-essential sudo
RUN rm -rf /tmp/verbose-robot

RUN useradd cif

VOLUME /etc/cif/rules/default
VOLUME /var/lib/cif
VOLUME /var/lib/fm
VOLUME /var/log/cif

COPY rules/* /etc/cif/rules/default/

WORKDIR /home/cif

ENTRYPOINT ["/entrypoint", "-n"]