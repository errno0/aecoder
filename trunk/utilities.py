#!/usr/bin/env python
# copyright @2008 limk <aecoder@gmail.com
#

import re
import struct
from StringIO import StringIO

from google.appengine.api import users
from google.appengine.ext import db


from django import http
from django import shortcuts

import appsettings
import models

def render_to_response(request, template, template_values = {}):
  currentuserid = users.get_current_user()
  currentuserkey = ''
  currentuserfriendlyname = ''
  
  if currentuserid:
    query = db.GqlQuery("SELECT * FROM CoderUser WHERE userid = :1", currentuserid)
    
    coderuser = query.get()
    
    if coderuser:
      currentuserkey = str(coderuser.key())
      if coderuser.firstname:
        currentuserfriendlyname = coderuser.firstname
        
      if coderuser.lastname:
        currentuserfriendlyname += ' ' + coderuser.lastname
    
      if not currentuserfriendlyname:
        p = re.compile('\@([a-zA-Z0-9\.])*$')
        currentuserfriendlyname = p.sub('', str(coderuser.userid))
        
  template_values.update(
    {
      'user' : currentuserid,
      'currentuserkey': currentuserkey,
      'currentuserfriendlyname': currentuserfriendlyname,
      'request': request,
      'login_url': users.CreateLoginURL('/login?r=' + request.environ.get('PATH_INFO','')),
      'logout_url': users.CreateLogoutURL('http://' + request.environ.get('HTTP_HOST') + '/'),
      'application_name': appsettings.APPLICATION_NAME,
      'googleanalytics': appsettings.GOOGLE_ANALYTICS,
    }
  )
  return shortcuts.render_to_response(template, template_values)

## from pyib
def getImageInfo(data):
  data = str(data)
  size = len(data)
  height = -1
  width = -1
  content_type = ''

    # handle GIFs
  if (size >= 10) and data[:6] in ('GIF87a', 'GIF89a'):
    # Check to see if content_type is correct
    content_type = 'image/gif'
    w, h = struct.unpack("<HH", data[6:10])
    width = int(w)
    height = int(h)

  # See PNG 2. Edition spec (http://www.w3.org/TR/PNG/)
  # Bytes 0-7 are below, 4-byte chunk length, then 'IHDR'
  # and finally the 4-byte width, height
  elif ((size >= 24) and data.startswith('\211PNG\r\n\032\n')
      and (data[12:16] == 'IHDR')):
    content_type = 'image/png'
    w, h = struct.unpack(">LL", data[16:24])
    width = int(w)
    height = int(h)

  # Maybe this is for an older PNG version.
  elif (size >= 16) and data.startswith('\211PNG\r\n\032\n'):
    # Check to see if we have the right content type
    content_type = 'image/png'
    w, h = struct.unpack(">LL", data[8:16])
    width = int(w)
    height = int(h)

  # handle JPEGs
  elif (size >= 2) and data.startswith('\377\330'):
    content_type = 'image/jpeg'
    jpeg = StringIO(data)
    jpeg.read(2)
    b = jpeg.read(1)
    try:
      while (b and ord(b) != 0xDA):
        while (ord(b) != 0xFF): b = jpeg.read
        while (ord(b) == 0xFF): b = jpeg.read(1)
        if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
          jpeg.read(3)
          h, w = struct.unpack(">HH", jpeg.read(4))
          break
        else:
          jpeg.read(int(struct.unpack(">H", jpeg.read(2))[0])-2)
        b = jpeg.read(1)
      width = int(w)
      height = int(h)
    except struct.error:
      pass
    except ValueError:
      pass

  return content_type, width, height
  

## from cccwiki
class Transform(object):
  """Abstraction for a regular expression transform.

  Transform subclasses have two properties:
     regexp: the regular expression defining what will be replaced
     replace(MatchObject): returns a string replacement for a regexp match

  We iterate over all matches for that regular expression, calling replace()
  on the match to determine what text should replace the matched text.

  The Transform class is more expressive than regular expression replacement
  because the replace() method can execute arbitrary code to, e.g., look
  up a WikiWord to see if the page exists before determining if the WikiWord
  should be a link.
  """
  def run(self, content):
    """Runs this transform over the given content.

    We return a new string that is the result of this transform.
    """
    parts = []
    offset = 0
    for match in self.regexp.finditer(content):
      parts.append(content[offset:match.start(0)])
      parts.append(self.replace(match))
      offset = match.end(0)
    parts.append(content[offset:])
    return ''.join(parts)


class AutoLink(Transform):
  """A transform that auto-links URLs."""
  def __init__(self):
    self.regexp = re.compile(r'([^"])\b((http|https)://[^ \t\n\r<>\(\)&"]+' \
                             r'[^ \t\n\r<>\(\)&"\.])')

  def replace(self, match):
    url = match.group(2)
    return match.group(1) + '<a href="%s">%s</a>' % (url, url)

class NewLine(Transform):
  """A transform that convert new line to <br/>"""
  def __init__(self):
    self.regexp = re.compile(r'\n')
      
  def replace(self, match):
    return '<br/>'

