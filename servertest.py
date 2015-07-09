# coding: utf-8

import logging
import random
import time
import traceback
import urllib

from google.appengine.api import urlfetch
from google.appengine.ext import db

import ec

class ECServerTester:

    def runServerTest(self):
        self.setUp()
        message = "Test failed"
        try:
            self.testProjectNaming()
            self.testProjectData()
        except ECException, reason:
            logging.warning("Server test failed - "+str(reason))
            message = "Test failed: "+str(reason)
        else:
            message = "Test succeeded"
        self.tearDown()
        return message

    def runLoadTest(self):
        self.setUp()
        message = "Test failed"
        try:
            self.testLoad(20, doImageUpload=False)
        except ECException, reason:
            logging.warning("Server test failed - "+str(reason))
            message = "Test failed: "+str(reason)
        except Exception, reason:
            logging.warning("Server test error - "+str(reason))
            message = "Test error: "+str(reason)
        else:
            message = "Test succeeded"
        self.tearDown()
        return message

    def setUp(self):
        logging.info("Setting up server test")

        q = db.GqlQuery("SELECT __key__ FROM Entry WHERE enterpriseName = :1", "ecServerTest")
        results = q.fetch(1000)
        db.delete(results)

        q = db.GqlQuery("SELECT __key__ FROM Project WHERE name >= :1 AND name < :2", "ecServerTest", u"ecServerTest" + u"\ufffd")
        results = q.fetch(1)
        db.delete(results)

    def tearDown(self):

        q = db.GqlQuery("SELECT __key__ FROM Entry WHERE enterpriseName = :1", "ecServerTest")
        results = q.fetch(1000)
        db.delete(results)

        q = db.GqlQuery("SELECT __key__ FROM Project WHERE name >= :1 AND name < :2", "ecServerTest", u"ecServerTest" + u"\ufffd")
        results = q.fetch(1)
        db.delete(results)
        logging.info("Deleted temporary server-test data")


    def testProjectNaming(self):
        #try to create two projects with the same name
        logging.info("Trying to create two projects with the same name")
        url=self.getUrlRoot()+"createProject"
        form_fields={"projectName" : "ecServerTestProjectAlpha"}
        self.doPost(url,form_fields)
        self.doPost(url,form_fields)
        self.assertEquals(1, ec.Project.all().filter('name =', 'ecServerTestProjectAlpha').count())
        db.delete(ec.Project.all().filter('name =', 'ecServerTestProjectAlpha').get())

        #create a project with a complex name - spaces, underscores, ampersands, etc.
        logging.info("Trying to create a project with a complex name")
        url=self.getUrlRoot()+"createProject"
        form_fields={"projectName" : "ecServerTest-Hodder+Stoughton"}
        self.doPost(url,form_fields)
        self.assertEquals(1, ec.Project.all().filter('name =', 'ecServerTest-Hodder+Stoughton').count())
        db.delete(ec.Project.all().filter('name =', 'ecServerTest-Hodder+Stoughton').get())
        
        #try to create a project with a non-ASCII name
        #create a project with a complex name - spaces, underscores, ampersands, etc.
        logging.info("Trying to create a project with a non-ASCII name")
        url=self.getUrlRoot()+"createProject"
        form_fields={"projectName" : "ecServerTestMontréal"}
        self.doPost(url,form_fields)
        self.assertEquals(0, ec.Project.all().filter('name =', u'ecServerTestMontréal').count())

    def testProjectData(self):

        #ensure there's no existing polluting data
        q = db.GqlQuery("SELECT * FROM Entry WHERE enterpriseName = :1", "ecServerTest")
        results = q.fetch(1)
        self.assertEquals(0, len(results))

        #upload multiple data points from multiple devices for Project I, Form A
        #upload multiple data points from multiple devices for Project II, Form B
        #at least one case of a single device uploading to multiple projects
        time0=str(time.time())
        self.uploadEntry("ID"+str(time0), time0, "testDevice1", "ecServerTestProjectI", "tester1@tester.com", ["formAkey1","formAkey2"], ["formAvalue1","formAvalue2"])
        time1=str(time.time())
        self.uploadEntry("ID"+str(time1), time1, "testDevice1", "ecServerTestProjectI", "tester1@tester.com", ["formAkey1","formAkey2"], ["formAvalue1","formAvalue2"])
        time2=str(time.time())
        self.uploadEntry("ID"+str(time2), time2, "testDevice1", "ecServerTestProjectI", "tester2@tester.com", ["formAkey1","formAkey2"], ["formAvalue3","formAvalue4"])
        time3=str(time.time())
        self.uploadEntry("ID"+str(time3), time3, "testDevice1", "ecServerTestProjectI", "tester1@tester.com", ["formAkey1","formAkey2"], ["formAvalue5","formAvalue6"])
        time4=str(time.time())
        self.uploadEntry("ID"+str(time4), time4, "testDevice2", "ecServerTestProjectI", "tester1@tester.com", ["formAkey1","formAkey2"], ["formAvalue7","formAvalue8"])
        time5=str(time.time())
        self.uploadEntry("ID"+str(time5), time5, "testDevice1", "ecServerTestProjectII", "tester1@tester.com", ["formBkey1","formBkey2"], ["formBvalue1","formBvalue2"])
        time6=str(time.time())
        self.uploadEntry("ID"+str(time6), time6, "testDevice1", "ecServerTestProjectII", "tester2@tester.com", ["formBkey1","formBkey2"], ["formBvalue3","formBvalue4"])
        time7=str(time.time())
        self.uploadEntry("ID"+str(time7), time7, "testDevice2", "ecServerTestProjectII", "tester1@tester.com", ["formBkey1","formBkey2"], ["formBvalue5","formBvalue6"])
        time8=str(time.time())
        self.uploadEntry("ID"+str(time8), time8, "testDevice2", "ecServerTestProjectII", "tester2@tester.com", ["formBkey1","formBkey2"], ["formBvalue7","formBvalue8"])
        time9=str(time.time())
        self.uploadEntry("ID"+str(time9), time9, "testDevice2", "ecServerTestProjectII", "tester1@tester.com", ["formAkey1","formAkey2"], ["formAvalue9","formAvalue10"])
        uploadsFinished=time.time()

        q = db.GqlQuery("SELECT * FROM Entry WHERE enterpriseName = :1", "ecServerTest")
        results = q.fetch(1000)
        #ensure all entries were captured
        self.assertEquals(10, len(results))

        proj1count=0
        proj2count=0
        dev1count=0
        dev2count=0
        tester1count=0
        tester2count=0
        timestamps = [time0,time1,time2,time3,time4,time5,time6,time7,time8,time9]
        for result in results:
            #ensure entryIDs unique
            q2= db.GqlQuery("SELECT * FROM Entry WHERE entryID = :1", result.entryID)
            r2 = q2.fetch(2)
            self.assertTrue(len(r2)==1)

            #ensure entryIDs captured correctly
            self.assertTrue(result.entryID in ["ID"+str(time0),"ID"+str(time1),"ID"+str(time2),"ID"+str(time3),"ID"+str(time4),"ID"+str(time5),"ID"+str(time6),"ID"+str(time7),"ID"+str(time8),"ID"+str(time9)])

            #ensure timestamps captured correctly
            #sometimes they're off by a second between BigTable or wherever, but that's OK.
            resultTime = result.timeCreated
            resultTimestamp = time.mktime(resultTime.timetuple())
            j=0
            while j<len(timestamps):
                if abs(float(timestamps[j])-resultTimestamp)<=1.0:
                    break
                j+=1
            self.assertTrue(j<10)
            
            if result.projectName=="ecServerTestProjectI":
                proj1count+=1
            if result.projectName=="ecServerTestProjectII":
                proj2count+=1
            if result.deviceID=="testDevice1":
                dev1count+=1
            if result.deviceID=="testDevice2":
                dev2count+=1
            if result.userEmail=="tester1@tester.com":
                tester1count+=1
            if result.userEmail=="tester2@tester.com":
                tester2count+=1

            #ensure form data is being stored
            pass
        
        #ensure there's no crosstalk between the projects
        self.assertEquals(5, proj1count)
        self.assertEquals(5, proj2count)
        #ensure that we have separated device IDs correctly
        self.assertEquals(6, dev1count)
        self.assertEquals(4, dev2count)

        #ensure emails are being stored
        self.assertEquals(7, tester1count)
        self.assertEquals(3, tester2count)

        time.sleep(2)

        #edit a few entries
        #ensure that they're being overwritten, not saved again
        self.uploadEntry("ID"+str(time1), time1, "testDevice1", "ecServerTestProjectI", "tester1@tester.com", ["formAkey1","formAkey2"], ["formAvalue11","formAvalue12"])
        q2 = db.GqlQuery("SELECT * FROM Entry WHERE entryID = :1", "ID"+str(time1))
        r2 = q2.fetch(2)
        self.assertEquals(1, len(r2))
        self.assertTrue("formAvalue11" in r2[0].fieldValues)
        self.assertTrue("formAvalue12" in r2[0].fieldValues)
        lastEdited = time.mktime(r2[0].lastEdited.timetuple())
        self.assertTrue(lastEdited > uploadsFinished)

        self.uploadEntry("ID"+str(time8), time8, "testDevice2", "ecServerTestProjectII", "tester2@tester.com", ["formBkey1","formBkey2"], ["formBvalue9","formBvalue10"])
        q2 = db.GqlQuery("SELECT * FROM Entry WHERE entryID = :1", "ID"+str(time8))
        r2 = q2.fetch(2)
        self.assertEquals(1, len(r2))
        self.assertTrue("formBvalue9" in r2[0].fieldValues)
        self.assertTrue("formBvalue10" in r2[0].fieldValues)
        lastEdited = time.mktime(r2[0].lastEdited.timetuple())
        self.assertTrue(lastEdited > uploadsFinished)
        
        #upload an entry with a form value that includes newlines
        #ensure that it is stored correctly
        time10=str(time.time())
        newlines="""
        Now is the time for all good men to come to the aid of their country.
        
        The quick brown fox jumped over the lazy dog.
        """
        self.uploadEntry("ID"+str(time10), time10, "testDevice2", "ecServerTestProjectII", "tester1@tester.com", ["formAkey1","formAkey2"], ["formAvalue9",newlines])
        q2 = db.GqlQuery("SELECT * FROM Entry WHERE entryID = :1", "ID"+str(time10))
        r2 = q2.fetch(2)
        self.assertEquals(1, len(r2))
        logging.info("newlines is "+newlines+", fieldValues are "+str(r2[0].fieldValues))
        self.assertTrue(newlines in r2[0].fieldValues)
        
        #upload non-ASCII data
        #ensure it's being correctly saved
        time11=str(time.time())
        self.uploadEntry("ID"+str(time11), time11, "testDevice2", "ecServerTestProjectII", "tester1@tester.com", ["formAkey1","formAkey2"], ["formAvalue9","Montréal"])
        q2 = db.GqlQuery("SELECT * FROM Entry WHERE entryID = :1", "ID"+str(time11))
        r2 = q2.fetch(2)
        self.assertEquals(1, len(r2))
        self.assertTrue(u"Montréal" in r2[0].fieldValues)
        
        #upload an entry with a form value that includes several paragraphs of text
        #ensure that it is stored correctly
        time15=str(time.time())
        longText="""
        Now is the time for all good men to come to the aid of their country.
        
        The quick brown fox jumped over the lazy dog.
        
        Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
        """
        self.uploadEntry("ID"+str(time15), time15, "testDevice2", "ecServerTestProjectII", "tester1@tester.com", ["formAkey1","formAkey2", "formAkey3"], ["formAvalue9", longText, "formAvalue10"])
        q2 = db.GqlQuery("SELECT * FROM Entry WHERE entryID = :1", "ID"+str(time15))
        r2 = q2.fetch(2)
        self.assertEquals(1, len(r2))
        self.assertTrue("formAvalue9" in r2[0].fieldValues)
        self.assertTrue("formAvalue10" in r2[0].fieldValues)
        self.assertTrue(longText in r2[0].longFieldValues)

        #upload small image
        #ensure it's correctly recorded
        time12=str(time.time())
        self.uploadEntry("ID"+str(time12), time12, "testDevice2", "ecServerTestProjectII", "tester1@tester.com", ["formAkey1","formAkey2"], ["formAvalue9","formAvalue10"], "image"+time12)
        imageURL="http://farm3.static.flickr.com/2439/3568503317_0c69e929ab_b.jpg"
        self.saveImage("image"+time12, imageURL)
        q2 = db.GqlQuery("SELECT * FROM Entry WHERE entryID = :1", "ID"+str(time12))
        r2 = q2.fetch(2)
        self.assertEquals(1, len(r2))
        self.assertFalse(r2[0].photoPath is None)
        self.assertFalse(r2[0].photoPath =="None")
        self.assertFalse(r2[0].image is None)
        #TODO: check image details

    def testLoad(self, maxHits, doImageUpload=False):
        upUrl=self.getUrlRoot()+"uploadToServer"
        ids=[]
        rpcs=[]
        i=0
        while i<maxHits:
            id = "LoadTest"+str(i)+"-"+str(time.time())
            form_fields = {
                "ecEntryID" : id,
                "ecTimeCreated" : str(time.time()),
                "ecLastEdited" : str(time.time()),
                "ecDeviceID" : "testDevice1",
                "ecEnterpriseName" : "ecServerTest",
                "ecAppName" : "ecServerLoadTest",
                "ecUserEmail" : "tester1@tester1.com",
                "ecPhotoPath" : "None",
                "ecAltitude" : str(1000*random.random()),
                "ecLatitude" : str(360*(random.random()-0.5)),
                "ecLongitude" : str(360*(random.random()-0.5)),
                "formAkey1" : "formAvalue1",
                "formAkey2" : "formAvalue2",
            }
            ids.append(id)
            rpcs.append(urlfetch.create_rpc())
            urlfetch.make_fetch_call(rpc=rpcs[i],
                                     url=upUrl,
                                     method=urlfetch.POST,
                                     payload=urllib.urlencode(form_fields),
                                     headers={'Content-Type': 'application/x-www-form-urlencoded'})
            i+=1

        if doImageUpload:
            imageURL="http://farm3.static.flickr.com/2439/3568503317_0c69e929ab_b.jpg"
            imageResponse = urlfetch.fetch(imageURL)
            image=imageResponse.content
            entryHandler = ec.EntryHandler()

        j=0
        for rpc in rpcs:
            rpc.check_success()
            if doImageUpload:
                result = entryHandler.saveImage(ids[j], image)
                self.assertTrue(result.startswith("Success"))
                j+=1

    def uploadEntry(self, id, timestamp, deviceID, projectName, userEmail, formKeys, formValues, photoPath=None):
        #assemble data
        form_fields = {
            "ecEntryID" : id,
            "ecTimeCreated" : timestamp,
            "ecLastEdited" : str(time.time()),
            "ecDeviceID" : deviceID,
            "ecEnterpriseName" : "ecServerTest",
            "ecAppName" : projectName,
            "ecUserEmail" : userEmail,
            "ecPhotoPath" : photoPath,
            "ecAltitude" : str(1000*random.random()),
            "ecLatitude" : str(360*(random.random()-0.5)),
            "ecLongitude" : str(360*(random.random()-0.5)),
        }
        
        i=0
        while i < len(formKeys):
            form_fields[formKeys[i]]=formValues[i]
            i+=1

        #prepare and upload data
        url=self.getUrlRoot()+"uploadToServer"
        self.doPost(url,form_fields)
        
    def saveImage(self, imageID, imageURL):
        #fetch image
        imageResponse = urlfetch.fetch(imageURL)
        image=imageResponse.content
        logging.info("Image ID: "+imageID+" size: "+str(len(image)))
        
        #save it
        entryHandler = ec.EntryHandler()
        result = entryHandler.saveImage(imageID, image)
        self.assertTrue(result.startswith("Success"))
    
    def doPost(self, url, form_fields):
        form_data = urllib.urlencode(form_fields)
        result = urlfetch.fetch(url=url,
                                payload=form_data,
                                method=urlfetch.POST,
                                headers={'Content-Type': 'application/x-www-form-urlencoded'})
        self.assertEquals(200, result.status_code)
        return result
        
    def assertEquals(self, a, b):
        if a==b:
            pass
        else:
            self.doRaise("AssertEquals failed: "+str(a)+" != "+str(b))
    
    def assertFalse(self, test):
        if test is not False:
            self.doRaise("AssertFalse failed")
    
    def assertTrue(self, test):
        if test is not True:
            self.doRaise("AssertTrue failed")

    def doRaise(self,reason):
        message=''
        for line in traceback.format_stack(limit=5):
            message+=line+"<BR/>"
        raise ECException(reason+"\n<BR/>"+message)

    def getUrlRoot(self):
#        return "http://127.0.0.1:8081/"
        return "http://epicollectserver.appspot.com/"

class ECException(Exception):
    pass