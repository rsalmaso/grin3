# -*- mode: ruby -*-
# vim: set ft=ruby ts=2 sw=2 :

require "fileutils"

# ensure log directory exists
$vm_log_dir = File.join(Dir.pwd, ".vagrant", "log")
FileUtils.mkdir_p $vm_log_dir

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/bionic64"  # 18.04
  config.vm.provision :shell, :path => "vagrant.sh"

  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--memory", 2048]
    vb.customize ["modifyvm", :id, "--uartmode1", "file", File.join($vm_log_dir, "bionic.log")]
  end
end
