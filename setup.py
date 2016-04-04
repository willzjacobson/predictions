# coding=utf-8
import sys

from pip.download import PipSession
from pip.req import parse_requirements
from setuptools import setup, find_packages

if not sys.version_info.major == 2 and sys.version_info.minor == 7:
    sys.exit("Sorry, Python 3 is not supported")

# parse requirements
install_reqs = parse_requirements("requirements.txt",
                                  session=PipSession())
# reqs is a list of requirements
reqs = [str(ir.req) for ir in install_reqs]
pkgs = find_packages(exclude=["*.tests"])
# magic function for including subpackages in repo
# can list packages with subpackages explicitly later
setup(
    name='larkin',
    version='0.53',
    packages=pkgs,
    data_files=[('./etc/larkin', ['larkin/user_config.yaml'])],
    url='https://github.com/PrescriptiveData/datascience',
    license='Proprietary',
    author='PrescriptiveData',
    author_email='dkarapetyan@prescriptivedata.io',
    description=(
        'An analytics and prediction engine'
        'for energy and electricity usage in'
        'commercial and non-commercial buildings.'
    ),
        scripts=['larkin/bin/run_analytics'],
    install_requires=reqs
)
