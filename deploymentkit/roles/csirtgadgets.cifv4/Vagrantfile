#e -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"
VAGRANTFILE_LOCAL = 'Vagrantfile.local'

$script = <<SCRIPT
set -e
echo 'installing the basics'
apt-get update && apt-get install -y python-minimal python-pip

echo 'installing ansible...'
pip install 'ansible>=2.4,<2.5'

echo 'running ansible...'
cd /vagrant

ansible-playbook --syntax-check test.yml
ansible-playbook -i "localhost," -c local test.yml -vv

echo 'giving cif-* a chance to boot up...'
sleep 15
curl localhost:5000

SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.provision "shell", inline: $script
  config.vm.box = 'ubuntu/xenial64'

  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--cpus", "2", "--ioapic", "on", "--memory", "1024" ]
  end

  if File.file?(VAGRANTFILE_LOCAL)
    external = File.read VAGRANTFILE_LOCAL
    eval external
  end
end
