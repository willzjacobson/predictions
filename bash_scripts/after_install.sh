#!/bin/bash

# if anaconda not yet installed, install it
if [ ! -d "$/var/analytics/anaconda2"]; then
	bash /var/analytics/Anaconda2-4.0.0-Linux-x86_64.sh -b -p /var/analytics/anaconda2
fi

apt-get install -y python-pip
pip install /var/analytics/an_predictions
pip uninstall -y larkin
pip install /var/analytics/an_predictions