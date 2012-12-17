# -*- coding: utf-8 -*-

# Find people photos in current directory tree.
#
# Scans current directory and children to find photos
# tagged in Picasa. Then creates 2 separate dirs for
# every person - one with all related photos, and
# another with portraits cut from these photos.

# Needs contacts.xml, PIL library to cut photos,
# relies that face tag info is stored in .picasa.ini
# files.

# Coded by anatoly techtonik <techtonik@gmail.com>
# Licensed to the public domain.

# Thanks to Franz Buchinger <fbuchinger@gmail.com>
# for the description of the file format.


# --- options ---
# NOTE: all paths should be in Unicode

# path to contacts.xml
CONTACTS = u'contacts.xml'
# where to create directory with person photos
OUTPPL = u'__people'
# where to create directory with person portraits
OUTFACE = u'__people_faces'

# -- /options ---


# --- picasa format converters ---

def rect64tofloat(hash):
  coords = []
  for x in range(0, 16, 4):
    chunk = hash[x:x+4]
    coord = float(int(chunk, 16)) / 0xffff
    coords.append(coord)
  return coords

def rect64tocoords(hash, width, height):
  # (left, top, right, bottom) in pixels
  coords = rect64tofloat(hash)
  return [width*coords[0], height*coords[1], width*coords[2], height*coords[3]]

# /-- picasa format ---


import os
from ConfigParser import RawConfigParser
from xml.etree import ElementTree
from collections import defaultdict

class Contact(object):
  def __init__(self, id, name):
    self.name = name
    self.id = id

imgidx = {}     # filename  -> fullpath
# imgface = {}  # fullpath -> faces
faceidx = {}    # contactid -> [(fullpath, rect), ...]

# build index of photos
for root, dirs, files in os.walk('.'):
  #print root
  for f in files:
    if f.upper().endswith('.JPG'):
      if f in imgidx:
        raw_input('Warning, duplicate %s' % f.upper())
      imgidx[f] = root + '/' + f
      continue
    elif not f.endswith('.ini'):
      continue

    name = root + '/' + f
    config = RawConfigParser()
    inifile = config.read(name)
    #print 'ini file:', inifile
    for filesec in config.sections():
      #if file not in imgidx:
      #  print 'File not found in index: %s' % file
      #  raw_input()
      inifname = root + '/' + filesec
      opts = config.options(filesec)
      if 'faces' in opts:
        # rect64(5fdf61b56916754b),3cc9f77ac2da16ec;rect64(991651c4a2e1667d),69185921d98ad8a4
        for facerect in config.get(filesec, 'faces').split(';'):
          rect, contact = facerect.split(',')
          rect = rect.split('(')[1].split(')')[0]
          if contact not in faceidx:
            faceidx[contact] = []
          if filesec not in files:
            #print files
            print 'File (ini) not found in : %s' % inifname
            # raw_input()
          faceidx[contact].append( (inifname, rect) )



import shutil
import Image

def checkdir(name):
  # create dir if it not exists
  if not os.path.exists(name):
    os.mkdir(name)

checkdir(OUTPPL)
checkdir(OUTFACE)

contxml = ElementTree.parse(CONTACTS)
for cx in contxml.getroot():
  name = unicode(cx.get('name'))  #, 'windows-1251')
  id = cx.get('id').encode('utf-8')
  c = Contact(id, name)

  if not id in faceidx:
    print name.encode('utf-8')
  else:
    print name.encode('utf-8'), len(faceidx[id])
    namepath = OUTPPL + u'/' + name
    checkdir(namepath)

    for entry in faceidx[id]:
      fpath, recthash = entry
      if not os.path.exists(fpath):
        continue

      shutil.copy(fpath, namepath)

      namepath2 = OUTFACE + u'/' + name
      checkdir(namepath2)

      ifname, ext = os.path.splitext(fpath)
      im = Image.open(fpath)

      # pixel rect ...
      width, height = im.size
      if len(recthash) < 16:
        print "skipping", recthash, 'for', ifname
        continue
      
      pixelrect = [int(x) for x in rect64tocoords(recthash, width, height)]
      name2 = namepath2 + u'/___' + os.path.basename(ifname) + u'.JPG'
      #print name2
      print pixelrect

      frame = im.crop(pixelrect)
      frame.save(name2, 'JPEG')

#print rect64tocoords('121b23a67b3acbb1', 1024, 768)

