#!/bin/bash

export "PATH=/var/analytics/anaconda2/bin:$PATH"
pip install /var/analytics/an_predictions
pip uninstall -y larkin
pip install /var/analytics/an_predictions