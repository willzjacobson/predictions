#!/bin/bash
apt-get install -y python-pip
pip install /var/analytics/an_predictions
pip uninstall -y larkin
pip install /var/analytics/an_predictions