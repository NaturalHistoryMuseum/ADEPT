
from setuptools import find_packages, setup

setup(
    name="adept",
    version="0.1",
    description='ADEPT',
    url='http://github.com/benscott/adept',
    author='Ben Scott',
    author_email='ben@benscott.co.uk',    
    packages=["adept"],
    entry_points={
        'console_scripts': [
            'adept = adept.cli:cli',
        ],
    },


)
