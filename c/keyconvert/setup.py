"""
   This file can be used to build keyconvert as a python extension

   use "python ./setup.py build"
"""

from distutils.core import setup, Extension

module1 = Extension('keyconvert',
                    libraries = ['ssl'], 
                    sources = ['keyconvert.c', 'keyconvertext.c'])

setup (name = 'keyconvert',
              version = '1.0',
              description = 'key converter',
              ext_modules = [module1])
