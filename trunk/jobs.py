# jobs controller
# Copyright 2008 limk
#

import logging
import datetime

import os
import re
import datetime
import urllib
import logging
import struct
import string
import cgi
import math

import wsgiref.handlers
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.api import images

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.ext.db import djangoforms

import django
from django import http
from django import shortcuts
from django import newforms as forms
from django.contrib.formtools.preview import FormPreview

import appsettings
import utilities
import models

"""
Form class
Investigate how to use preview
"""
class NewJobForm(djangoforms.ModelForm):
  firstname = forms.CharField(label='Firstname*',
    widget = forms.TextInput(attrs = {'size': '30','maxlength': '100'})
    )

  lastname = forms.CharField(label='Lastname*',
    widget = forms.TextInput(attrs = {'size': '30','maxlength': '100'})
    )

  email = forms.EmailField(label='Apply to email*',
    widget = forms.TextInput(attrs = {'size': '30','maxlength': '100'})
    )

  company = forms.CharField(label='Company*',
    widget = forms.TextInput(attrs = {'size': '30','maxlength': '100'})
    )

  url = forms.URLField(label='Website',required=False,
    widget = forms.TextInput(attrs = {'size': '30','maxlength': '100'})
    )

  title = forms.CharField(label='Job Title*',
    widget = forms.TextInput(attrs = {'size': '30','maxlength': '100'})
    )

  description = forms.CharField(label='Description*',
    widget = forms.Textarea(attrs = {'cols': '50', 'rows': '10'})
    )

  class Meta:
    model = models.Jobs
    fields = [ 'firstname', 'lastname', 'email', 'company', 'url', 'title', 'description', 'category']
    #exclude =['userid', 'views', 'logo', 'logotype', 'status', 'location', 'created', 'modified']


def GetLatest(num = 10):
    query = db.GqlQuery("SELECT * FROM Jobs WHERE status='published' ORDER BY created DESC")

    return query.fetch(10)

def index(request):

  page = int(request.GET.get('page',0))

  if not page:
    page=0
    offset=0
  else:
    offset = page * appsettings.MAX_JOB_PER_PAGE

  logging.debug("jobs.index page %d", page)

  query = db.GqlQuery("SELECT * FROM Jobs WHERE status='published' ORDER BY created DESC")
  jobscount = query.count()

  logging.info("jobscount %d\n", jobscount)
  
  num_pages = jobscount / appsettings.MAX_JOB_PER_PAGE
  pagenav=''
  if jobscount % appsettings.MAX_JOB_PER_PAGE:
    num_pages += 1

  if jobscount > 1:
    i = 0
    pagenav='<a href="/job?page=0" title="Page 1">&#171;</a>'
    while i < num_pages:
      pagenav += '&nbsp;<a href="/job?page=' + str(i) + '" title="Page ' + str(i+1) + '">' + str(i+1) + '</a>'
      i += 1

    pagenav += '&nbsp;<a href="/job?page=' + str((num_pages-1)) + '" title="Page ' + str(num_pages) + '">&#187;</a>'

  jobs = query.fetch(int(appsettings.MAX_JOB_PER_PAGE), int(offset))
  

  navpaths = []
    
  navpaths.append(
    { 'name': 'Home',
          'url': "/"}
  )
  navpaths.append(
    { 'name': 'Job',
          'url': '/job' }
  )
  
  navpaths.append(
    { 'name': 'All',
            'url': '' }
  )
  

  template_values = {
    "page_subtitle": "All Jobs",
    "joblisttype": "View All Jobs",
    "navpaths": navpaths,
    "jobs": jobs,
    "pagenav": pagenav,
    }

  return utilities.render_to_response(request, 'viewjoblist.html',template_values )

def edit(request):

  job = None
  jobid = None
  if request.POST:
    jobid = request.POST.get('jobid', '')

  if jobid:
    job = models.Jobs.get(jobid)   
                   
    if job == None:
      return http.HttpRequestForbidden("Permission denied editing this job posting")

    """
    published job requires user/owner to edit
    else it is just a temporary editing posting
    """
    
    if job.status == 'published':
      user = users.get_current_user()

      if user is None or user != job.userid:
        return http.HttpRequestForbidden("Please login to continue editing this job posting")

  #everything's fine or new job posting
  #anonymous posting is allowed, no editing afterwards

  jobform = NewJobForm(data=request.POST or None, instance = job)

  if jobform.is_valid():
    jobform.clean()
    
  navpaths = []

  navpaths.append(
    { 'name': 'Home',
      'url': "/"}
  )
  navpaths.append(
    { 'name': 'Job',
      'url': '/job' }
  )
  navpaths.append(
    { 'name': 'New',
      'url': '' }
  )

  template_values = {
    'application_name': 'AECoder',
    'page_subtitle': 'New Job',
    'navpaths': navpaths,
    'MAX_LOGO_FILE_SIZE' : appsettings.MAX_LOGO_FILE_SIZE,
  }
  template_values.update(
    {'jobform' : jobform,
     'formaction' : request.META['PATH_INFO']},
  )
  if not request.POST:
    return utilities.render_to_response(request, 'editjob.html', template_values)

  errors = jobform.errors
  logoerrors = []
  if not errors:
    try:
      job = jobform.save(commit = False)
      job.firstname = cgi.escape(job.firstname).strip()
      job.lastname = cgi.escape(job.lastname).strip()
      job.title = cgi.escape(job.title)
      job.company = cgi.escape(job.company)
      job.description =cgi.escape(job.description)
      job.email = cgi.escape(job.email).replace("\"", '&quote').strip()
      
      uploadedfile = request.FILES.get('joblogofile', None)
      image_data = None
      
      if uploadedfile:
        #save image post or url upload
        logging.debug("Upload image from user")
        try:
          image_data = db.Blob(uploadedfile.get('content', None))
        except TypeError, err:
          logging.error('Error uploading file %s' % err)
          pass
      
      elif request.POST.get('joblogourl', None):
        #load image
        logourl = request.POST.get('joblogourl')
        logging.debug("Upload image from website %s", logourl)
        try:
          logo_data = urlfetch.Fetch(logourl.encode("utf-8"))
        
          if logo_data.status_code == 200:
            try:
              image_data = db.Blob(logo_data.content)
            except:
              pass
        except urlfetch.DownloadError:
          logoerrors.append( { 'Logo': 'Error downloading image' },)
        except urlfetch.InvalidURLError:
          logoerrors.append( { 'Logo': 'Invalid logo URL' },)
        
      if image_data:
        try:
          imageinfo = utilities.getImageInfo(image_data)
          widthdiff = imageinfo[1] - appsettings.MAX_IMAGE_DIMENSION[0]
          heightdiff = imageinfo[2] - appsettings.MAX_IMAGE_DIMENSION[1]
          
          needresize = False
          if widthdiff > 0 or heightdiff > 0:
            needresize = True
            
            ##bound to image width
            if widthdiff > heightdiff:
              imageratio = float(appsettings.MAX_IMAGE_DIMENSION[0]) / float(imageinfo[1])
              newwidth = appsettings.MAX_IMAGE_DIMENSION[0]
              newheight = imageinfo[2] * imageratio
            else:
              #bound to image height
              imageratio = float(appsettings.MAX_IMAGE_DIMENSION[1]) / float(imageinfo[2])
              newheight= appsettings.MAX_IMAGE_DIMENSION[1]
              newwidth = imageinfo[1] * imageratio
                
          img = images.Image(image_data)
          
          if needresize:
            img.resize(int(newwidth), int(newheight))
          
          img.im_feeling_lucky()
          
          new_image_data = img.execute_transforms(output_encoding = images.PNG)
          
          job.logo = new_image_data
          job.logotype = 'image/png'
        except images.BadRequestError:
          logoerrors.append( {'Logo': 'Request error' }, )
        except images.NotImageError:
          logoerrors.append( {'Logo': 'Not an image data' }, )
        except images.BadImageError:
          logoerrors.append( {'Logo': 'Bad image data' }, )
        except images.LargeImageError:
          logoerrors.append( {'Logo': 'Image too large' }, )
        except images.TransformationError:
          logoerrors.append('Logo', 'Transform error')
        
    except ValueError, err:
      errors['__all__'] = unicode(err)

  if errors or logoerrors:
    template_values.update(
      { 
         'errors': errors,
         'logoerrors': logoerrors,
      }
    )
    return utilities.render_to_response(request, 'editjob.html', template_values)

  ## form is fine, put our value
  cmd = request.POST.get('cmd', 'preview')

  if cmd == "preview":
    job.status = 'edit'
    job.put()

    template_values.update(
      {
      'page_subtitle': 'Job Preview - Please confirm your job posting.',
      'jobid': str(job.key()),
      'jobdescriptiondisplay': display_description(job.description),
      'job':job,
      }
    )
    return utilities.render_to_response(request, 'newjobpreview.html', template_values)
  elif cmd == "confirm":
    job.status = 'published'
    job.put()
    template_values.update(
      {
      'page_subtitle': 'Job Posted - Redirecting to your job posting.',
      'jobid': str(job.key()),
      'job':job,
      }
    )
    return utilities.render_to_response(request, 'newjobconfirm.html', template_values)


def new(request):
  return edit(request)

def viewjob(request, jobid):
  navpaths = []

  navpaths.append(
    { 'name': 'Home',
      'url': "/"}
  )
  navpaths.append(
    { 'name': 'Job',
      'url': '' }
  )
  

  template_values = {
    'application_name': 'AECoder',
    'navpaths': navpaths,
  }
  if jobid:

    logging.debug("viewing job jobid %s", jobid)
    job = models.Jobs.get(jobid)
    
    if job != None and job.status == 'published':
      increase_job_views(jobid, 1)
      
      #related jobs
      relatedjobs = models.Jobs.all().filter("category = ", job.category).filter("status = ", "published").order("-created").fetch(6)
          
      i = 0
      for rj in relatedjobs:
        if rj.key() == job.key():
          del relatedjobs[i]
          break
        i=i+1
            
        
        
      template_values.update(
        {
         'page_subtitle': job.company + ' - ' + job.title,
         'jobdescriptiondisplay': display_description(job.description),
         'job': job,
         'relatedjobs': relatedjobs,
        }
      )
      return utilities.render_to_response(request, 'viewjob.html', template_values)
  else:
    template_values.update(
      {
       'page_subtitle': 'Job not found',
      }
    )
    return http.HttpResponseNotFound('No job found')

def viewjobimage(request, jobid = None):
  if jobid:
    job = models.Jobs.get(jobid)
    
    if job:
      return http.HttpResponse(job.logo, mimetype=job.logotype)
    else:
      return http.HttpResonseNotFount('No job %s found', jobid)
  else:
    return http.HttpResonseNotFount('No job image %s found', jobid)  
def increase_job_views(key, incr = 1):
  job = models.Jobs.get(key)
  job.views += incr
  job.put()
  
  
def display_description(jobdescription):
  transforms = [
    utilities.AutoLink(),
    utilities.NewLine(),
  ]

  jobdescriptiondisplay = jobdescription

  for transform in transforms:
    jobdescriptiondisplay = transform.run(jobdescriptiondisplay)
  
  return jobdescriptiondisplay

def jobbox_js(request):
  jobs = GetLatest(10)
  
  response = http.HttpResponse()
  response.write("""function showjobbox(width) {
      if(width <= 0) width =300;
      document.writeln("<table width=\\\"" + width + "\\\" style=\\\"border: 1px solid #369; background-color: #fff\\\">"
        + "<tr><th colspan=\\\"2\\\" style=\\\"width: " + width + "px; background-color: #9cf; font-family: Arial, Sans-serif; font-size: 12px; font-weight: bold; text-align: center; padding: 5px;\\\">Latest Job - """ + appsettings.APPLICATION_NAME + """</th></tr>");\n""")

  for job in jobs:
    response.write("""
      document.writeln("<tr><td colspan=\\\"2\\\"><a href=\\\"http://""" + request.environ.get('HTTP_HOST', 'coder.appspot.com') + """/job/""" + str(job.key()) +  """\\\">""" + cgi.escape(job.title) + """</a></td></tr><tr><td>&nbsp</td><td>""" + cgi.escape(job.company) +  """</td></tr>");
    """)
  response.write("""
      document.writeln("<tr><td colspan=\\\"2\\\"><hr/></td></tr><tr><td colspan=\\\"2\\\" style=\\\"text-align: center; background-color: #9cf; padding: 5px; font-family: Arial, Sans-serif; font-size: 12px; font-weight: bold; \\\"><a href=\\\"http://""" + request.environ.get('HTTP_HOST', 'coder.appspot.com') + """/job\\\">View all jobs</a>&nbsp; |&nbsp; <a href=\\\"http://""" + request.environ.get('HTTP_HOST', 'coder.appspot.com') + """/job/new\\\">Post a job</a></td></tr>");""")
  response.write("""
      document.writeln("<tr><td colspan=\\\"2\\\" style=\\\"text-align: center;\\\"><a href=\\\"http://""" + request.environ.get('HTTP_HOST', 'coder.appspot.com') + """/getjobbox\\\">Copy job box</a></td></tr>");""")

  response.write("""
      document.writeln("<tr><td colspan=\\\"2\\\"><hr/></td></tr><tr><td colspan=\\\"2\\\" style=\\\"text-align: center;\\\"><em>Powered by <a href=\\\"http://coder.appspot.com\\\">AECoder</a></em></td></tr>");""")
  response.write("""
      document.writeln("</table>");
    }
  """)
  
  
  return response

def getjobbox(request):
  navpaths = []
    
  navpaths.append(
    { 'name': 'Home',
          'url': "/"}
  )
  navpaths.append(
    { 'name': 'Job',
          'url': '/job' }
  )
  
  navpaths.append(
    { 'name': 'Jobbox',
            'url': '' }
  )

  jobs = GetLatest(10)
  
  jobboxsample = """
   <table id="jobboxsample" width="250px" style="width: 250px; border: 1px solid #369; background-color: #fff">
     <tr><th colspan="2" style="width: 250px; background-color: #9cf; font-family: Arial, Sans-serif; font-size: 12px; font-weight: bold; text-align: center; padding: 5px;">Latest Job - """ + appsettings.APPLICATION_NAME + """</th></tr>
     """

  for job in jobs:
    jobboxsample = jobboxsample + """
      <tr><td colspan="2"><a href="http://""" + request.environ.get('HTTP_HOST', 'coder.appspot.com') + """/job/""" + str(job.key()) +  """\\\">""" + cgi.escape(job.title) + """</a></td></tr><tr><td>&nbsp</td><td>""" + cgi.escape(job.company) +  """</td></tr>
      """

  jobboxsample = jobboxsample + """
      <tr><td colspan="2"><hr/></td></tr><tr><td colspan="2" style="text-align: center; background-color: #9cf; padding: 5px; font-family: Arial, Sans-serif; font-size: 12px; font-weight: bold; "><a href="http://""" + request.environ.get('HTTP_HOST', 'coder.appspot.com') + """/job">View all jobs</a>&nbsp; |&nbsp; <a href="http://""" + request.environ.get('HTTP_HOST', 'coder.appspot.com') + """/job/new">Post a job</a></td></tr>
      """
  
  jobboxsample = jobboxsample + """
      <tr><td colspan="2" style="text-align: center;"><a href="http://""" + request.environ.get('HTTP_HOST', 'coder.appspot.com') + """/getjobbox">Copy job box</a></td></tr>
      """

  jobboxsample = jobboxsample + """
      <tr><td colspan="2"><hr/></td></tr><tr><td colspan="2" style="text-align: center;"><em>Powered by <a href="http://coder.appspot.com">AECoder</a></em></td></tr>
      """
  jobboxsample = jobboxsample + """
      </table> 
      """

  template_values = {
    "page_subtitle": "Get Job Box",
    "navpaths": navpaths,
    "jobboxsample": jobboxsample,
  }
  return utilities.render_to_response(request, 'getjobbox.html',template_values )
  
