#!/bin/sh
#Import the MongoDB GPG Key#
curl -fsSL https://pgp.mongodb.com/server-8.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor

#Add the MongoDB Repository
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/8.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list

#Reload local package database
sudo apt-get update

#install MongoDB
sudo apt-get install -y mongodb-org


#Fix Directory permissions(if required)
sudo chown -R mongodb:mongodb /var/log/mongodb
sudo chown -R mongodb:mongodb /var/lib/mongodb

#start and enable the service
sudo systemctl daemon-reload
sudo systemctl start mongod
sudo systemctl enable mongod

#verify the installation
sudo systemctl status mongod

#connect to the database shell using mongosh or the mongo client
#mongosh
