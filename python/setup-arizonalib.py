#!/usr/bin/env python

from distutils.core import setup, Extension

setup(name='arizonalib',
      version='1.0',
      description='Univeristy of Arizona Libraries for Stork',
      author='University of Arizona Department of Computer Science',
      author_email='stork@cs.arizona.edu',
      url='http://www.cs.arizona.edu/stork/',
#      packages=['transfer'],
      py_modules = ['arizonacomm',
                    'arizonaconfig',
                    'arizonacrypt',
                    'arizonacurl',
                    'arizonaerror',
                    'arizonageneral',
                    'arizonagroup',
                    'arizonareport',
                    'arizonatemplate',
                    'arizonatransfer',
                    'arizonaunittest',
                    'arizonawarning',
                    'arizonaxml',
                    'planetlabAPI',
                    'planetlabCall',
                    'download_indicator',
                    'securerandom',
                    'transfer.arizonatransfer_bittorrent',
                    'transfer.arizonatransfer_coblitz',
                    'transfer.arizonatransfer_coral',
                    'transfer.arizonatransfer_ftp',
                    'transfer.arizonatransfer_http',
                    'transfer.arizonatransfer_https',
                    'transfer.arizonatransfer_nest',
                    'transfer.arizonatransfer_s3',
                    'storkbtdownloadheadless'

#                    'storktransaction',
#                    'storkpackage',
#                    'package.storkrpm',
#                    'package.storktar'
                    ],
     )

