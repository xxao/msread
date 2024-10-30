#  Created by Martin Strohalm

from setuptools import setup, find_packages

# include additional files
package_data = {}

# set classifiers
classifiers = [
    'Development Status :: 4 - Beta',
    'Programming Language :: Python :: 3 :: Only',
    'Operating System :: OS Independent',
    'License :: OSI Approved :: MIT License',
    'Topic :: Scientific/Engineering',
    'Intended Audience :: Science/Research']

# main setup
setup(
    name = 'msread',
    version = "0.6.0",
    description = 'Mass spectrometry data reading library',
    url = 'https://github.com/xxao/msread',
    author = 'Martin Strohalm',
    author_email = 'msread@bymartin.cz',
    license = 'MIT',
    packages = find_packages(),
    package_data = package_data,
    classifiers = classifiers,
    install_requires = ['numpy'],
    zip_safe = False)
