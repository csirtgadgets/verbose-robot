#e -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"
VAGRANTFILE_LOCAL = 'Vagrantfile.local'

RUN_TESTS=ENV.fetch('TESTS', '')

$script = <<SCRIPT
cd /vagrant

RUN_TESTS="#{RUN_TESTS}"

CIF_TOKEN=`head -n 25000 /dev/urandom | openssl dgst -sha256 | awk -F ' ' '{print $2}'`
if [ "${CIF_TOKEN}" == "" ]; then
  export CIF_TOKEN=`head -n 25000 /dev/urandom | openssl dgst -sha256`
fi

export CIF_TOKEN=${CIF_TOKEN}
echo "#!/bin/sh" > /etc/profile.d/cif.sh
echo "export CIF_TOKEN=${CIF_TOKEN}" >> /etc/profile.d/cif.sh

bash helpers/easybutton.sh

CIF_ROUTER_CONFIG_PATH=/home/cif/router.yml /usr/local/bin/supervisord -c /usr/local/etc/supervisord.conf
sleep 10

echo "token: ${CIF_TOKEN}" > /home/cif/cif.yml
chown cif:cif /home/cif/cif.yml
chmod 660 /home/cif/cif.yml

if [ "${RUN_TESTS}" == "" ]; then
    echo 'skipping tests..'
else
    bash /home/cif/test.sh
fi
SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.provision "shell", inline: $script

  config.vm.box = 'ubuntu/xenial64'

  config.vm.network :forwarded_port, guest: 5000, host: 5000

  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--cpus", "2", "--ioapic", "on", "--memory", "2048" ]
  end

  if File.file?(VAGRANTFILE_LOCAL)
    external = File.read VAGRANTFILE_LOCAL
    eval external
  end
end
