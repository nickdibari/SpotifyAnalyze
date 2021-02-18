# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/bionic64"

  config.hostmanager.enabled = true
  config.hostmanager.manage_host = true

  config.vm.provider "virtualbox" do |vb|
    vb.customize [ "modifyvm", :id, "--uartmode1", "disconnected" ]  # Disable virtualbox logging
  end

  config.vm.define "app" do |app|
    app.vm.network "private_network", ip: "192.168.20.21"
    app.vm.network "forwarded_port", id: "ssh", host: 3333, guest: 22
    app.vm.hostname = "spotify-analyze.vm"

	app.vm.synced_folder ".", "/srv/app/"

	app.vm.provision "shell", path: "provision.bash"
  end
end
