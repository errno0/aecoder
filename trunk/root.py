#!/usr/bin/env python
#
# Copyright 2008 Limk
#
#
#

import os
import re
import datetime
import urllib
import logging
import struct
import StringIO
import string
from StringIO import StringIO

import wsgiref.handlers
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

import django
from django import http
from django import shortcuts

import appsettings
import models
import utilities
import jobs
#import Coders

def index(request):

  navpaths = []
  navpaths.append( {'name': 'Home', 'url': '' } )

  latestjobs = jobs.GetLatest(10)

  template_values= {
    'jobs' : latestjobs,
    'joblisttype': 'Latest Jobs',
    'navpaths': navpaths,
    'pagenav': '<a href="/job" title="View All Jobs">View All Jobs</a>',
    }

  return utilities.render_to_response(request, 'main.html',template_values )

def login(request):
  
  redirectto = request.REQUEST.get('r', '')
  currentuserid = users.get_current_user()

  if currentuserid:
    query = db.GqlQuery("SELECT * FROM CoderUser WHERE userid = :1", currentuserid)

    coderuser = query.get()
  
  else:
    return http.HttpResponseRedirect('/')
  
  if coderuser:
    coderuser.lastlogin = datetime.datetime.now()
    coderuser.put()
  
    return http.HttpResponseRedirect(redirectto)
  else:
    navpaths = []

    navpaths.append( 
	  { 'name': 'Home',
			'url': "/"}
	)
    navpaths.append(
	  { 'name': 'User',
			'url': '/user' }
	)
    navpaths.append(
	  { 'name': 'Welcome',
			'url': '' }
	)

    coderuser = models.CoderUser(userid=currentuserid, name=currentuserid.nickname())
    coderuser.put()
    template_values = {
      'navpaths': navpaths,
      'redirectto': redirectto,
	}

    return utilities.render_to_response(request, 'welcome.html', template_values)

