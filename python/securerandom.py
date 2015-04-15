#! /usr/bin/env python
import random
import struct

class SecureRandom(random.Random):
  def __init__(self, paranoid=False):
    self._file = None
    self._paranoid = paranoid
    self.seed(None)
  def seed(self, junk):
    if self._file:
      try:
        self._file.close()
      except:
        pass
    if self._paranoid:
      fname = '/dev/random'
    else:
      fname = '/dev/urandom'
    self._file = open(fname, 'r')
  def getstate(self):
    return None
  def setstate(self, junk):
    pass
  def jumpahead(self, junk):
    pass
  def random(self):
    #struct.calcsize('i') should be 4 on both 32-bit and 64-bit architectures
    assert(struct.calcsize('i') == 4)
    return abs(struct.unpack('i', self._file.read(4))[0])/(0.+(~(-2147483648)))
