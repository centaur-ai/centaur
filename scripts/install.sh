#!/bin/bash

sudo mv ../centaur.service /etc/systemd/system/centaur.service
sudo systemctl enable centaur
sudo systemctl start centaur
