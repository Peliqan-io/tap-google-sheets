#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='tap-google-sheets',
      version='2.0.0',
      description='Singer.io tap for extracting data from the Google Sheets v4 API',
      author='jeff.huth@bytecode.io',
      classifiers=['Programming Language :: Python :: 3 :: Only'],
      py_modules=['tap_google_sheets'],
      install_requires=[
          'backoff==1.8.0',
          'requests==2.22.0',
          'singer-python @ git+https://github.com/peliqan-io/singer-python@master'
      ],
      extras_require={
          'test': [
              'pylint',
              'nose'
          ],
          'dev': [
              'ipdb',
          ]
      },
      entry_points='''
          [console_scripts]
          tap-google-sheets=tap_google_sheets:main
      ''',
      packages=find_packages(),
      package_data={
          'tap_google_sheets': [
              'schemas/*.json'
          ]
      })
