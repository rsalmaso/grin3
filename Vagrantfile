# -*- mode: ruby -*-
# vim: set ft=ruby ts=2 sw=2 :

require "fileutils"

VAGRANTFILE_API_VERSION = "2"

$script = <<-SCRIPT
export DEBIAN_FRONTEND=noninteractive
add-apt-repository --no-update --yes ppa:deadsnakes/ppa
add-apt-repository --no-update --yes ppa:git-core/ppa

apt update
apt dist-upgrade -y

# python-software-properties
apt install --yes \
    git \
    python3.5 python3.5-dev python3.5-venv \
    python3.6 python3.6-dev python3.6-venv \
    python3.7 python3.7-dev python3.7-venv \
    python3.8 python3.8-dev python3.8-venv \
    python3-pip

mkdir -p /etc/mercurial
cat >/home/vagrant/.config/hg/hgrc << EOF
[extensions]
evolve =
EOF
python3 -m pip install mercurial
python3 -m pip install hg-evolve
python3 -m pip install tox

# Fix locale to allow saving unicoded filenames
echo 'LANG=en_US.UTF-8' > /etc/default/locale

# Start in project dir by default
echo "\n\ncd /vagrant" >> /home/vagrant/.bashrc
SCRIPT

# ensure log directory exists
$vm_log_dir = File.join(Dir.pwd, ".vagrant", "log")
FileUtils.mkdir_p $vm_log_dir

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/focal64"
  config.vm.provision :shell, inline: $script

  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--memory", 2048]
    vb.customize ["modifyvm", :id, "--uartmode1", "file", File.join($vm_log_dir, "focal.log")]
  end
end
