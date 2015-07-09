import os
import logging
import random
import time
import urllib
import re

from datetime import datetime
from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.api import users

from HTMLParser import HTMLParser, HTMLParseError
from xml.dom.minidom import parse, parseString

class SiteMessage(db.Model):
  sender = db.EmailProperty()
  subject = db.StringProperty()
  readBy = db.UserProperty()
  message = db.TextProperty()
  feedbackType = db.StringProperty()
  
  def getSiteMessages(self):
    if users.is_current_user_admin():
      query = SiteMessage.all()
      query.filter('readBy', None)
      msgs = query.fetch(100)
      return msgs
    else:
      return "User is not admin"

  def storeMessage(self, _sender, _subject, _message, _feedbackType):
    msg = SiteMessage(sender = db.Email(_sender), subject= _subject, feedbackType = _feedbackType, readBy = None, message = _message)
    msg.put();

class Enterprise (db.Model):
  name = db.StringProperty()

class Project(db.Model):
  enterprise = db.ReferenceProperty(Enterprise)
  name = db.StringProperty()
  description = db.TextProperty()
  image = db.BlobProperty()
  protected = db.BooleanProperty()  
  
  def getLatestForm(self):
    forms = db.GqlQuery("Select * FROM Form WHERE project = :1 ORDER BY timeCreated DESC", self.key()).fetch(1)
    if len(forms)>0:
      return forms[0]
    else:
      return None
    
  def saveImage(self, fileName, file):
      MaxBTSize=1000000
      logging.info("attemptingToSaveProjectImage")
      if len(file)<MaxBTSize:
        logging.info("savingImageAsObject")  
        self.image = db.Blob(file)
        logging.info("Successfully received small image "+fileName)
        return "Successfully received image "+fileName
      else:
        logging.info("savingImageAsChunks") 
        marker=0
        while marker*MaxBTSize<len(file):
          if MaxBTSize*(marker+1)>len(file):
            chunk = ProjectImageChunk(projectRef=self, index=marker, chunk=db.Blob(file[MaxBTSize*marker:]))
          else:
            chunk = ProjectImageChunk(projectRef=self, index=marker, chunk=db.Blob(file[MaxBTSize*marker:MaxBTSize*(marker+1)]))
          chunk.put()
          marker+=1
        logging.info("Successfully received large image "+fileName)
        return "Successfully received image "+fileName

  def removeImage(self):
    self.image = None;
    imageChunks = db.GqlQuery("SELECT * FROM ProjectImageChunk WHERE ProjectEntryRef = :1 ORDER BY index", self.key()).fetch(1000)
    db.delete(imageChunks)    
  
  def getImage(self):
    if self.image is not None:
      return self.image
    
    chunks = db.GqlQuery("SELECT * FROM ProjectImageChunk WHERE ProjectEntryRef = :1 ORDER BY index", self.key()).fetch(1000)
    if len(chunks)==0:
      return None

    image=""
    for chunkRow in chunks:
      image+=chunkRow.chunk
    return image

  def hasImage(self): 
    chunks = db.GqlQuery("SELECT * FROM ProjectImageChunk WHERE ProjectEntryRef = :1 ORDER BY index", self.key()).fetch(1000)
    return (len(chunks) > 0) | (self.image is not None)

class Form(db.Model):
  timeCreated = db.DateTimeProperty(auto_now_add=True)
  user = db.UserProperty()
  project = db.ReferenceProperty(Project)
  name = db.StringProperty()
  xml = db.TextProperty()
  versionNumber = db.StringProperty()
  allowDownloadEdits = db.BooleanProperty()

  def getXformXML(self):
    projectName="None"
    if self.project is not None:
      projectName = self.project.name

    xml ="<xform> "
    xml+= '<model> <submission id="'+self.name
    xml+='" projectName="'+unicode(projectName)
    xml+='" allowDownloadEdits="'+str(self.allowDownloadEdits).lower()
    xml+='" versionNumber="'+self.versionNumber
    xml+='" /> </model>\n'
    xml+= self.xml
    xml+= "</xform>\n"
    return xml

class Entry (db.Model):
  project = db.ReferenceProperty(Project)
  timeCreated = db.DateTimeProperty()
  lastEdited = db.DateTimeProperty()
  timeUploaded = db.DateTimeProperty(auto_now_add=True)
  entryID = db.StringProperty()
  deviceID = db.StringProperty()
  enterpriseName = db.StringProperty() #denormalize for performance...
  projectName = db.StringProperty() #denormalize for performance...
  userEmail = db.StringProperty()
  altitude = db.FloatProperty()
  location = db.GeoPtProperty()
  fieldNames = db.StringListProperty()
  fieldValues = db.StringListProperty()
  longFieldNames = db.StringListProperty()
  longFieldValues = db.ListProperty(db.Text)
  photoPath = db.StringProperty()
  mediaPaths = db.StringProperty()
  image = db.BlobProperty()

  def getKVDict(self):
    kv={}
    i=0
    while i<len(self.fieldNames):
      kv[self.fieldNames[i]]=self.fieldValues[i]
      i+=1
    i=0
    while i<len(self.longFieldNames):
      kv[self.longFieldNames[i]]=self.longFieldValues[i]
      i+=1
    return kv

  def hasPhoto(self):
    has = False
    if self.image is not None and self.image != "":
      return True
    elif self.photoPath is not None and self.photoPath != "":
      if re.match("^[A-Za-z0-9=_-]*$",self.photoPath) is None:
        has = True
      else:
        return True
    chunks = db.GqlQuery("SELECT * FROM ImageChunk WHERE entryRef = :1 ORDER BY index", self.key()).fetch(1000)
    #logging.info("hasPhoto :: number of chunks = " + str(len(chunks)))
    has = len(chunks) > 0
    return has
    
    

  #returns the URL for the image for this entry, relative to localhost
  def getImageUrlPath(self, hostUrl):
    if self.hasPhoto():
      if re.match("^[A-Za-z0-9=_-]*$",self.photoPath) is None :
        return hostUrl+"/showImageWithKey?imageKey="+str(self.key())
      else :
        return hostUrl+"/showImageWithKey?imageKey="+str(self.photoPath)
    return ""

class ImageChunk(db.Model):
  entryRef = db.ReferenceProperty(Entry)
  index = db.IntegerProperty()
  chunk = db.BlobProperty()

class ProjectImageChunk(db.Model):
  projectRef = db.ReferenceProperty(Project)
  index = db.IntegerProperty()
  chunk = db.BlobProperty()

class Ticket (db.Model):
  timeCreated = db.DateTimeProperty(auto_now_add=True)
  user = db.UserProperty()
  id = db.StringProperty()


class TicketHandler:
  def validate(self, ticketID, projectKey):
    logging.info("Validating ticket with ID "+ticketID)

    project = db.get(projectKey)
    if project is None:
      return "No project found for the given key"
    
    currentUser = users.get_current_user()
    form = project.getLatestForm()
    if currentUser is not None:
      #if there's no existing form, so just being logged on validates you
      if form is None or form.user is None or currentUser==form.user:
        return None
      else:
        logging.info("Mismatch of current user "+str(currentUser)+" with form user "+str(form.user))
        return "Sorry! Only the "+str(form.user)+" Google Account may edit this form."

    #OK, we need to parse the ticket
    if ticketID is None or len(ticketID)==0:
      return "No ticket provided"

    tickets = db.GqlQuery("SELECT * FROM Ticket WHERE id = :1 ORDER BY timeCreated DESC", ticketID).fetch(1)
    if len(tickets)==0:
      return "Ticket "+str(ticketID)+" not found"
  
    ticket=tickets[0]
    delta = time.time()-time.mktime(ticket.timeCreated.timetuple())
    if delta > 10800: # tickets are good for 3 hours
      return "Ticket "+str(ticketID)+" is more than 3 hours old and hence invalid"
    
    logging.info("Ticket validated as user "+str(ticket.user))
    if form is None or form.user is None:
      return None
    elif form.user == ticket.user:
      return None
    else:
      logging.info("Mismatch with form user "+str(form.user))
      return "Sorry! Only the "+str(form.user)+" Google Account may edit this form."



class EntryHandler:
  def saveFromWeb(self, argsVals):
    lat = None
    long = None
    entry=Entry()
    formFields = [];
    
    if argsVals["key"] != "":
      entry = Entry.get(argsVals["key"]);
    #Check project Exists and get project and form
    if argsVals["projectName"] == "":
      return "{\"success\":false,\"msg\":\"entry must specify a project name\"}"
    else:
      entry.projectName=argsVals["projectName"]
      q = db.GqlQuery("SELECT * FROM Project WHERE name = :1", entry.projectName)
      projects = q.fetch(1)
      if len(projects)==0:
         return "{\"success\":false,\"msg\":\"project could not be found\"}"
      else:
        project = projects[0] 
        entry.project=project
        fh = FormHandler()
        formFields = fh.getFullFields(project.getLatestForm());
    if argsVals["dateCreated"]!="":
      
      entry.timeCreated=datetime.strptime(argsVals["dateCreated"].split(".")[0], '%Y-%m-%d %H:%M:%S')
    else:
      entry.timeCreated=datetime.utcnow()
    entry.altitude = float(argsVals["altitude"])
    lat = float(argsVals["latitude"])
    long = float(argsVals["longitude"])
    entry.entryID=argsVals["entryId"]
    entry.deviceId=argsVals["deviceId"]
    entry.photoPath=argsVals["photo"] if argsVals["photo"] != "" else None
    
    args=[]
    vals=[]
    for field in formFields:
     
      vals.append(argsVals[field["name"]])
      args.append(field["name"])
      #logging.info(str(arg) + " = " + str(val))

    try:
      entry.location=db.GeoPt(lat,long)
    except db.BadValueError:
      logging.warn("Could not build GeoPt from latitude value "+str(lat)+" longitude value "+str(long))
      entry.location = None

    #OK, we've handled the required EpiCollect fields.
    try:
      #logging.info("Saving values "+str(vals)+" for fields "+str(args))

      #Now deal with long form fields - move them to the "longFieldNames" and "longFieldValues" lists.
      #we should make sure we don't store redundant fields
      
      
      longArgs=[]
      longVals=[]
      i=0
      while i<len(vals):
        if len(vals[i])>=500:
          longArgs.append(args.pop(i))
#          longVals.extend(db.Text(vals.pop(i), encoding="utf-8"))
          longVals.append(db.Text(vals.pop(i)))
        else:
          i+=1

      entry.fieldNames=args
      entry.fieldValues=vals
      entry.longFieldNames=longArgs
      entry.longFieldValues=longVals
      entry.lastEdited=datetime.utcnow();
      if entry.timeUploaded is None:
        entry.timeUploaded=datetime.utcnow();
      entry.put();
 
      return "{\"success\" : true, \"msg\": \"received entry "+str(entry.entryID)+"\"}"
 
    except db.BadValueError, reason:
      logging.error("Could not save field names & values - save aborted "+str(reason))
      return "Failed to write entry to server database - try again later?"

    except db.NotSavedError, reason:
      logging.error("Could not save entry to DB! "+str(reason))
      return "Failed to save entry to server database - try again later?"
  
  def saveEntry(self, argsVals):
    lat = None
    long = None
    entry=Entry()

    args = argsVals.keys()
    vals=[]
    for thisArg in args:
      val=argsVals[thisArg]
      vals.append(val)
      arg=thisArg.lower()

      try:
        if arg==u'ectimecreated':
          seconds=float(val)
          if seconds>1000000000000.0: # if we're dealing with milliseconds not seconds
            seconds=seconds/1000
          entry.timeCreated=datetime.utcfromtimestamp(seconds)
        elif arg==u'eclastedited':
          seconds=float(val)
          if seconds>1000000000000.0: # if we're dealing with milliseconds not seconds
            seconds=seconds/1000
          entry.lastEdited=datetime.utcfromtimestamp(seconds)
        elif arg==u'ecaltitude':
          entry.altitude=float(val)
        elif arg==u'eclatitude':
          lat=float(val)
        elif arg==u'eclongitude':
          long=float(val)
        elif arg==u'ecentryid':
          entry.entryID=val
        elif arg==u'ecdeviceid':
          entry.deviceID=val
        elif arg==u"ecuseremail":
          entry.userEmail=val
        elif arg==u"ecappname" or arg==u"ecprojectname":
          entry.projectName=val
          q = db.GqlQuery("SELECT * FROM Project WHERE name = :1", val)
          projects = q.fetch(1)
          if len(projects)==0:
            project = Project(name=val, enterprise = None)
            project.put()
          else:
            project = projects[0]
          entry.project=project
#          if len(existingProject)==0 and entry.enterpriseName is not None: #we have an enterprise, can go ahead and insert now
#            q2 = db.GqlQuery("SELECT * FROM ENTERPRISE WHERE name = :2", entry.enterpriseName)
#            existingEnterprises = q2.fetch(1)
#            if len(existingEnterprises)>0:
#              project = Project(name=val, enterprise = existingEnterprises[0])
#              project.put()
#            else:
#              project = existingProject[0]
#            entry.project=project
#        elif arg=="ecenterprisename":
#          entry.enterpriseName=val
#          q = db.GqlQuery("SELECT * FROM Enterprise WHERE name = :1", val)
#          existing = q.fetch(1)
#          if len(existing)==0:
#            newEnt = Enterprise(name=val)
#            newEnt.put()
#            if entry.projectName is not None: #in case the project name came in first
#              project = Project(name=entry.projectName, enterprise = newEnt)
#              project.put()
        elif arg=="ecphotopath":
          entry.photoPath=val
      except ValueError, reason:
        logging.warn("Value error for field name "+thisArg+" value " +unicode(val)+" reason "+str(reason))
      except db.BadValueError, reason:
        logging.warn("Bad value error for field name "+thisArg+" value "+unicode(val)+" reason "+str(reason))

    try:
      entry.location=db.GeoPt(lat,long)
    except db.BadValueError:
      logging.warn("Could not build GeoPt from latitude value "+str(lat)+" longitude value "+str(long))
      entry.location = None

    #OK, we've handled the required EpiCollect fields.
    try:
      logging.info("Saving values "+str(vals)+" for fields "+str(args))

      #Now deal with long form fields - move them to the "longFieldNames" and "longFieldValues" lists.
      longArgs=[]
      longVals=[]
      i=0
      while i<len(vals):
        if len(vals[i])>=500:
          longArgs.append(args.pop(i))
#          longVals.extend(db.Text(vals.pop(i), encoding="utf-8"))
          longVals.append(db.Text(vals.pop(i)))
        else:
          i+=1

      entry.fieldNames=args
      entry.fieldValues=vals
      entry.longFieldNames=longArgs
      entry.longFieldValues=longVals
      
      logging.info("entry id is " + entry.entryID)
      #Now, handle the case that the entry has already been uploaded
      query = db.GqlQuery("SELECT * FROM Entry WHERE entryID = :1", entry.entryID)
      results = query.fetch(1)
      
      if len(results) == 0:
        entry.put()
      else:
        localTimeEdited = results[0].lastEdited
        if localTimeEdited is None or localTimeEdited<entry.lastEdited:
          entry.put()
          results[0].delete()
        else:
          logging.info("Discarding uploaded entry "+str(entry.entryID)+" - local version is more recent")
 
      return "Success: received entry "+str(entry.entryID)
 
    except db.BadValueError, reason:
      logging.error("Could not save field names & values - save aborted "+str(reason))
      return "Failed to write entry to server database - try again later?"

    except db.NotSavedError, reason:
      logging.error("Could not save entry to DB! "+str(reason))
      return "Failed to save entry to server database - try again later?"


  def saveImage(self, fileName, file):
      MaxBTSize=1000000
      query = Entry.all()
      query.filter("photoPath =", fileName)
      results=query.fetch(1)
      if len(results)==0:
        logging.warning("Error - could not find the entry associated with image "+fileName+" on this server")
        return "Failed"
      else:
        entry = results[0]
        if len(file)<MaxBTSize:
          entry.image = db.Blob(file)
          entry.put()
          logging.info("Successfully received small image "+fileName)
          return "Successfully received image "+fileName
        else:
          marker=0
          while marker*MaxBTSize<len(file):
            if MaxBTSize*(marker+1)>len(file):
              chunk = ImageChunk(entryRef=entry, index=marker, chunk=db.Blob(file[MaxBTSize*marker:]))
            else:
              chunk = ImageChunk(entryRef=entry, index=marker, chunk=db.Blob(file[MaxBTSize*marker:MaxBTSize*(marker+1)]))
            chunk.put()
            marker+=1
          logging.info("Successfully received large image "+fileName)
          return "Successfully received image "+fileName


  def getImageByEntryKey(self, key):
    entry = db.get(key)
    if entry is None:
      return None
    return self.getImageForEntry(entry)

  def getImageByImageName(self, fileName):
    entries = db.GqlQuery("Select * FROM Entry WHERE photoPath = :1", fileName).fetch(1)
    if len(entries)==0:
      return None
    return self.getImageForEntry(entries[0])
      
  def getImageForEntry(self, entry):
    if entry.image is not None:
      return entry.image

    chunks = db.GqlQuery("SELECT * FROM ImageChunk WHERE entryRef = :1 ORDER BY index", entry.key()).fetch(1000)
    if len(chunks)==0:
      return None

    image=""
    for chunkRow in chunks:
      image+=chunkRow.chunk
    return image


  def getMapXML(self, project, hostUrl, number=1000, offset=0, testFlag=False):
    if project is None:
      return "Error - no project"
    
    if testFlag:
      t ="<EpiCollect><Record>"
      t+="<time>2010-03-30 20:41:37.160000</time><timeMillis>1269981697160</timeMillis>"
      t+="<lastEdited>2010-03-30 20:43:15.050000</lastEdited><lastEditedMillis>1269981795050</lastEditedMillis>"
      t+="<id>testEntry32F12A85-BE9E-45F1-8B8C-818FD4CEA8BE-241-0000001C458633590</id>"
      t+="<altitude>151.198226968</altitude><latitude>51.3694322146</latitude><longitude>-0.175511183306</longitude>"
      t+="<userEmail>test@example.com</userEmail><ecPhotoPath></ecPhotoPath><short>Test short 0</short><long>Test long 0</long>"
      t+="<one>three</one><many>one</many>"
      t+="</Record><Record>"
      t+="<time>2010-03-30 20:41:08.820000</time><timeMillis>1269981668820</timeMillis>"
      t+="<lastEdited>2010-03-30 20:42:27.100000</lastEdited><lastEditedMillis>1269981747100</lastEditedMillis>"
      t+="<id>testEntry32F12A85-BE9E-45F1-8B8C-818FD4CEA8BE-241-0000001C458633591</id>"
      t+="<altitude>748.162007775</altitude><latitude>51.7268305243</latitude><longitude>-0.12230282448</longitude>"
      t+="<userEmail>test2@example.com</userEmail><ecPhotoPath></ecPhotoPath><short>Test short 1</short><long>Test long 1</long>"
      t+="<one>three</one><many>three</many>"
      t+="</Record></EpiCollect>"
      return t
      formHandler = FormHandler()
      form = project.getLatestForm()
      if form is None:
        form = formHandler.getTestForm()
      entries=self.generateTestEntriesFor(form)
    else:
      if project.protected and form.user != users.get_current_user():
        self.response.out.write("[]")
        return;
      #entries = self.getSavedEntries(None, project.name, 200, offset)
      entries = db.GqlQuery("Select * FROM Entry WHERE projectName = '%s' LIMIT %s OFFSET %s" % (project.name, number, offset))
      
    xml = '<EpiCollect>'
    j = 0;
    #while j < number: 
    for entry in entries:
        
        xml+="<Record>"
        xml+="<id>"+entry.entryID+"</id>"
        xml+="<f_time>"+str(entry.timeCreated)+"</f_time>"
        if entry.timeCreated is not None:
            xml+="<timeMillis>"+repr((time.mktime(entry.timeCreated.timetuple()) * 1000) + (entry.timeCreated.microsecond / 1000))+"</timeMillis>"
        else:
            xml+="<timeMillis>0</timeMillis>"
        xml+="<lastEdited>"+str(entry.lastEdited)+"</lastEdited>"
        if entry.timeCreated is not None:
            xml+="<lastEditedMillis>"+repr((time.mktime(entry.lastEdited.timetuple()) * 1000) + (entry.lastEdited.microsecond / 1000))+"</lastEditedMillis>"
        else:
            xml+="<lastEditedMillis>0</lastEditedMillis>"
        xml+="<latitude>"+str(entry.location.lat)+"</latitude>"
        xml+="<longitude>"+str(entry.location.lon)+"</longitude>"
        xml+="<altitude>"+str(entry.altitude)+"</altitude>"
        xml+="<ecPhotoPath>"+entry.getImageUrlPath(hostUrl)+"</ecPhotoPath>"
        if entry.userEmail is not None:
          xml+="<userEmail>"+entry.userEmail+"</userEmail>"
        i=0
        for fieldName in entry.fieldNames:
          fn = fieldName.replace(' ', '_').replace('?','')
          xml+="<f_"+fn+">"+entry.fieldValues[i].replace('&', '&amp;')+"</f_"+fn+">"
          i+=1
        i=0
        for name in entry.longFieldNames:
          fn = fieldName.replace(' ', '_').replace('?','')
          xml+="<f_"+fn+">"+entry.longFieldValues[i].replace('&', '&amp;')+"</f_"+fn+">"
          i+=1
        xml+="</Record>"
        j += 1
        if j == number:
          break
      #entries = self.getSavedEntries(None, project.name, 200, offset + j)
      #if len(entries) == 0:
      #  break
    xml+="</EpiCollect>"
    return xml

  def getMapKML(self, project, hostUrl, testFlag=False):
    if project is None:
      return "Error - no project"
    
    formHandler = FormHandler()
    form = project.getLatestForm()
    if form is None:
      form = formHandler.getTestForm()

    if testFlag:
      entries=self.generateTestEntriesFor(form)
    else:
      entries = self.getSavedEntries(None, project.name)

    kml = '<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://earth.google.com/kml/2.0">\n<Document>\n'
    kml+= '<Style id="normalPlacemark"><IconStyle>\n<Icon>\n<href>http://labs.google.com/ridefinder/images/mm_20_red.png</href>\n</Icon>\n</IconStyle>\n</Style>\n'
    kml+= '<Style id=\"highlightPlacemark\">\n<IconStyle>\n<Icon>\n<href>http://labs.google.com/ridefinder/images/mm_20_red.png</href>\n</Icon>\n</IconStyle>\n</Style>\n'
    kml+= '<StyleMap id=\"exampleStyleMap\">\n<Pair>\n<key>normal</key>\n<styleUrl>#normalPlacemark</styleUrl>\n</Pair>\n<Pair>\n<key>highlight</key>\n<styleUrl>#highlightPlacemark</styleUrl>\n</Pair>\n</StyleMap>\n<Style id=\"POS_normalPlacemark\">\n<IconStyle>\n<Icon>\n<href>http://pmarneffei.multilocus.net/earth/POS_off.png</href>\n</Icon>\n</IconStyle>\n</Style>\n<Style id=\"POS_highlightPlacemark\">\n<IconStyle>\n<Icon>\n<href>http://pmarneffei.multilocus.net/earth/POS_on.png</href>\n</Icon>\n</IconStyle>\n</Style>\n<StyleMap id=\"POS_exampleStyleMap\">\n<Pair>\n<key>normal</key>\n<styleUrl>#POS_normalPlacemark</styleUrl>\n</Pair>\n<Pair>\n<key>highlight</key>\n<styleUrl>#POS_highlightPlacemark</styleUrl>\n</Pair>\n</StyleMap>\n'
    kml+= '<name>EpiCollect</name>\n<Folder>\n<name>EpiCollect Sites</name>\n<visibility>1</visibility>\n'

    for entry in entries:
      if entry.location.lat == 0 and entry.location.lon == 0:
          continue
        
      kml+='<Placemark>\n<styleUrl>#exampleStyleMap</styleUrl>\n'

      if entry.hasPhoto():
        if entry.is_saved():
          kml+='<description><![CDATA[<p><img src="'+entry.getImageUrlPath(hostUrl)+'" width="300" height="250" />'
        else:
          kml+='<description><![CDATA[<p><img src="'+str(entry.photoPath)+'" width="300" height="250" /></p>'
      else:
        kml+='<description><![CDATA['

      entryDict = {}
      i=0
      for fieldName in entry.fieldNames:
        lower=fieldName.lower()
        
        entryDict[lower]=entry.fieldValues[i]
        if not lower.startswith("ec"):
          kml+='<br/>'+fieldName+' - '+entry.fieldValues[i]
        elif lower=="ectimecreated":
          if entry.fieldValues[i] is None:
              seconds = 0
          else:
              seconds=float(entry.fieldValues[i])
          if seconds>1000000000000.0: # if we're dealing with milliseconds not seconds
            seconds=seconds/1000
          kml+='<br/>Time created - '+str(datetime.utcfromtimestamp(seconds))
        elif lower=="eclastedited":
          seconds=float(entry.fieldValues[i])
          if seconds>1000000000000.0: # if we're dealing with milliseconds not seconds
            seconds=seconds/1000
          kml+='<br/>Last edited - '+str(datetime.utcfromtimestamp(seconds))
        i+=1

      entryDict["ectimecreated"] = str(entry.timeCreated)
      entryDict["eclatitude"] = str(entry.location.lat)
      entryDict["eclongitude"] = str(entry.location.lon)

      i=0
      for fieldName in entry.longFieldNames:
        kml+=fieldName+' - '+entry.fieldValues[i]+'<br/>'
        i+=1
      
      #NB clean this up
      #should probably be getting title from the form directly, not the formhandler
      #should consistently be returning/using either "ectimecreated" or "time" as defaults.
      
      title = formHandler.getTitle(form).lower()
   
      if title == "time": #NB: clean this up
        title = "ectimecreated"
        
      kml+=']]></description>\n'
      kml+='<name>'+entryDict[title]
      
      kml+='</name>\n'
      kml+='<Point>\n<coordinates>'+entryDict["eclongitude"]+','+entryDict["eclatitude"]+'</coordinates>\n</Point>\n'
      kml+='</Placemark>\n'

    kml+="</Folder>\n</Document>\n</kml>"
    return kml


  def getSavedEntriesXML(self, hostUrl, enterpriseName, projectName):
    entries = self.getSavedEntries(enterpriseName, projectName)
    xml ="<entries>"
    for entry in entries:
      xml+="<entry>"

      i=0
      for name in entry.fieldNames:
        xml+="<"+name.replace(' ', '_')+">"
        if name.lower()=="ecphotopath":
          xml+=entry.getImageUrlPath(hostUrl)
        else:
          xml+=entry.fieldValues[i]
        xml+="</"+name.replace(' ', '_')+">"
        i+=1

      i=0
      for name in entry.longFieldNames:
        xml+="<"+name.replace(' ', '_')+">"+entry.longFieldValues[i]+"</"+name.replace(' ', '_')+">"
        i+=1

      xml+="</entry>\n"
    xml+="</entries>"
    return xml

  def getSavedEntries(self, enterpriseName, projectName, number=1000, offset=0):

    query = Entry.all()

#    if enterpriseName is not None and len(enterpriseName)>0:
#      query.filter("enterpriseName =", enterpriseName)

    if projectName is None or len(projectName)==0:
      return [] #otherwise we might return every entry in the DB, which would be bad
    else:
      query.filter("projectName =", projectName)

    query.order("-timeCreated")
    results=query.fetch(number, offset)

    entries=[]
    entries.extend(results)

    #page entries for >1000 data points
    while len(results)==1000:
      earliestDate = results[999].timeCreated
      query.filter("timeCreated <", earliestDate)
      results=query.fetch(1000)
      entries.extend(results)

    return entries

  #Generates test entries.
  #Does not save them to the database: that's up to the caller.
  def generateTestEntriesFor(self, form, entryCount=50):
    i=0
    entries=[]
    formHandler=FormHandler()
    formFields=formHandler.getFields(form)
    chartables, markerField = formHandler.getChartables(form)

    testDeviceID="testEntriesFor-"+form.name+"-"+str(form.versionNumber)
    existing = db.GqlQuery("SELECT * FROM Entry WHERE deviceID = :1",testDeviceID).fetch(1000)
    entriesToGenerate = entryCount-len(existing)

    while i<entriesToGenerate:
      now = time.time()+100*random.random()
      edited = time.time()+100+100*random.random()
      new = Entry()
      new.timeCreated=datetime.fromtimestamp(now)
      new.entryID="testEntry32F12A85-BE9E-45F1-8B8C-818FD4CEA8BE-241-0000001C45863359"+str(i)
      new.deviceID=testDeviceID
      new.enterpriseName="ecTest-"+form.name
      if form.project is None:
        new.projectName="form test "+form.name;
      else:
        new.projectName=form.project.name;
      new.altitude=random.random()*1000;
      lat = 51.5+random.random()-0.5
      long = 0.0+random.random()-0.5
      new.location=db.GeoPt(lat,long)
      if i%2==0:
        new.userEmail="test@example.com"
      else:
        new.userEmail="test2@example.com"
      new.fieldNames = ["ecTimeCreated", "ecLastEdited", "ecEntryID", "ecDeviceID", "ecEnterpriseName", "ecProjectName", "ecAltitude", "ecLatitude", "ecLongitude", "ecUserEmail", "ecPhotoPath"]
      new.fieldNames.extend(formFields)
      new.fieldValues = [str(now), str(edited), new.entryID, new.deviceID, new.enterpriseName, new.projectName, str(new.altitude), str(new.location.lat), str(new.location.lon), new.userEmail, "http://epicollectserver.appspot.com/showImageWithKey?imageKey=ahBlcGljb2xsZWN0c2VydmVycg0LEgVFbnRyeRijhwgM"]
      for field in formFields:
        isChartable=False
        for chartable in chartables:
          if chartable["name"]==field:
            isChartable=True
            options=chartable["options"]
            if len(options)>0:
              rand = int(random.random()*len(options))
              new.fieldValues.append(options[rand]["value"])
            else:
              new.fieldValues.append(str(int(random.random()*20)-10))

        if not isChartable:
          new.fieldValues.append("Test "+field+" "+str(i))
        #TODO: handle selects, at least those in the form's chartables, differently

      entries.append(new)
      i+=1
    
    return entries

  # the price we pay for flexibility...
  def getTitleStringFor(self, entry):
    projects = db.GqlQuery("Select * FROM Project WHERE name = :1", entry.projectName).fetch(1)
    if len(projects)==0:
      return str(entry.timeCreated)

    form = projects[0].getLatestForm()
    if form is None:
      return str(entry.timeCreated)
    
    formHandler=FormHandler()

    try:
      titleField=formHandler.getTitle(form)
      if titleField is None:
        return str(entry.timeCreated)
        
      title = entry.getKVDict()[titleField]
      if title is None:
        return str(entry.timeCreated)

      return title
  
#      subTitleField=formHandler.getSubtitle(form)
#      subTitle = entry.getKVDict()[subTitleField]
#  
#      if subTitle is None:
#        return title
#      else:
#        return title +" ("+subTitle+")"
    except Exception, reason:
      logging.warning("Error generating title string for entry: "+str(reason))
      return str(entry.timeCreated)


class FormHandler:

  def getFormFor(self, formKey, formName, formVersion, projectKey, projectName):
    form=None

    if formKey!=None and len(formKey.strip())>0:
      return db.get(formKey)

    elif formName!=None and formVersion!=None and len(formName.strip())>0 and len(formVersion.strip())>0:
      forms = db.GqlQuery("SELECT * FROM Form WHERE name = :1 AND versionNumber = :2", formName.strip(), formVersion.strip()).fetch(1)
      if len(forms)>0:
        return forms[0]

    elif projectKey!=None and len(projectKey.strip())>0:
      project = db.get(projectKey)
      if project==None:
        return None
      return project.getLatestForm()

    elif projectName!=None and len(projectName.strip())>0:
      projects = db.GqlQuery("SELECT * FROM Project WHERE name = :1",projectName.strip()).fetch(1)
      if len(projects)>0:
        return projects[0].getLatestForm()

    return None

  def getFormXML(self, formKey, formName, formVersion, projectKey, projectName):
    form=self.getFormFor(formKey, formName, formVersion, projectKey, projectName)
    if form==None:
      return 'No form found for inputs: form key '+str(formKey)+", form name "+str(formName)+" and version "+str(formVersion)+", project key "+str(projectKey)+", project name "+str(projectName)
    else:
      return form.getXformXML()
    

  #Returns the error message, or None if there's no problem
  def validateNameAndVersion(self, form, name, version):
    name=name.strip()
    if name==None or len(name)==0:
        return "You must enter a name for the form."

    version=version.strip()
    if version==None or len(version)==0:
        return "You must enter a version number for the form."

    existing = db.GqlQuery("SELECT * FROM Form WHERE name = :1 AND versionNumber = :2", name, version).fetch(1)
    if len(existing)>0:
      if form==None and version!="1.0":
        return "Sorry, this form name is already in use. Please use a new one."
      return "Sorry, this combination of form name and version number is already in use. Please choose a new one."

    return None

  def validateXML(self, xml):
    try:
        parser = FormValidityParser()
        parser.clear()
        parser.feed(xml)
        parser.close()
    except HTMLParseError, reason:
        return "HTML Parse Error: "+str(reason)

    if not parser.hasAnInput:
        return "Invalid EpiCollect form - no inputs found."

    return None

  def saveXML(self, formXML, formName, version, formProject, allowDownloadEdits="false", sendEmail=False):
    newForm = Form()
    try:
        newForm.user = users.User()
    except users.UserNotFoundError:
        logging.warn("No user found for form "+str(formName))
    newForm.project = formProject
    newForm.name = formName.strip()
    newForm.xml = db.Text(formXML.strip().replace("\n",""))
    newForm.versionNumber = version.strip()
    newForm.allowDownloadEdits = (allowDownloadEdits=="true")
    newForm.put()
    logging.info("Saved form with xml "+str(newForm.xml))

    return newForm
 
  def getTitle(self, form):
    xml = form.xml
    nFlag = xml.find(' title="true"')
    if nFlag==-1:
      return "time"
    return self.getFieldNameFor(xml,nFlag)

  def getSubtitle(self, form):
    xml = form.xml
    nFlag = xml.find(' subtitle="true"')
    if nFlag==-1:
      return "time"
    return self.getFieldNameFor(xml,nFlag)
  
  def getFullFields(self,form):
    fields = []
    xml = parseString("<form>" + form.xml + "</form>")
    for node in xml.childNodes:
      for nd in node.childNodes:
        curfield = {"type":nd.nodeName, "name":nd.getAttribute('ref'), "label":nd.getElementsByTagName('label')[0].firstChild.data, "options":[], "title":nd.getAttribute('title') if nd.getAttribute('title') else 'false', "required": nd.getAttribute('required') if nd.getAttribute('required')else 'false', "numeric":nd.getAttribute('numeric')if nd.getAttribute('numeric') else 'false', "chart":nd.getAttribute('chart')if nd.getAttribute('chart')else 'false' }
        for ele in nd.getElementsByTagName('item'):
          curfield["options"].append({"label" : ele.getElementsByTagName('label')[0].firstChild.data if ele.getElementsByTagName('label')[0].firstChild else ele.getElementsByTagName('value')[0].firstChild.data, "value" : ele.getElementsByTagName('value')[0].firstChild.data if ele.getElementsByTagName('value')[0].firstChild else ''})
        fields.append(curfield)
        
    return fields
  
  def getFields(self, form):
    fields = []
    
    xml = form.xml
    nFlag = xml.find(' ref=')
    while nFlag>0:
      nLeft=xml.find('"',nFlag)
      nRight=xml.find('"',nLeft+1)
      fieldName = xml[nLeft+1:nRight]
      fields.append(fieldName)
      nFlag = xml.find(' ref=',nFlag+5)

    return fields

  def getChartables(self,form):
    chartables=[]
    
    xml = form.xml
    nFlag = xml.find(' chart=')
    while nFlag>0:
      fieldStart=xml.rfind("<",0,nFlag)

      parser = ChartableFieldParser()
      parser.clear()
      parser.feed(xml[fieldStart:])
      parser.close()
      
      chartable = {}
      chartable["name"] = parser.fieldName
      chartable["label"] = parser.label
      chartable["type"] = parser.type
      chartable["graphType"] = parser.graphType
      chartable["options"] = parser.options
      chartables.append(chartable)

      nFlag = xml.find(' chart=',nFlag+10)

    markerField={}
    for chartable in chartables:
      if chartable["type"]=="select":
        markerField=chartable
        break

    return chartables, markerField

  #utility method
  def getFieldNameFor(self, xml, nFlag):
    nName = xml.rfind(" ref=",0,nFlag)
    nLeft=xml.find('"',nName)
    nRight=xml.find('"',nLeft+1)
    name = xml[nLeft+1:nRight]
    return name

  def getTestForm(self):
    formxml = "<input ref=\"user\" required=\"true\"> <label>User</label> </input>\n"
    formxml+= "<input ref=\"thoughts\"> <label>Thoughts</label> </input>\n"
    formxml+= "<select ref=\"environment\" chart=\"pie\"> <label>Surroundings</label> <item><label>Treees</label><value>arboreal</value></item> <item><label>Water</label><value>aquatic</value></item> <item><label>Rocks</label><value>geologic</value></item> </select>\n"
    formxml+= "<input ref=\"species\" required=\"true\" title=\"true\"> <label>Species</label> </input>\n"
    formxml+= "<select1 ref=\"status\" readonly=\"true\" chart=\"bar\"> <label>Status</label> <item><label>Alive</label><value>live</value></item> <item><label>Deceased</label><value>dead</value></item> </select1>\n"
    formxml+= "<input ref=\"ph\" chart=\"pie\" subtitle=\"true\"> <label>pH Level</label> </input>\n"
    formxml+= "<textarea ref=\"comments\"> <label>Comments</label> </textarea>\n"

    newForm = Form()
    newForm.name="ecTest"
    newForm.versionNumber="0.1"
#    newForm.xml=db.Text(formxml.strip().replace("\n",""))
    newForm.xml=db.Text(formxml.strip())
    return newForm
    
#Expandable later.
class ChartableFieldParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)

    def clear(self):
        self.currentData=""
        self.finished=False
        self.inItem=False
        self.tagName=None
        self.fieldName=""
        self.label=""
        self.type=""
        self.graphType=""
        self.options=[]
        self.currentOption={}

    def handle_starttag(self, tag, attrs):
      if not self.finished:
        if self.tagName==None:
          self.tagName=tag
          if self.tagName.lower().startswith("select"):
            self.type="select"
          else:
            self.type="compare"
          for attr in attrs:
            if attr[0]=="ref":
              self.fieldName=attr[1]
            elif attr[0]=="chart":
              self.graphType=attr[1]
        elif tag.lower()=="item":
          self.inItem=True

    def handle_data(self, text):
      self.currentData+=text

    def handle_endtag(self, tag):
      if tag==self.tagName:
        self.finished=True

      if not self.finished:
        if tag.lower()=="label" and not self.inItem:
          self.label=self.currentData.strip()
        elif tag.lower()=="item":
          self.inItem=False
          self.options.append(self.currentOption)
          self.currentOption={}
        elif self.inItem:
          if tag.lower()=="label":
            self.currentOption["label"]=self.currentData.strip()
          elif tag.lower()=="value":
            self.currentOption["value"]=self.currentData.strip()

      self.currentData=""


#Expandable later.
class FormValidityParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.hasAnInput=False

    def clear(self):
        self.hasAnInput=False

    def handle_starttag(self, tag, attrs):
        lower=tag.lower()
        if lower=='input' or lower=='select' or lower=='select1' or lower=='textarea':
            self.hasAnInput=True

    def handle_data(self, text):
        pass

    def handle_endtag(self, tag):
        pass

