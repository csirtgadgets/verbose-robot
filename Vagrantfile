#e -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"
VAGRANTFILE_LOCAL = 'Vagrantfile.local'

$script = <<SCRIPT
cd /vagrant

DEBIAN_FRONTEND=noninteractive

echo "deb http://http.debian.net/debian/ stretch main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://http.debian.net/debian/ stretch-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://security.debian.org/ stretch/updates main contrib non-free" >> /etc/apt/sources.list

echo "resolvconf resolvconf/linkify-resolvconf boolean false" | debconf-set-selections

# https://hackernoon.com/tips-to-reduce-docker-image-sizes-876095da3b34
apt-get update \
  && apt-get install -y --no-install-recommends python3-dev python-pip3 geoipupdate resolvconf sqlite3 libmagic-dev build-essential

pip3 install pip --upgrade

cp docker/GeoIP.conf /etc/

cp dist/*.tar.gz /tmp/verbose-robot.tar.gz
mkdir /tmp/verbose-robot \
  && cd /tmp \
  && tar -zxvf /tmp/verbose-robot.tar.gz --strip-components=1 -C /tmp/verbose-robot

cd /tmp/verbose-robot

easy_install distribute
pip3 install https://github.com/Supervisor/supervisor/archive/85558b4c86b4d96bd47e267489c208703f110f0f.zip
pip3 install -r requirements.txt
python3 setup.py install

rm -rf /tmp/verbose-robot

useradd cif

cp rules/* /etc/cif/rules/default/
cp docker/tokens.sh /home/cif/
cp helpers/test.sh /home/cif/

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

/usr/local/bin/supervisord -n -c /usr/local/etc/supervisord.conf &
sleep 10

bash /home/cif/test.sh
SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.provision "shell", inline: $script

  config.vm.box = 'ubuntu/xenial64'

  #config.vm.network :forwarded_port, guest: 443, host: 8443

  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--cpus", "2", "--ioapic", "on", "--memory", "2048" ]
  end

  if File.file?(VAGRANTFILE_LOCAL)
    external = File.read VAGRANTFILE_LOCAL
    eval external
  end
end
