import os
import logging
import random
import time
import urllib
import wsgiref.handlers
import zipfile
import re

from cStringIO import StringIO
from datetime import datetime
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.ext import webapp
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import images

import ec
import servertest

class MainHandler(webapp.RequestHandler):
  def get(self):
    
    results = db.GqlQuery("Select * FROM Enterprise")
    templateValues = {
      'enterprises' : results
    }

    path = os.path.join(os.path.dirname(__file__), 'html/index.html')
    self.response.out.write(unicode(template.render(path, templateValues)))

class About(webapp.RequestHandler):
  def get(self):
    templateValues = {}
    path = os.path.join(os.path.dirname(__file__), 'html/about.html')
    self.response.out.write(unicode(template.render(path, templateValues)))

class Media(webapp.RequestHandler):
  def get(self):
    templateValues = {}
    path = os.path.join(os.path.dirname(__file__), 'html/media.html')
    self.response.out.write(unicode(template.render(path, templateValues)))

class Help(webapp.RequestHandler):
  def get(self):
    templateValues = {}
    path = os.path.join(os.path.dirname(__file__), 'html/iPhone-help.html')
    self.response.out.write(unicode(template.render(path, templateValues)))

class Tutorial(webapp.RequestHandler):
  def get(self):
    templateValues = {}
    path = os.path.join(os.path.dirname(__file__), 'html/tutorial.html')
    self.response.out.write(unicode(template.render(path, templateValues)))

class Template(webapp.RequestHandler):
  def get(self):
    templateValues = {}
    path = os.path.join(os.path.dirname(__file__), 'html/template.html')
    self.response.out.write(unicode(template.render(path, templateValues)))



class CreateProject(webapp.RequestHandler):
  def post(self):
    error = ''
    projectName = self.request.get("projectName")
    protect = self.request.get("protect") == "true"
    if projectName == None or len(projectName.strip()) < 4: #just show the form, don't process anything
      self.response.out.write("Error: Project names must be at least 4 characters long.")
      return

    if projectName.find(" ") >= 0 or projectName.find("\t") >= 0 or projectName.find("\n") >= 0 or projectName.find(",") >= 0 or projectName.find("&") >= 0 or projectName.find(".") >= 0 or projectName.find("-") >= 0:
      self.response.out.write("Error: Spaces, tabs, commas, hyphens, dots and/or ampersands are not allowed in project names.")
      return

    try:
      asciiString = str(projectName)
    except UnicodeEncodeError:
      self.response.out.write("Error: Project names must consist only of ASCII characters; accented or other special characters are not (yet) allowed.")
      return

    results = db.GqlQuery("SELECT * FROM Project WHERE name = :1 ", projectName).fetch(1)
    if len(results) > 0:
      self.response.out.write("Error: The name " + projectName + " is already in use by another project.") 
      return

    try:
      logging.info("Creating project named " + projectName)
      newProject = ec.Project(name = projectName, description = "", imagePath = "", protected = protect)
      newProject.put()
      self.response.out.write("Success")
    except db.BadValueError, reason:
      self.response.out.write("Error: Bad value error - " + str(reason))
    except Exception, reason:
      self.response.out.write("Error: Unexpected exception - " + str(reason))
    
class EditProject(webapp.RequestHandler):
  def post(self):
    projectKey = self.request.get("projectKey")
    projectName = self.request.get("projectName")
   
    if projectKey != None and len(projectKey.strip()) > 0: #just show the form, don't process anything
      project = db.get(projectKey)
      projectName = project.name
      logging.info("updating project " + project.name)

    elif projectName != None and len(projectName.strip()) > 0: #just show the form, don't process anything
      results = db.GqlQuery("SELECT * FROM Project WHERE name = :1 ", projectName).fetch(1)
      if len(results) > 0:
        project = results[0]  
    
    if project is None:
      templateValues = { "error" : "Could not find project with key " + str(projectKey) + " and/or name " + str(projectName) }
      self.response.out.write(unicode(templateValues))
      return
        
    project.description = self.request.get("projectDescription")
      #project.image = db.Blob(self.request.get("projectImg"))
    logging.info(self.request.get("removeImg"))
    if self.request.get("removeImg") != "":
      project.removeImage()
    if self.request.get("projectImg") != "":
      img_tmp = images.Image(self.request.get("projectImg"))
      logging.info("image width = " + str(img_tmp.width) + " image height = " + str(img_tmp.height))
      if (img_tmp.width > 300) | (img_tmp.height > 200):
        logging.info("resizing image")
        img_tmp = images.resize(self.request.get("projectImg"), 300, 200)
      else :
        logging.info("not resizing image")
        img_tmp = self.request.get("projectImg")
      project.saveImage('image', db.Blob(img_tmp))
    
    project.put()
    self.redirect("/project.html?key=" + str(project.key()))
    return

class ProjectImage(webapp.RequestHandler):
  def get(self):
    logging.info("Getting Project Image") 
    projectKey = self.request.get("projectKey")
    projectName = self.request.get("projectName")
    
    if projectKey != None and len(projectKey.strip()) > 0: #just show the form, don't process anything
      project = db.get(projectKey)
      projectName = project.name
      logging.info("updating project " + project.name)

    elif projectName != None and len(projectName.strip()) > 0: #just show the form, don't process anything
      results = db.GqlQuery("SELECT * FROM Project WHERE name = :1 ", projectName).fetch(1)
      if len(results) > 0:
        project = results[0]
    
    image = project.getImage()
    
    if image is not None:
      self.response.headers['Content-Type'] = 'image/gif'
      self.response.out.write(str(image))
      
class ProjectMenu(webapp.RequestHandler):
  def get(self):
    projectKey = self.request.get("key")
    projectName = self.request.get("name") 
    templateValues = {}
    project = None
    
    if projectKey != None and len(projectKey.strip()) > 0: 
      project = db.get(projectKey)
      projectName = project.name

    elif projectName != None and len(projectName.strip()) > 0: #just show the form, don't process anything
      results = db.GqlQuery("SELECT * FROM Project WHERE name = :1 ", projectName).fetch(1)
      if len(results) > 0:
        project = results[0]
	
	

    if project is None:
      templateValues = { "error" : "Could not find project with key " + str(projectKey) + " and/or name " + str(projectName) + ", <a href=\"http://www.epicollect.net/create1.html\">Create a new project?</a>" }
    else:
      form = project.getLatestForm() 
      templateValues["projectName"] = project.name
      if users.get_current_user() is None:
        templateValues["loginLink"] = " | <a href=\"" + users.create_login_url(self.request.uri) + "\" >Login</a>"
      else :
        templateValues["loginLink"] = " | <a href=\"" + users.create_logout_url(self.request.uri) + "\" >Logout</a>"
      if project.protected and form.user != users.get_current_user():
        templateValues = { "error" : "You do not have permission to view this project " + ("<a href=\"" + users.create_login_url('/project.html?name=' + projectName) + "\">Login</a>" if users.get_current_user() is None else ""), "projectName" : str(project.name), "projectKey" : "", "description" : "", "hasImage" : ""}
      else :
        
        
        if project.image is not None:
          templateValues["projectImage"] = "<img src= \"/projectImage?projectKey=" + str(project.key()) + "\" />"
        if form is not None:
          templateValues["projectDescription"] = project.description
          templateValues["getFormLink"] = "<a href=\"/getForm?projectKey=" + str(project.key()) + "\" >View form definition</a>" 
          templateValues["userMenu"] = "<tr><td colspan=\"2\" bgcolor=\"#CCCCCC\"><strong>View Data</strong></td></tr><tr><td width=\"50%\" align=\"center\"><a href=\"/listEntries?projectKey=" + str(project.key()) + "\"><img src=\"http://www.epicollect.net/website/images/projecthome/form_view.png\" alt=\"form\" width=\"98\" height=\"70\"></a></td><td width=\"50%\" align=\"center\"><a href=\"/showMap?projectKey=" + str(project.key()) + "\"><img src=\"http://www.epicollect.net/website/images/projecthome/map.png\" alt=\"map\" width=\"98\" height=\"70\"></a></td></tr><tr><td width=\"50%\" align=\"center\"><a id=\"listEntries\" href=\"/listEntries?projectKey=" + str(project.key()) + "\">Browse Project Data</a></td><td width=\"50%\" align=\"center\"><a id=\"showMap\" href=\"/showMap?projectKey=" + str(project.key()) + "\">Show Map </tr>"
        else:
          templateValues["projectDescription"] = "<p>The url of this project's homepage is <a href=\"http://www.epicollect.net/project.html?name=" + project.name + "\">http://www.epicollect.net/project.html?name=" + project.name + "</a><p>Congratulations, you have now created your project wesbite. Before submitting data you must create a Form - to do this click the 'create/Edit Project Form Icon below. For instructions please click the link at the top left of this page.</p><p>You can also add some explanatory text and upload an image which will appear here by clicking the Update Project description and picture icon.</p>"
        if form is None or form.user == users.get_current_user() :
          templateValues["adminMenu"] = "<tr><td colspan=\"2\" bgcolor=\"#CCCCCC\"><strong>Project Administration</strong></td></tr><tr><td width=\"50%\" align=\"center\"><a href=\"/createOrEditForm.html?projectKey=" + str(project.key()) + "\"><img src=\"http://www.epicollect.net/website/images/projecthome/form_small.png\" alt=\"form\" width=\"98\" height=\"70\"></a></td><td width=\"50%\" align=\"center\"><a href=\"/ProjectDescription.html?projectKey=" + str(project.key()) + "\"><img src=\"http://www.epicollect.net/website/images/projecthome/homepage_update.png\" alt=\"map\" width=\"98\" height=\"70\"></a></td></tr><tr><td width=\"50%\" align=\"center\"><a id=\"listEntries\" href=\"/createOrEditForm.html?projectKey=" + str(project.key()) + "\">Create or Edit Project Form</a></td><td width=\"50%\" align=\"center\"><a id=\"updateProject\" href=\"/ProjectDescription.html?projectKey=" + str(project.key()) + "\">Update Homepage description and picture</tr>"   
    
	
	
    path = os.path.join(os.path.dirname(__file__), 'html/project.html')
    content = template.render(path, templateValues)
   
    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write(unicode(content))

class ProjectDescription(webapp.RequestHandler):
  def get(self):
    projectKey = self.request.get("projectKey")
    projectName = self.request.get("projectName") 
    templateValues = {}
    project = None
    
    if projectKey != None and len(projectKey.strip()) > 0: #just show the form, don't process anything
      project = db.get(projectKey)
      projectName = project.name

    elif projectName != None and len(projectName.strip()) > 0: #just show the form, don't process anything
      results = db.GqlQuery("SELECT * FROM Project WHERE name = :1 ", projectName).fetch(1)
      if len(results) > 0:
        project = results[0]

    if project is None:
      templateValues = { "error" : "Could not find project with key " + str(projectKey) + " and/or name " + str(projectName) }
      return
    
    form = project.getLatestForm() 
    templateValues["projectName"] = project.name
    
    if project.protected and form.user != users.get_current_user():
      templateValues = { "error" : "You do not have permission to view this project " + ("<a href=\"" + users.create_login_url('/project.html?name=' + projectName) + "\">Login</a>" if users.get_current_user() is None else ""), "projectName" : str(project.name), "projectKey" : "", "description" : "", "hasImage" : ""}
    else :
      templateValues["projectDescription"] = project.description
      templateValues["getFormLink"] = "<a href=\"/getForm?projectKey=" + str(project.key()) + "\" >View form definition</a>" 
      if project.image is not None:
        templateValues["projectImage"] = "<img style=\"float: right;\" src= \"/projectImage?projectKey=" + str(project.key()) + "\" />"
       
    path = os.path.join(os.path.dirname(__file__), 'html/ProjectDescription.html')
    self.response.out.write(unicode(template.render(path, templateValues)))

class ProjectHome(webapp.RequestHandler):
  def post(self):
    projectKey = self.request.get("projectKey")
    projectName = self.request.get("projectName") 
    templateValues = {}
    project = None

    if projectKey != None and len(projectKey.strip()) > 0: #just show the form, don't process anything
      project = db.get(projectKey)
      projectName = project.name

    elif projectName != None and len(projectName.strip()) > 0: #just show the form, don't process anything
      results = db.GqlQuery("SELECT * FROM Project WHERE name = :1 ", projectName).fetch(1)
      if len(results) > 0:
        project = results[0]

    if project is None:
      templateValues = { "error" : "Could not find project with key " + str(projectKey) + " and/or name " + str(projectName) }
      self.response.out.write(unicode(templateValues))
      return
    form = project.getLatestForm()
    if not project.protected or form is None or (project.protected and form.user == users.get_current_user()) :
      templateValues = { "error" : "none", "projectName" : str(project.name), "projectKey" : str(project.key()), "description" : str(project.description), "hasImage" : str(project.hasImage())}

      if form is None:
        templateValues["hasForm"] = "false"
      else:
        templateValues["hasForm"] = "true"
        formHandler = ec.FormHandler()
        #TODO: check that the user is OK
    
      logging.info("Returning project-home values as JSON: " + str(templateValues))
      
      templateValues["loginUrl"] = users.create_login_url(self.request.uri.replace('project.asp', 'project.html?name=' + projectName));
    else:
      templateValues = { "error" : "You do not have permission to view this project " + ("<a href=\"" + users.create_login_url('/project.html?name=' + projectName) + "\">Login</a>" if users.get_current_user() is None else ""), "projectName" : str(project.name), "projectKey" : "", "description" : "", "hasImage" : ""}
    self.response.out.write(unicode(templateValues))
    return


class DoCreateOrEditForm(webapp.RequestHandler):
  def post(self):
    #ticketHandler=ec.TicketHandler()
    #ticketError = ticketHandler.validate(self.request.get("ticket"), self.request.get("projectKey"))
    #if ticketError is not None:
    #  self.response.out.write("Error: "+ticketError)
    #  return
    if users.get_current_user() is None:
      self.response.out.write(unicode("Error: You are not logged in <a href=\"" + users.create_login_url('/project.html?name=' + projectName) + "\">Login</a>"))
      return

    projectKey = self.request.get("projectKey")
    projectName = self.request.get("projectName")
    formKey = self.request.get("formKey")
    formName = self.request.get("formName")
    versionNumber = self.request.get("formVersion")
    allowDownloadEdits = self.request.get("allowDownloadEdits")
    xml = self.request.get("inputXML")
    logging.info("form xml is " + str(xml))

    project = None
    form = None
    if formKey != None and len(formKey.strip()) > 0:
      form = db.get(formKey)
      project = form.project
    else:
      if projectKey != None and len(projectKey.strip()) > 0:
        project = db.get(projectKey)
        projectName = project.name
      elif projectName != None and len(projectName.strip()) > 0:
        projects = db.GqlQuery("SELECT * FROM Project WHERE name = :1", projectName).fetch(1)
        if len(projects) > 0:
          project = projects[0]

    success = ''
    formHandler = ec.FormHandler()
    error = formHandler.validateNameAndVersion(form, formName, versionNumber)
    #If 'XML' button checked, test that the XML is minimally valid
    if error != None:
      self.response.out.write(unicode("Error: " + error))
      return
      
    error = formHandler.validateXML(xml)
    if error != None:
      self.response.out.write(unicode("XML validation Error: " + error))
      return

    form = formHandler.saveXML(xml, formName, versionNumber, project, allowDownloadEdits, sendEmail = True)
    self.response.out.write(unicode(form.key()))

class GetFormXML(webapp.RequestHandler):
  def get(self):
    formKey = self.request.get("formKey")
    formName = self.request.get("name")
    formVersion = self.request.get("version")
    projectKey = self.request.get("projectKey")
    projectName = self.request.get("projectName")
    
    formHandler = ec.FormHandler()
    xml = formHandler.getFormXML(formKey, formName, formVersion, projectKey, projectName)
    logging.info("Responding to form request with xml:\n" + xml)
    self.response.headers['Content-Type'] = "text/xml"
    self.response.out.write(unicode(xml))

class ShowFormHelp(webapp.RequestHandler):
  def get(self):
    templateValues = {}
    path = os.path.join(os.path.dirname(__file__), 'html/formBuilderHelp.html')
    self.response.out.write(unicode(template.render(path, templateValues)))

class GetEntries(webapp.RequestHandler):
  def get(self):
    projectKey = self.request.get("projectKey")
    project = db.get(projectKey)
    #logging.info("getting for for " + projectKey + " " + project.name)
    form = project.getLatestForm()
    if project.protected and form.user != users.get_current_user():
      self.response.out.write("[]")
      return;
      
    formHandler = ec.FormHandler()
    
    offset = int(self.request.get("offset"))
    num = int(self.request.get("num"))
      
    if form is not None:
      #logging.info("got form")
      fieldNames = formHandler.getFields(form)
      #logging.info("form has " + str(len(fieldNames)) + " fields")
      entries = db.GqlQuery("Select * FROM Entry WHERE projectName = :1", project.name)
      
      entryHandler = ec.EntryHandler()
      i = 0
      count = 0
      self.response.out.write("[")
      
      for ent in entries:
        j = 0
        if count == num :
            #self.response.out.write("break")
            break
        if i < offset :
            i += 1
            #self.response.out.write("continue %s" % i)
            continue
        
        photoUrl = "http://epicollectserver.appspot.com/static/no_image.png"
        if ent.hasPhoto():
          if re.match("^[A-Za-z0-9=_-]*$", ent.photoPath) is None:
            photoUrl = 'showImageWithKey?imageKey=' + str(ent.key())
          else:
            logging.info("getting blobstore image")
            photoUrl = 'showImageWithKey?imageKey=' + str(ent.photoPath)
        if count > 0:
            self.response.out.write(",")
        self.response.out.write("{")
        self.response.out.write("\"key\" : \"" + str(ent.key()) + "\",\"title\" : \"" + entryHandler.getTitleStringFor(ent).replace("\n", "<br />").replace("'", "`").replace("\r", "").replace("\"", "\\\"").replace("\t", " ") + "\",")
        self.response.out.write("\"dateCreated\" : \"" + str(ent.timeCreated) + "\",\"latitude\" : \"" + str(ent.location.lat) + "\",")
        self.response.out.write("\"longitude\" : \"" + str(ent.location.lon) + "\",")
        self.response.out.write("\"altitude\" : \"" + str(ent.altitude) + "\",")
        self.response.out.write("\"photo\" : \"" + photoUrl + "\",")
        self.response.out.write("\"image\" : \"<img src=\\\"" + photoUrl + "\\\" height=\\\"32\\\"/>\",")
        self.response.out.write("\"deviceId\" : \"" + str(ent.deviceID) + "\",")
        self.response.out.write("\"entryId\" : \"" + str(ent.entryID) + "\",")
        self.response.out.write("\"lastEdited\" : \"" + str(ent.lastEdited) + "\",")
        self.response.out.write("\"timeUploaded\" : \"" + str(ent.timeUploaded) + "\",")
        self.response.out.write("\"enterpriseName\" : \"" + str(ent.enterpriseName) + "\",")
        self.response.out.write("\"projectName\" : \"" + ent.projectName + "\",")
        
        vals = dict(zip(ent.fieldNames, ent.fieldValues))
        j = 0
        while j < len(fieldNames):
            field = unicode(fieldNames[j])
            if(j > 0):
               self.response.out.write(",")
            if vals.has_key(field):
                self.response.out.write("\"%s\":\"%s\"" % (field, vals[field].replace("\n", "<br />").replace("'", "`").replace("\r", "").replace("\"", "\\\"").replace("\t", " ")))
            else:
               self.response.out.write("\"%s\":\"\"" % (field))
            j += 1
        self.response.out.write("}")
        i += 1
        count += 1
        # while j<len(fieldNames):
          # k=0
          # added = False
          # while k<len(entries[i].fieldNames):
              # logging.info(entries[i].fieldNames[k] +" " + fieldNames[j])
              
              # if entries[i].fieldNames[k] == fieldNames[j]:
                # strOut += "\"" + fieldNames[j] + "\":\"" + entries[i].fieldValues[k].replace("\n", "<br />").replace("'", "\\'").replace("\r", "").replace("\"", "\\\"").replace("\t", " ") + "\""
                # added=True
              # k+=1
          # if not added:
            # strOut += "\"" + fieldNames[j] + "\":\"\""
          # if j < len(fieldNames) - 1:
            # strOut += ","
          # j+=1
          
        # strOut += "}"
        # if i < len(entries) - 1:
          # strOut += ","
        # i+=1
      self.response.out.write("]")

class MiniDomTest(webapp.RequestHandler):
  def get(self):
    projectKey = self.request.get("projectKey")
    project = db.get(projectKey)
    #logging.info("getting for for " + projectKey + " " + project.name)
    form = project.getLatestForm()
    formHandler = ec.FormHandler()
    self.response.out.write(unicode(formHandler.getFullFields(form)))

class ListEntries(webapp.RequestHandler):
  def get(self):
    projectKey = self.request.get("projectKey")
    project = db.get(projectKey)
    #logging.info("getting for for " + projectKey + " " + project.name)
    form = project.getLatestForm()
    formHandler = ec.FormHandler()
    fields = []
    
    if form is not None:
      #logging.info("got form")
      fields = formHandler.getFullFields(form)
  
    isOwner = False
    if users.get_current_user() and form.user:
      logging.info("List Entries : current user " + users.get_current_user().nickname() + " form user " + form.user.nickname())
      isOwner = users.get_current_user() == form.user
    
    upload_url = blobstore.create_upload_url('/upload_photo')
    
    templateValues = {
      'project' : project,
      'fields' : fields,
      'isOwner' : isOwner,
      'projectKey' : projectKey,
      'uploadurl' : upload_url
    }

    path = os.path.join(os.path.dirname(__file__), 'html/listEntries.html')
    self.response.out.write(unicode(template.render(path, templateValues)))

class ListEntriesCSV(webapp.RequestHandler):
  def get(self):
    projectKey = self.request.get("projectKey")
    project = db.get(projectKey)
    #logging.info("getting for for " + projectKey + " " + project.name)
    form = project.getLatestForm()
    formHandler = ec.FormHandler()
    results = []
    self.response.headers['Content-Type'] = 'text/csv'
    
    n = int(self.request.get("limit"))  if self.request.get("limit") != '' else None #number of entries
    o = int(self.request.get("offset")) if  self.request.get("offset") != '' else 0 #how many entries to skip

    if n is not None:
      n = n + o;
      
    i = 0 #iterator
    
    if form is not None:
        #logging.info("got form")
        fieldNames = formHandler.getFields(form)
        #logging.info("form has " + str(len(fieldNames)) + " fields")
        entries = db.GqlQuery("Select * FROM Entry WHERE projectName = :1", project.name)
        entryHandler = ec.EntryHandler()
        j = 0
         
        self.response.out.write('key,dateCreated,latitude,longitude,altitude,deviceId,entryId,lastEdited,timeUploaded,projectName,photo,')
        
        while j < len(fieldNames):
        	self.response.out.write(fieldNames[j] + ',')
        	j += 1
        self.response.out.write('\r\n')
        
        
        for ent in entries:
        
            if o is not None and i < o:
                #self.response.out.write('skip - offset\r\n')
                i += 1
                continue
            if n is not None and i >= n :
                #self.response.out.write('skip - limit\r\n')
                i += 1
                break
        
            self.response.out.write(getString(ent.key()) + ',' + getString(ent.timeCreated) + 
        	',' + getString(ent.location.lat) + ',' + getString(ent.location.lon) + ',' + getString(ent.altitude) + 
        	',' + getString(ent.deviceID) + ',' + getString(ent.entryID) + ',' + getString(ent.lastEdited) + ',' + getString(ent.timeUploaded) + 
        	',' + getString(ent.projectName) + ',"http://epicollectserver.appspot.com/showImageWithKey?imageKey=' + getString(ent.key()) + '",')
        
            vals = dict(zip(ent.fieldNames, ent.fieldValues))
            j = 0
            while j < len(fieldNames):
        		field = unicode(fieldNames[j])
        		if vals.has_key(field):
        			self.response.out.write('"%s",' % vals[field].replace('\n', ' ').replace('"', '`'))
        		else:
        			self.response.out.write('"",')
        		j += 1 
        		
            self.response.out.write('\r\n')
			
			#if i == 100:
			#	p+=1
			#	entries = db.GqlQuery("Select * FROM Entry WHERE projectName = :1", project.name).fetch(100, 100 * p)
			#	if len(entries) > 0:
			#		i = 0;
            i += 1
        
def getString(obj):
  if obj is None:
    return ' '
  else:
    try:
      return str(obj).replace('"', '""')
    except:
      return ' '

class EntryDetails(webapp.RequestHandler):
  def get(self):
    entryKey = self.request.get("key")
    entry = db.get(entryKey)
    
    fields = []
    i = 0
    while i < len(entry.fieldNames):
      value = entry.fieldValues[i]
      if value is not None and len(value) > 0:
        aDict = { 'name' : entry.fieldNames[i], 'value' : value }
      fields.append(aDict)
      i += 1

    i = 0
    while i < len(entry.longFieldNames):
      aDict = { 'name' : entry.longFieldNames[i], 'value' : entry.longFieldValues[i] }
      fields.append(aDict)
      i += 1

    templateValues = {
      'title' : entry.timeCreated,
      'entry' : entry,
      'fields' : fields,
    }

    path = os.path.join(os.path.dirname(__file__), 'html/entryDetails.html')
    self.response.out.write(unicode(template.render(path, templateValues)))

class SaveWebEntry(webapp.RequestHandler):
  def get(self):
    self.post();

  def post(self):
    argsVals = {}
    myArgs = self.request.arguments()
    for arg in myArgs:
      val = self.request.get(arg)
      argsVals[arg] = val

    #logging.info("Received entry data via web: "+str(argsVals))

    entryHandler = ec.EntryHandler()
    responseText = entryHandler.saveFromWeb(argsVals)
    self.response.out.write(responseText)

class SaveEntry(webapp.RequestHandler):
  def get(self):
    self.post();

  def post(self):
    argsVals = {}
    myArgs = self.request.arguments()
    for arg in myArgs:
      val = self.request.get(arg)
      argsVals[unicode(arg)] = unicode(val)

    logging.info("Received entry data: " + str(argsVals))

    entryHandler = ec.EntryHandler()
    responseText = entryHandler.saveEntry(argsVals)
    self.response.out.write(responseText)

class GetSavedEntries(webapp.RequestHandler):
  def get(self):
    enterpriseName = self.request.get("enterprise")
    projectName = self.request.get("project")
    if projectName is None or len(projectName) == 0:
      projectName = self.request.get("application") # legacy naming support

    entryHandler = ec.EntryHandler()
    xml = entryHandler.getSavedEntriesXML(self.request.host_url, enterpriseName, projectName)
    logging.info("Returning entry data: " + xml)
    self.response.headers['Content-Type'] = 'text/xml'
    self.response.out.write(xml)
     
class RemoveEntry(webapp.RequestHandler):
  def get(self):
    self.post()
    
  def post(self):
    
    curUser = users.get_current_user()
    if curUser:  
      projectKey = self.request.get("projectKey")
      project = db.get(projectKey)
      #logging.info("getting for for " + projectKey + " " + project.name)
      form = project.getLatestForm()
      if curUser == form.user or curUser.is_current_user_admin():
        if self.request.get("entryKey"):
          entry = ec.Entry.get(self.request.get("entryKey"))
          entry.delete()
          self.response.out.write({"success":True, "msg":""})
        else:
          self.response.out.write({"success":False, "msg":"You must specify and entry key to remove an entry"})
      else:
        self.response.out.write({"success":False, "msg":"You do not have permission to remove entries from this project"})
    else:
      self.response.out.write({"success":False, "msg":"You must be logged in to remove an entry"})

class StoreImage(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):
    upload_files = self.get_uploads('photo-path') 
    blob_info = upload_files[0]
    self.redirect('/imageStored?key=' + str(blob_info.key()))

class ImageStored(webapp.RequestHandler):
  def get(self):
    self.response.out.write('{"success": true, "msg" :"' + str(self.request.get("key")) + '", "newUrl":"' + blobstore.create_upload_url('/upload_photo') + '"}')
  

class DisplayImage(blobstore_handlers.BlobstoreDownloadHandler):
  def get(self, resource):
    resource = str(urllib.unquote(resource))
    blob_info = blobstore.BlobInfo.get(resource)
    self.send_blob(blob_info)


class SaveImage(webapp.RequestHandler):
  def post(self):
    entryHandler = ec.EntryHandler()
    logging.info("Saving image with arguments " + str(self.request.arguments()))
    for arg in self.request.arguments():
      file = self.request.get(arg)
      response = entryHandler.saveImage(arg, file)
      self.response.out.write(response)

class CountImages(webapp.RequestHandler):
  def get(self):
    query = ec.Entry.all()
    query.filter("image !=", None)
    results = query.fetch()
    self.response.out.write("Found " + str(len(results)) + " images")

class ListImages(webapp.RequestHandler):
  def get(self):
    query = ec.Entry.all()
    query.filter("image !=", None)
    for entry in query:
      imageCount += 1
      self.response.out.write('<a href="' + entry.getImageUrlPath() + '">' + str(imageCount) + "</a>\n")

class ShowImageWithKey(webapp.RequestHandler):
  def get(self):
    key = self.request.get('imageKey').replace('%3D', '=')
    entryHandler = ec.EntryHandler()
    try:
      image = entryHandler.getImageByEntryKey(key)
      try:
        if self.request.get('width') is not None:
          width = int(self.request.get('width'))
        else:
          width = 300
        
        if self.request.get('height') is not None:
          height = int(self.request.get('height'))
        else:
          height = 200
  
        img = images.resize(image, width, height)
        if image is not None:
          self.response.headers['Content-Type'] = 'image/jpeg'
          self.response.out.write(img)
      except:
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(str(image))
    except:
      self.redirect('/displayImage/' + key)
      
class ShowImageNamed(webapp.RequestHandler):
  def get(self):
    fileName = self.request.get('fileName')
    entryHandler = ec.EntryHandler()
    image = entryHandler.getImageByImageName(fileName)
    if image is not None:
      self.response.headers['Content-Type'] = 'image/jpeg'
      self.response.out.write(image)
    else:
      self.response.out.write("Image with file name " + str(fileName) + " not found")

class ShowMap(webapp.RequestHandler):
  def get(self):
    project = None
    projectKey = self.request.get("projectKey")
    projectName = self.request.get("projectName")

    if projectKey != None and len(projectKey.strip()) > 0:
      project = db.get(projectKey)
      if project is not None:
        projectName = project.name
    elif projectName != None and len(projectName.strip()) > 0:
      projects = db.GqlQuery("SELECT * FROM Project WHERE name = :1", projectName).fetch(1)
      if len(projects) > 0:
        project = projects[0]

    if project is None:
      self.response.out.write("Error: no valid project key or name passed in - cannot show map")
      return

    form = project.getLatestForm()
    formKey = self.request.get("formKey")
    if formKey != None and len(formKey.strip()) > 0:
      form = db.get(formKey)

    formHandler = ec.FormHandler()

    doTest = len(self.request.get("doTest")) > 0

    if form is None:
      if doTest:
        form = formHandler.getTestForm()
      else:
        self.response.out.write("Error: no form found for project - cannot show map")
        return

    if doTest:
      entryHandler = ec.EntryHandler()
      entries = entryHandler.generateTestEntriesFor(form, 50)
      
    fields = []
    fields.append("time")
    fields.extend(formHandler.getFields(form))
    
    chartables, markerField = formHandler.getChartables(form)
    logging.info("Chartables: " + str(chartables))

    templateValues = {
      "project" : project,
      "fields" : fields,
      "title" : formHandler.getTitle(form),
      "subtitle" : formHandler.getSubtitle(form),
      "chartables" : chartables,
      "markerField" : markerField,
    }
    
    if doTest:
      templateValues["doTestUrlSuffix"] = "&doTest=true"

    path = os.path.join(os.path.dirname(__file__), 'html/showMap.html')
    self.response.out.write(unicode(template.render(path, templateValues)))

class GetMapXML(webapp.RequestHandler):
  def get(self):
    projectKey = self.request.get("projectKey")
    if projectKey != None and len(projectKey.strip()) > 0:
      project = db.get(projectKey)
      handler = ec.EntryHandler()
      
      number = self.request.get("number")
      offset = self.request.get("offset")
      #logging.info("number = " + str(number) + " offset = " + str(offset))
      try:
        number = int(number)
      except (TypeError, ValueError):
        #logging.warning("Number could not be parsed")
        number = 1000
        
      try:
        offset = int(offset)
      except (TypeError, ValueError):
        #logging.warning("Offset could not be parsed")
        offset = 0
        
      #logging.info("number = " + str(number) + " offset = " + str(offset))
      doTest = len(self.request.get("doTest")) > 0
      #xml = handler.getMapXML(project, self.request.host_url, number, offset, testFlag = doTest
      self.response.headers['Content-Type'] = "text/xml"
      
      entries = db.GqlQuery("Select * FROM Entry WHERE projectName = '%s' LIMIT %s OFFSET %s" % (project.name, number, offset))
      self.response.out.write('<epicollect>')
      for entry in entries:
        
        xml="<Record>"
        xml+="<id>"+entry.entryID+"</id>"
        xml+="<f_time>"+str(entry.timeCreated)+"</f_time>"
        if entry.timeCreated is not None:
            xml+="<timeMillis>"+repr((time.mktime(entry.timeCreated.timetuple()) * 1000) + (entry.timeCreated.microsecond / 1000))+"</timeMillis>"
        else:
            xml+="<timeMillis>0</timeMillis>"
        xml+="<lastEdited>"+str(entry.lastEdited)+"</lastEdited>"
        if entry.lastEdited is not None:
            xml+="<lastEditedMillis>"+repr((time.mktime(entry.lastEdited.timetuple()) * 1000) + (entry.lastEdited.microsecond / 1000))+"</lastEditedMillis>"
        else:
            xml+="<lastEditedMillis>0</lastEditedMillis>"
        xml+="<latitude>"+str(entry.location.lat)+"</latitude>"
        xml+="<longitude>"+str(entry.location.lon)+"</longitude>"
        xml+="<altitude>"+str(entry.altitude)+"</altitude>"
        xml+="<ecPhotoPath>"+entry.getImageUrlPath(self.request.host_url)+"</ecPhotoPath>"
        if entry.userEmail is not None:
          xml+="<userEmail>"+entry.userEmail+"</userEmail>"
          
        i = 0  
        for fieldName in entry.fieldNames:
          fn = fieldName.replace(' ', '_').replace('?','')
          xml+="<f_"+fn+">"+entry.fieldValues[i].replace('&', '&amp;')+"</f_"+fn+">"
          i+=1

        self.response.out.write(xml)
        self.response.out.write('</Record>')
        
      self.response.out.write('</epicollect>')
      #self.response.out.write(xml)
    else:
      self.response.out.write("No project indicated - you must pass in a project key")

class GetMapKML(webapp.RequestHandler):
  def get(self):
    projectKey = self.request.get("projectKey")
    if projectKey != None and len(projectKey.strip()) > 0:
      project = db.get(projectKey)
      handler = ec.EntryHandler()
      
      doTest = len(self.request.get("doTest")) > 0
      kml = handler.getMapKML(project, self.request.host_url, testFlag = doTest)
      self.response.headers['Content-Type'] = "application/vnd.google-earth.kml+xml"
      self.response.headers['Content-Disposition'] = 'attachment; filename=' + str(time.time()) + '.kml'
      self.response.out.write(kml)

    else:
      self.response.out.write("No project indicated - you must pass in a project key")

class GetKMLFeed(webapp.RequestHandler):
    def get(self):
        projectKey = self.request.get("projectKey")
        if projectKey != None and len(projectKey.strip()) > 0:
            self.response.headers['Content-Type'] = "application/vnd.google-earth.kml+xml"
            self.response.headers['Content-Disposition'] = 'attachment; filename=' + str(time.time()) + '.kml'
             
            self.response.out.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?><kml xmlns=\"http://www.opengis.net/kml/2.2\" xmlns:gx=\"http://www.google.com/kml/ext/2.2\" xmlns:kml=\"http://www.opengis.net/kml/2.2\" xmlns:atom=\"http://www.w3.org/2005/Atom\"><NetworkLink><name>EpiCollect</name><open>1</open><Link><href>" + self.request.url.replace("getKmlFeed", "getMapKml") + "</href><refreshMode>onInterval</refreshMode><refreshInterval>30</refreshInterval></Link></NetworkLink></kml>")
        else:
            self.response.out.write("No project indicated - you must pass in a project key")

class ValidateTicket(webapp.RequestHandler):
  def get(self):
    #if the user's logged in, that's OK too
    logging.info(self.request.get("projectKey"))
    if self.request.get("projectKey") == "":
      projects = db.GqlQuery("SELECT * FROM Project WHERE name = :1", self.request.get("projectName")).fetch(1)
      if len(projects) > 0:
        project = projects[0]
      else:
         self.response.set_status(401, "No Project found") 
    else:
      project = db.get(self.request.get("projectKey"))
       
    ticketHandler = ec.TicketHandler()
    ticketError = ticketHandler.validate(self.request.get("ticket"), project.key())
    if ticketError is None:
      self.response.out.write("ticket validated")
    else:
      self.response.set_status(401, ticketError)
      self.response.out.write(ticketError)

class LoginIframe(webapp.RequestHandler):
  def get(self):
    ticketString = self.request.get("ticket")
    ticket = ec.Ticket(id = ticketString, user = users.User())
    ticket.put()
    logging.info("Created ticket with ID " + ticket.id + " for user " + str(ticket.user))
    self.redirect(self.request.host_url + "/login-successful.html?destination=" + self.request.get("destination") + "&ticket=" + ticketString + "&projectKey=" + self.request.get("projectKey") + "&projectName=" + self.request.get("projectName"))

class RunServerTest(webapp.RequestHandler):
  def get(self):
    tester = servertest.ECServerTester()
    message = tester.runServerTest()
    self.response.out.write(message)

class RunLoadTest(webapp.RequestHandler):
  def get(self):
    tester = servertest.ECServerTester()
    message = tester.runLoadTest()
    self.response.out.write(message)

class DoTweak(webapp.RequestHandler):
  def get(self):
    forms = db.GqlQuery("SELECT * FROM Form WHERE name = :1", "UrbanBeasts").fetch(1)
    form = forms[0]
    formHandler = ec.FormHandler()
    requestError = formHandler.initiateApkRequest(form)
    self.response.out.write(requestError)


class AddEnterprise(webapp.RequestHandler):
  def get(self):
    error = ''
    newName = self.request.get("enterpriseName")
    existing = db.GqlQuery("Select * FROM Enterprise WHERE name = :1", newName).fetch(1)
    if len(existing) > 0:
      error = "Sorry - the name " + newName + " is already in use."
    elif len(newName.strip()) == 0:
      error = "You must enter a name."
    else:
      newEnt = ec.Enterprise(name = newName)
      newEnt.put()

    results = db.GqlQuery("Select * FROM Enterprise")
    templateValues = {
      'error' : error,
      'enterprises' : results,
    }

    path = os.path.join(os.path.dirname(__file__), 'html/index.html')
    self.response.out.write(unicode(template.render(path, templateValues)))

class AddProject(webapp.RequestHandler):
  def get(self):
    error = ''
    enterpriseKey = self.request.get("enterpriseKey")
    enterprise = db.get(enterpriseKey)
    
    protected = self.request.get("protect") == "true"
    newName = self.request.get("projectName")
    existing = db.GqlQuery("Select * FROM Project WHERE enterprise = :1 AND name = :2", enterprise, newName).fetch(1)
    if len(existing) > 0:
      error = "Sorry - the project name " + newName + " is already in use for this enterprise."
    elif len(newName.strip()) == 0:
      error = "You must enter a name."
    else:
      newProj = ec.Project(enterprise = enterprise, name = newName, protected = protected)
      newProj.put()

    results = db.GqlQuery("Select * FROM Project WHERE enterprise = :1", enterprise)
    templateValues = {
      'error' : error,
      'enterprise' : enterprise,
      'projects' : results
    }

    path = os.path.join(os.path.dirname(__file__), 'html/listProjects.html')
    self.response.out.write(unicode(template.render(path, templateValues)))

class ListProjects(webapp.RequestHandler):
  def get(self):
    enterpriseKey = self.request.get("enterpriseKey")
    enterprise = db.get(enterpriseKey)

    results = db.GqlQuery("Select * FROM Project WHERE enterprise = :1", enterprise)
    templateValues = {
      'enterprise' : enterprise,
      'projects' : results
    }

    path = os.path.join(os.path.dirname(__file__), 'html/listProjects.html')
    self.response.out.write(unicode(template.render(path, templateValues)))

class ListForms(webapp.RequestHandler):
  def get(self):
    error = ''

    projectKey = self.request.get("projectKey")
    project = None
    if projectKey != None and len(projectKey.strip()) > 0: 
      project = db.get(projectKey)

    results = db.GqlQuery("Select * FROM Form WHERE project = :1", project)
    templateValues = {
      'error' : error,
      'project' : project,
      'forms' : results
    }

    path = os.path.join(os.path.dirname(__file__), 'html/listForms.html')
    self.response.out.write(unicode(template.render(path, templateValues)))

class ListMessages(webapp.RequestHandler):
  def get(self):
    sm = ec.SiteMessage();
    results = sm.getSiteMessages();
    if type(results) == str:
      templateValues = {"messages" : False, "error": results}
    else:    
      templateValues = {"messages" : results}
    
    path = os.path.join(os.path.dirname(__file__), 'html/feedback.html')
    self.response.out.write(unicode(template.render(path, templateValues)))

class StoreMessage(webapp.RequestHandler):
  def get(self):
    sm = ec.SiteMessage();
    sm.storeMessage(self.request.get('sender'), self.request.get('subject'), self.request.get('message'), self.request.get('feedbackType'))
    self.response.out.write('{"success":true,"msg":"successs"}')

class MarkMessageRead(webapp.RequestHandler):
  def get(self):
    post(self)

  def post(self):
    sm = db.get(self.request.get("msgKey"))
    sm.readBy = users.get_current_user()
    sm.put();
                               
class GetTestData(webapp.RequestHandler):
  def get(self):
    testData = "<entries>"
    testData += "<entry><appID>testApp</appID><deviceID>testDevice</deviceID>"
    testData += "<latitude>-37.0</latitude><longitude>19.5</longitude><timeCreated>2009-09-09 19:19:19</timeCreated>"
    testData += "<title>Test Title 1</title><subtitle>This came all the way from the server</subtitle><random>Random</random></entry>\n"
    testData += "<entry><appID>default</appID><deviceID>testDevice</deviceID>"
    testData += "<latitude>-36.0</latitude><longitude>99.5</longitude><timeCreated>2009-09-09 19:19:21</timeCreated>"
    testData += "<title>Test Title 2</title><subtitle>This did too.</subtitle><randomer>Randomer</randomer></entry>\n"
    testData += "</entries>"
    self.response.out.write(testData)

class GetTestForm(webapp.RequestHandler):
  def get(self):
    formHandler = ec.FormHandler()
    testForm = formHandler.getTestForm()
    self.response.headers['Content-Type'] = "text/xml"
    self.response.out.write("<xform>\n")
    self.response.out.write("<model> <submission id=\"test-form\" allowDownloadEdits=\"true\" versionNumber=\"1.11\"/> </model>\n")
    self.response.out.write(testForm.xml + "\n</xform>")

class GetForm1(webapp.RequestHandler):
  def get(self):
    formData = "<xform>\n"
    formData += "<model> <submission id=\"test form\" allowDownloadEdits=\"false\" versionNumber=\"1.1\"/> </model>\n"
    formData += "<input ref=\"title\"> <label>Title</label> </input>\n"
    formData += "<input ref=\"species\"> <label>Species</label> </input>\n"
    formData += "<input ref=\"ph\"> <label>pH Level</label> </input>\n"
    formData += "<textarea ref=\"observations\"> <label>Observations</label> </textarea>\n"
    formData += "</xform>"
    self.response.out.write(formData)
    
class GetForm2(webapp.RequestHandler):
  def get(self):
    formData = "<xform>\n"
    formData += "<model> <submission id=\"test-form\" allowDownloadEdits=\"false\" versionNumber=\"1.1\"/> </model>\n"
    formData += "<input ref=\"subtitle\"> <label>Sub-Title</label> </input>\n"
    formData += "<input ref=\"user\"> <label>User</label> </input>\n"
    formData += "<select ref=\"environment\"> <label>Surroundings</label> <item><label>Treees</label><value>arboreal</value></item> <item><label>Water</label><value>aquatic</value></item> <item><label>Rocks</label><value>geologic</value></item> </select>\n"
    formData += "<input ref=\"species\"> <label>Species</label> </input>\n"
    formData += "<select1 ref=\"status\"> <label>Status</label> <item><label>Alive</label><value>live</value></item> <item><label>Deceased</label><value>dead</value></item> <item><label>Unknown</label><value>indeterminate</value></item> </select1>\n"
    formData += "<input ref=\"ph\"> <label>pH Level</label> </input>\n"
    formData += "<textarea ref=\"comments\"> <label>Comments</label> </textarea>\n"
    formData += "</xform>"
    self.response.out.write(formData)

class GenerateTestData(webapp.RequestHandler):
  def get(self):
    formKey = self.request.get("formKey")
    formName = self.request.get("formName")
    formVersion = self.request.get("formVersion")
    projectKey = self.request.get("projectKey")
    projectName = self.request.get("projectName")

    formHandler = ec.FormHandler()
    form = formHandler.getFormFor(formKey, formName, formVersion, projectKey, projectName)
    if form is None:
      form = formHandler.getTestForm()
    entryHandler = ec.EntryHandler()
    entries = entryHandler.generateTestEntriesFor(form, 50)
    for entry in entries:
      entry.put()
    self.response.out.write("Generated 50 new test entries for form " + form.name)



def main():
  application = webapp.WSGIApplication([
    ('/', MainHandler),
    ('/about', About),
    ('/media', Media),
    ('/help', Help),
    ('/tutorial', Tutorial),
    ('/template', Template),

    ('/createProject', CreateProject),
    ('/createProject.asp', CreateProject),
    ('/updateProject', EditProject),
    ('/updateProject.asp', EditProject),
    ('/projectHome', ProjectHome),
    ('/project.asp', ProjectHome),
    ('/projectImage', ProjectImage),
    ('/projectImage.asp', ProjectImage),
    ('/project.html', ProjectMenu),
    ('/ProjectDescription.html', ProjectDescription),
    
    ('/buildForm', DoCreateOrEditForm),
    ('/saveForm.asp', DoCreateOrEditForm),
    ('/getForm', GetFormXML),
    ('/getForm.asp', GetFormXML),
    ('/formHelp', ShowFormHelp),
    ('/formHelp.asp', ShowFormHelp),
    
    ('/listEntries', ListEntries),
    ('/getEntries', GetEntries),
    ('/listEntriesCSV', ListEntriesCSV),
    ('/listEntriesCSV.csv', ListEntriesCSV),
    ('/entryDetails', EntryDetails),
    ('/uploadToServer', SaveEntry),
    ('/saveEntryWeb', SaveWebEntry),
    ('/downloadFromServer', GetSavedEntries),
    ('/updateEntry', SaveEntry),
    ('/removeEntry', RemoveEntry),
    ('/upload_photo', StoreImage),
    ('/displayImage/([^/]+)?', DisplayImage),
    ('/imageStored', ImageStored),
    
    ('/uploadImageToServer', SaveImage),
    ('/countImages', CountImages),
    ('/listImages', ListImages),
    ('/showImageWithKey', ShowImageWithKey),
    ('/showImageNamed', ShowImageNamed),
    
    ('/showMap', ShowMap),
    ('/getMapXML', GetMapXML),
    ('/getMapKML', GetMapKML),
    ('/getMapKml', GetMapKML),
    ('/getKmlFeed', GetKMLFeed),
    
    ('/sendFeedback', StoreMessage),
    ('/feedback', ListMessages),
    ('/markMessage', MarkMessageRead),
    
    #login
    ('/validateTicket', ValidateTicket),
    ('/validateTicket.asp', ValidateTicket),
    ('/ecLogin', LoginIframe),
    ('/ecLogin.asp', LoginIframe),
    
    #not currently used
    ('/addEnterprise', AddEnterprise),
    ('/addProject', AddProject),
    ('/showProjectsFor', ListProjects),
    ('/showFormsFor', ListForms),

    #test
    ('/runServerTest', RunServerTest),
    ('/runLoadTest', RunLoadTest),
    ('/tweak', DoTweak),
    ('/miniDomTest', MiniDomTest),
    #test accessors
    ('/getTestForm', GetTestForm),
    ('/getTestForm1', GetForm1),
    ('/getFormDefinition', GetForm1),
    ('/getTestForm2', GetForm2),
    ('/getFormDefinition2', GetForm1),
    ('/downloadTestData', GetTestData),
    ('/generateTestData', GenerateTestData),
    
    ],
    debug = True)

  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
