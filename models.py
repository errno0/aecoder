#!/usr/bin/env python
# copyright 2008 limk
#
from google.appengine.ext import db

import appsettings

"""
Jobs model
holds job id, poster, and other misc information
"""

class Jobs(db.Model):
  userid = db.UserProperty()
  firstname = db.StringProperty(required=True)
  lastname = db.StringProperty(required=True)
  title = db.StringProperty(required = True)
  company = db.StringProperty(required = True)
  email = db.EmailProperty(required = True)
  url = db.LinkProperty(default=None)
  location = db.GeoPtProperty(default = None)
  logo = db.BlobProperty(default=None)
  logotype = db.StringProperty(default=  None)
  description = db.TextProperty(required = True)
  views = db.IntegerProperty(default=0)
  status = db.StringProperty(default='edit', choices=set(['published', 'edit', 'expired']))
  category = db.StringProperty(default='design', choices=set(appsettings.JOB_CATEGORIES))
  created = db.DateTimeProperty(auto_now_add=True)
  modified = db.DateTimeProperty(auto_now=True)

"""
users datastore model
"""
class CoderUser(db.Model):
  userid = db.UserProperty(required=True)
  firstname = db.StringProperty()
  lastname = db.StringProperty()
  email = db.EmailProperty(default=None)
  homepage = db.LinkProperty()
  picture = db.BlobProperty(default=None)
  picturetype = db.StringProperty()
  resume = db.TextProperty()
  location = db.GeoPtProperty() 
  score = db.RatingProperty() #user voted
  lastlogin = db.DateTimeProperty()
  views = db.IntegerProperty(default=0)
  created = db.DateTimeProperty(auto_now_add=True)
  modified = db.DateTimeProperty()

class CoderComment(db.Model):
  coderuser = db.ReferenceProperty(CoderUser)
  comment = db.TextProperty(required=True)
  created = db.DateTimeProperty(auto_now_add=True)

class CoderTag(db.Model):
  coderuser = db.ReferenceProperty(CoderUser, required=True)
  tag = db.CategoryProperty(required=True)

class CoderVote(db.Model):
  coderuser = db.ReferenceProperty(CoderUser)
  vote = db.IntegerProperty(required=True) 
  created = db.DateTimeProperty(auto_now_add=True)
