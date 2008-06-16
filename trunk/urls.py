# Copyright 2008 limk <aecoder@gmail.com>
# Original Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.conf.urls.defaults import *

urlpatterns = patterns('',
  (r'^[/]?$', 'root.index'),
  (r'^login[/]?$', 'root.login'),
  (r'^job[/]?$', 'jobs.index'),
  (r'^job/new[/]?$', 'jobs.new'),
  (r'^job/edit/([0-9a-zA-Z]+)[/]?$', 'jobs.edit'),
  (r'^job/([0-9a-zA-Z]+)[/]?$', 'jobs.viewjob'),
  (r'^jobimage/([0-9a-zA-Z]+)[/]?$', 'jobs.viewjobimage'),
  (r'^jobbox.js$', 'jobs.jobbox_js'),
  (r'^getjobbox[/]?$', 'jobs.getjobbox'),
  # Uncomment this for admin:
# (r'^admin/', include('django.contrib.admin.urls')),
)

"""
  apps_binding.append(('/user/edit', Coders.UserEdit))
  apps_binding.append(('/user(\/)?', Coders.UserList))
  apps_binding.append(('/user/(.*)', Coders.UserView))
  apps_binding.append(('/userimage/(.*)', Coders.GetUserImage))
"""
