# coding=utf-8
import os
import sys

import yaml

__author__ = "David Karapetyan"

# wrapper for loading yaml configuration file as if it were a python dictionary

yaml_dir = sys.prefix
stream = open(os.path.join(yaml_dir, "etc/larkin/user_config.yaml"))
user_config = yaml.load(stream)
stream.close()
