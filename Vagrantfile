#e -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"
VAGRANTFILE_LOCAL = 'Vagrantfile.local'

sdist=ENV['CIF_ANSIBLE_SDIST']
hunter_threads=ENV['CIF_HUNTER_THREADS']
hunter_advanced=ENV['CIF_HUNTER_ADVANCED']
csirtg_token=ENV['CSIRTG_TOKEN']
cif_token=ENV['CIF_TOKEN']

RUN_TESTS=ENV.fetch('TESTS', '')

$script = <<SCRIPT
export CIF_ANSIBLE_SDIST=#{sdist}
export CIF_HUNTER_THREADS=#{hunter_threads}
export CIF_HUNTER_ADVANCED=#{hunter_advanced}
export CIF_BOOTSTRAP_TEST=1
export CSIRTG_TOKEN=#{csirtg_token}
export CIF_TOKEN=#{cif_token}

cd /vagrant/deploymentkit

bash easybutton.sh
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
