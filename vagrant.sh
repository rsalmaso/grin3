#!/bin/sh

export DEBIAN_FRONTEND=noninteractive
add-apt-repository --no-update --yes ppa:deadsnakes/ppa
add-apt-repository --no-update --yes ppa:git-core/ppa

apt update
apt dist-upgrade -y

# python-software-properties
apt install --yes \
    git \
    python2.7 python2.7-dev \
    python3.4 python3.4-dev \
    python3.5 python3.5-dev \
    python3.6 python3.6-dev \
    python3.7 python3.7-dev \
    python3.8 python3.8-dev python3.8-distutils \
    python-pip python3-pip

python2.7 -m pip install mercurial
python2.7 -m pip install hg-evolve
python3.6 -m pip install tox

# Fix locale to allow saving unicoded filenames
echo 'LANG=en_US.UTF-8' > /etc/default/locale

# Configure mercurial
mkdir -p /home/vagrant/.config/hg
cat >/home/vagrant/.config/hg/hgrc << EOF
[extensions]
evolve =
EOF

# Start in project dir by default
echo "\n\ncd /vagrant" >> /home/vagrant/.bashrc
