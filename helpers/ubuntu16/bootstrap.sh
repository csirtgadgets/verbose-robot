#!/bin/bash

set -e

DEBIAN_FRONTEND=noninteractive

echo "resolvconf resolvconf/linkify-resolvconf boolean false" | debconf-set-selections

# https://blog.jetbrains.com/pycharm/2017/12/developing-in-a-vm-with-vagrant-and-ansible/
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 8CF63AD3F06FC659
add-apt-repository 'deb http://ppa.launchpad.net/jonathonf/python-3.6/ubuntu xenial main'

apt-get update \
  && apt-get install -y --no-install-recommends python3.6 python3.6-dev python3-pip python-setuptools geoipupdate \
  resolvconf sqlite3 libmagic-dev build-essential python3-setuptools htop tcpdump

ln -sf /usr/bin/python3.6 /usr/local/bin/python3

wget https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py
python3.6 /tmp/get-pip.py

cp /vagrant/docker/GeoIP.conf /etc/

cd /vagrant
easy_install distribute
pip3 install https://github.com/Supervisor/supervisor/archive/85558b4c86b4d96bd47e267489c208703f110f0f.zip
pip3 install -r requirements.txt
python3 setup.py install

useradd cif

mkdir -p /home/cif
mkdir -p /var/lib/cif
mkdir -p /var/log/cif
mkdir -p /var/lib/fm
mkdir -p /etc/cif/rules/default

cp /vagrant/docker/supervisord.conf /usr/local/etc/
cp /vagrant/rules/* /etc/cif/rules/default/
cp /vagrant/docker/tokens.sh /home/cif/
cp /vagrant/helpers/test_vagrant.sh /home/cif/test.sh

geoipupdate -v

chmod 770 /home/cif/tokens.sh
chmod 770 /home/cif/test.sh

/home/cif/tokens.sh

chown -R cif:cif /var/lib/cif
chown -R cif:cif /var/log/cif
chown -R cif:cif /var/lib/fm
chown -R cif:cif /etc/cif
chown -R cif:cif /home/cif

chmod -R 660 /etc/cif/rules
chmod 770 /etc/cif/rules
chmod 770 /etc/cif/rules/default
