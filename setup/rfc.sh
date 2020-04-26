#!/bin/bash

# Print script commands.
set -x
# Exit on errors.
set -e

sudo pip install xml2rfc
sudo apt install -y golang-go
git submodule init
git submodule update

PWD=`pwd`

sed -i '/GOPATH/d' ~/.bash_profile
echo "export GOPATH=${PWD}/mmark" >> ~/.bash_profile
mkdir -p mmark/bin
sed -i '/GOBIN/d' ~/.bash_profile
echo "export GOBIN=${PWD}/mmark/bin" >> ~/.bash_profile

source ~/.bash_profile

cd mmark
go get
go build

