# coding: utf-8

import unittest
import logging
import random
import time
import urllib
from datetime import datetime

from google.appengine.api import urlfetch
from google.appengine.ext import db

import ec

# form tests:
# parse form with all options, generate HTML with all options

class testTest(unittest.TestCase):
    # paranoia
    def testDeletion(self):
        testProject = ec.Project(name="ecUnitTest")
        testProject.put()
        testProject = ec.Project(name="tempTestProject")
        testProject.put()
        q = db.GqlQuery("SELECT __key__ FROM Project WHERE name >= :1 AND name < :2", "ecUnitTest", u"ecUnitTest" + u"\ufffd")
        results = q.fetch(1)
        db.delete(results)
        q = db.GqlQuery("SELECT __key__ FROM Project WHERE name = :1", "tempTestProject")
        results = q.fetch(1)
        self.assertTrue(len(results)==1)
        db.delete(results)
        
class testForms(unittest.TestCase):
    def setUp(self):
        testProject = ec.Project(name="ecUnitTest")
        testProject.put()

    def testGarbageXML(self):
        formHandler=ec.FormHandler()
        error = formHandler.validateXML("garbage data")
        self.assertTrue(len(error)>0)

    def testBadXML(self):
        formHandler=ec.FormHandler()
        error = formHandler.validateXML("<input ref='test adslfjd></inputt>")
        self.assertTrue(len(error)>0)

    def testRepeatedNameVersion(self):
        formHandler=ec.FormHandler()
        newForm = formHandler.saveXML("<input ref='test'/>", "ecUnitTest1", "1.0", None)
        self.assertTrue(newForm is not None)
        error = formHandler.validateNameAndVersion(newForm, "ecUnitTest1", "1.0")
        self.assertTrue(len(error)>0)
        error = formHandler.validateNameAndVersion(newForm, "ecUnitTest2", "1.0")
        self.assertTrue(error is None)
        error = formHandler.validateNameAndVersion(newForm, "ecUnitTest1", "1.1")
        self.assertTrue(error is None)

    def testValidation(self):
        #generate HTML
        formData = "<input ref=\"subtitle\" subtitle=\"true\"> <label>Sub-Title</label> </input>\n"
        formData+= "<input ref=\"user\" required=\"true\" title=\"true\"> <label>User</label> </input>\n"
        formData+= "<select ref=\"environment\"> <label>Surroundings</label> <item><label>Treees</label><value>arboreal</value></item> <item><label>Water</label><value>aquatic</value></item> <item><label>Rocks</label><value>geologic</value></item> </select>\n"
        formData+= "<input ref=\"species\" required=\"true\" chart=\"true\"> <label>Species</label> </input>\n"
        formData+= "<select1 ref=\"status\" readonly=\"true\" chart=\"true\"> <label>Status</label> <item><label>Alive</label><value>live</value></item> <item><label>Deceased</label><value>dead</value></item> <item><label>Unknown</label><value>indeterminate</value></item> </select1>\n"
        formData+= "<input ref=\"ph\" chart=\"true\"> <label>pH Level</label> </input>\n"
        formData+= "<textarea ref=\"comments\"> <label>Comments</label> </textarea>\n"
        projects = db.GqlQuery("SELECT * FROM Project WHERE name = :1","ecUnitTest").fetch(1)
        testProject = projects[0]
        formHandler=ec.FormHandler()
        
        #check parsing
        validationError = formHandler.validateXML(formData)
        self.assertEquals(validationError,None)

    
    def testGetFormXML(self):
        formData = "<input ref=\"subtitle\" subtitle=\"true\"> <label>Sub-Title</label> </input>\n"
        formData+= "<input ref=\"user\" required=\"true\" title=\"true\"> <label>User</label> </input>\n"
        formData+= "<select ref=\"environment\"> <label>Surroundings</label> <item><label>Treees</label><value>arboreal</value></item> <item><label>Water</label><value>aquatic</value></item> <item><label>Rocks</label><value>geologic</value></item> </select>\n"
        formData+= "<input ref=\"species\" required=\"true\" chart=\"true\"> <label>Species</label> </input>\n"
        formData+= "<select1 ref=\"status\" readonly=\"true\" chart=\"true\"> <label>Status</label> <item><label>Alive</label><value>live</value></item> <item><label>Deceased</label><value>dead</value></item> <item><label>Unknown</label><value>indeterminate</value></item> </select1>\n"
        formData+= "<input ref=\"ph\" chart=\"true\"> <label>pH Level</label> </input>\n"
        formData+= "<textarea ref=\"comments\"> <label>Comments</label> </textarea>\n"

        projects = db.GqlQuery("SELECT * FROM Project WHERE name = :1","ecUnitTest").fetch(1)
        testProject = projects[0]
        formHandler=ec.FormHandler()
        newForm = formHandler.saveXML(formData, "ecUnitTest3", "1.0", testProject)
        
        xml0 = formHandler.getFormXML(None, None, None, None, None)
        self.assertTrue(xml0.startswith("No form"))
        xml0 = formHandler.getFormXML(None, "ecUnitTestX", "1.0", None, None)
        self.assertTrue(xml0.startswith("No form"))
        xml0 = formHandler.getFormXML(None, "ecUnitTest3", "9.0", None, None)
        self.assertTrue(xml0.startswith("No form"))
        xml4 = formHandler.getFormXML(None, None, None, None, "ecUnitTestX")
        self.assertTrue(xml0.startswith("No form"))

        xml1 = formHandler.getFormXML(str(newForm.key()), None, None, None, None)
        xml2 = formHandler.getFormXML(None, "ecUnitTest3", "1.0", None, None)
        xml3 = formHandler.getFormXML(None, None, None, str(testProject.key()), None)
        xml4 = formHandler.getFormXML(None, None, None, None, "ecUnitTest")
        self.assertEqual(xml1,xml2)
        self.assertEqual(xml2,xml3)
        self.assertEqual(xml3,xml4)

        self.assertEqual(xml4, u"<xform> <model> <submission id=\"ecUnitTest3\" projectName=\"ecUnitTest\" allowDownloadEdits=\"false\" versionNumber=\"1.0\" /> </model>\n"+formData.replace("\n","")+"</xform>\n")

    def testFormMapAccessors(self):
        #generate HTML
        formHandler=ec.FormHandler()
        newForm = formHandler.getTestForm()

        self.assertEqual("species", formHandler.getTitle(newForm))
        self.assertEqual("ph", formHandler.getSubtitle(newForm))

        fields = formHandler.getFields(newForm)
        self.assertTrue("thoughts" in fields)
        self.assertTrue("user" in fields)
        self.assertTrue("environment" in fields)
        self.assertTrue("species" in fields)
        self.assertTrue("status" in fields)
        self.assertTrue("ph" in fields)
        self.assertTrue("comments" in fields)

        chartables, markerField = formHandler.getChartables(newForm)
        self.assertEqual(3, len(chartables))
        self.assertEqual(markerField["type"], "select")
        for chartable in chartables:
            if chartable["name"]=="environment":
                self.assertEquals("select",chartable["type"])
                options = chartable["options"]
                self.assertEquals(3, len(options))
                for option in options:
                    if option["value"]=="arboreal":
                        self.assertEquals(u"Treees", option["label"])
                    elif option["value"]=="geologic":
                        self.assertEquals(u"Rocks", option["label"])
                    elif option["value"]=="aquatic":
                        self.assertEquals(u"Water", option["label"])
                    else:
                        self.assertEquals("Invalid value", option["value"])
            elif chartable["name"]=="status":
                self.assertEquals("select",chartable["type"])
                options = chartable["options"]
                self.assertEquals(2, len(options))
                for option in options:
                    if option["value"]=="live":
                        self.assertEquals(u"Alive", option["label"])
                    elif option["value"]=="dead":
                        self.assertEquals(u"Deceased", option["label"])
                    else:
                        self.assertEquals("Invalid value", option["value"])
            elif chartable["name"]=="ph":
                self.assertEquals("pH Level", chartable["label"])
#TODO                self.assertEquals("compare", chartable["type"])            
            else:
                self.assertEquals("Invalid name", chartable["name"])

    def tearDown(self):
        #delete unit-test forms
        q = db.GqlQuery("SELECT __key__ FROM Form WHERE name >= :1 AND name < :2", "ecUnitTest", u"ecUnitTest" + u"\ufffd")
        results = q.fetch(10)
        db.delete(results)
        q = db.GqlQuery("SELECT __key__ FROM Project WHERE name >= :1 AND name < :2", "ecUnitTest", u"ecUnitTest" + u"\ufffd")
        results = q.fetch(10)
        db.delete(results)

# entry tests:
# move SaveEntries, GetSavedEntries into testable separate file
# test SaveEntries
# test GetSavedEntries
# test SaveImage?

class testEntries(unittest.TestCase):
    def setUp(self):
        p1 = ec.Project(name="ecUnitTestProject")
        p1.put()
        p2 = ec.Project(name="ecUnitTestProject2")
        p2.put()

    def testSave(self):
        now=time.time()
        tAV = {
            "ecTimeCreated" : str(now),
            "ecEntryID" : "ecUnitTest1",
            "ecDeviceID" : "ecUnitTestDevice",
            "ecEnterpriseName" : "ecUnitTestEnterprise",
            "ecAppName" : "ecUnitTestProject",
            "ecAltitude" : "1.0",
            "ecLatitude" : "54.0",
            "ecLongitude" : "0.0",
            "ecUserEmail" : "test@example.com",
            "ecPhotoPath" : "",
            "testField1" : "test Field 1",
            "testField2" : "test Field 2",
        }
        entryHandler = ec.EntryHandler()
        response=entryHandler.saveEntry(tAV)
        self.assertTrue(response.startswith("Success"))
        entries = db.GqlQuery("SELECT * FROM Entry WHERE entryID = :1","ecUnitTest1").fetch(1000)
        self.assertTrue(len(entries))==1
        saved=entries[0]
        self.assertTrue(len(saved.fieldNames)==12)
        self.assertTrue("testField1" in saved.fieldNames)
        self.assertTrue("testField2" in saved.fieldNames)
        self.assertTrue(len(saved.fieldValues)==12)
        self.assertTrue("test Field 1" in saved.fieldValues)
        self.assertTrue("test Field 2" in saved.fieldValues)
        
        self.assertAlmostEquals(saved.altitude,1.0)
        self.assertAlmostEquals(saved.location.lat,54.0)
        self.assertAlmostEquals(saved.location.lon,0.0)
        
        self.assertEquals(saved.userEmail, "test@example.com")
        self.assertEquals(saved.photoPath, "")
        self.assertEquals(saved.entryID, "ecUnitTest1")
        self.assertEquals(saved.deviceID, "ecUnitTestDevice")
        self.assertEquals(saved.projectName, "ecUnitTestProject")
# not currently really using enterprises
#        self.assertEquals(saved.enterpriseName, "ecUnitTestEnterprise")
#        self.assertAlmostEquals(saved.timeCreated,datetime.fromtimestamp(now))

    def testGet(self):
        entryHandler = ec.EntryHandler()
        now=time.time()
        tAV1 = {
            "ecTimeCreated" : str(now),
            "ecEntryID" : "ecUnitTest1",
            "ecDeviceID" : "ecUnitTestDevice",
            "ecEnterpriseName" : "ecUnitTestEnterprise",
            "ecAppName" : "ecUnitTestProject",
            "ecAltitude" : "1.0",
            "ecLatitude" : "54.0",
            "ecLongitude" : "0.0",
            "ecUserEmail" : "test@example.com",
            "ecPhotoPath" : "",
            "testField1" : "test Field 1",
            "testField2" : "test Field 2",
        }
        entryHandler.saveEntry(tAV1)
        now=time.time()
        tAV2 = {
            "ecTimeCreated" : str(now),
            "ecEntryID" : "ecUnitTest2",
            "ecDeviceID" : "ecUnitTestDevice",
            "ecEnterpriseName" : "ecUnitTestEnterprise",
            "ecAppName" : "ecUnitTestProject",
            "ecAltitude" : "2.0",
            "ecLatitude" : "55.0",
            "ecLongitude" : "-1.0",
            "ecUserEmail" : "test@example.com",
            "ecPhotoPath" : "",
            "testField3" : "test Field 3",
            "testField4" : "test Field 4",
        }
        entryHandler.saveEntry(tAV2)
        now=time.time()
        tAV3 = {
            "ecTimeCreated" : str(now),
            "ecEntryID" : "ecUnitTest3",
            "ecDeviceID" : "ecUnitTestDevice",
            "ecEnterpriseName" : "ecUnitTestEnterprise",
            "ecAppName" : "ecUnitTestProject2",
            "ecAltitude" : "3.0",
            "ecLatitude" : "56.0",
            "ecLongitude" : "-2.0",
            "ecUserEmail" : "test@example.com",
            "ecPhotoPath" : "",
            "testField5" : "test Field 5",
            "testField6" : "test Field 6",
        }
        entryHandler.saveEntry(tAV3)

# not really using enterprises       
#        entXML = entryHandler.getSavedEntriesXML("/unitTest", "ecUnitTestEnterprise",None)
#        logging.info("xml: "+entXML)
#        self.assertEqual(entXML.count("<entry>"),0)
        p1XML = entryHandler.getSavedEntriesXML("/unitTest", None, "ecUnitTestProject")
        self.assertEqual(p1XML.count("<entry>"),2)
        p2XML = entryHandler.getSavedEntriesXML("/unitTest", None, "ecUnitTestProject2")
        self.assertEqual(p2XML.count("<entry>"),1)
#        logging.info("xml is "+p2XML)
        
        #check a few values
        self.assertEquals(p1XML.count("test@example.com"),2)

#        self.assertNotEquals(entXML.find("<ecAltitude>3.0</ecAltitude"),-1)
        self.assertEquals(p1XML.find("<ecAltitude>3.0</ecAltitude"),-1)
        self.assertNotEquals(p2XML.find("<ecAltitude>3.0</ecAltitude"),-1)

#        self.assertNotEquals(entXML.find("<ecLongitude>-1.0</ecLongitude>"),-1)
        self.assertNotEquals(p1XML.find("<ecLongitude>-1.0</ecLongitude>"),-1)
        self.assertEquals(p2XML.find("<ecLongitude>-1.0</ecLongitude>"),-1)

#        self.assertNotEquals(entXML.find("<ecLatitude>54.0</ecLatitude>"),-1)
        self.assertNotEquals(p1XML.find("<ecLatitude>54.0</ecLatitude>"),-1)
        self.assertEquals(p2XML.find("<ecLatitude>54.0</ecLatitude>"),-1)

#        self.assertTrue(entXML.find("testField4")>entXML.find("testField6"))
        self.assertTrue(p1XML.find("testField1")>p1XML.find("testField3"))

    def testSaveImage(self):
        entryHandler = ec.EntryHandler()
        now=time.time()
        tAV1 = {
            "ecTimeCreated" : str(now),
            "ecEntryID" : "ecUnitTest1",
            "ecDeviceID" : "ecUnitTestDevice",
            "ecEnterpriseName" : "ecUnitTestEnterprise",
            "ecAppName" : "ecUnitTestProject",
            "ecAltitude" : "1.0",
            "ecLatitude" : "54.0",
            "ecLongitude" : "0.0",
            "ecUserEmail" : "test@example.com",
            "ecPhotoPath" : "unitTestImage.jpg",
            "testField1" : "test Field 1",
            "testField2" : "test Field 2",
        }
        entryHandler.saveEntry(tAV1)

        imageURL="http://farm1.static.flickr.com/44/117471023_46b910a4d1_m.jpg"
        result=urlfetch.fetch(imageURL)
        self.assertTrue(len(result.content)>0)
        entryHandler.saveImage("unitTestImage.jpg",result.content)
        
        entries = db.GqlQuery("SELECT * FROM Entry WHERE entryID = :1","ecUnitTest1").fetch(1000)
        self.assertTrue(len(entries))==1
        saved=entries[0]
        logging.info("key is "+str(saved.key()))
        self.assertEquals(result.content,saved.image)

    def testTestData(self):
        #check test map values
        formHandler=ec.FormHandler()
        newForm = formHandler.getTestForm()
        entryHandler = ec.EntryHandler()
        entries = entryHandler.generateTestEntriesFor(newForm,50)
        self.assertEquals(len(entries), 50)

    def tstPaging(self):
        i=0
        entryHandler=ec.EntryHandler()
        while i<25:
            now=time.time()
            tAV1 = {
                "ecTimeCreated" : str(now),
                "ecEntryID" : "ecUnitTest"+str(i),
                "ecDeviceID" : "ecUnitTestDevice",
                "ecEnterpriseName" : "ecUnitTestEnterprise",
                "ecAppName" : "ecUnitTestProject",
                "ecAltitude" : str(1.0+i/1000),
                "ecLatitude" : "54.0",
                "ecLongitude" : "0.0",
                "ecUserEmail" : "test@example.com",
                "ecPhotoPath" : "unitTestImage.jpg",
                "testField1" : "test Field 1 "+str(i),
                "testField2" : "test Field 2 "+str(i),
            }
            entryHandler.saveEntry(tAV1)
            i+=1
            logging.info("Saving test value "+str(i))
    
        fetchResults = db.GqlQuery("SELECT * FROM Entry").fetch(1000)
        self.assertEquals(25,len(fetchResults))

        entries1=entryHandler.getSavedEntries(None, "ecUnitTestProject")
        self.assertEquals(25,len(entries1))
    
        for entry in entries1:
            db.delete(entry.key())

        i=0
        while i<1250:
            now=time.time()
            tAV1 = {
                "ecTimeCreated" : str(now),
                "ecEntryID" : "ecUnitTest"+str(i),
                "ecDeviceID" : "ecUnitTestDevice",
                "ecEnterpriseName" : "ecUnitTestEnterprise",
                "ecAppName" : "ecUnitTestProject",
                "ecAltitude" : str(1.0+i/1000),
                "ecLatitude" : "54.0",
                "ecLongitude" : "0.0",
                "ecUserEmail" : "test@example.com",
                "ecPhotoPath" : "unitTestImage.jpg",
                "testField1" : "test Field 1 "+str(i),
                "testField2" : "test Field 2 "+str(i),
            }
            entryHandler.saveEntry(tAV1)
            i+=1
            logging.info("Saving test value "+str(i))
    
        entries2=entryHandler.getSavedEntries(None, "ecUnitTestProject")
        self.assertEquals(1250,len(entries2))
        for entry in entries2:
            db.delete(entry.key())
    
        i=0
        while i<2500:
            now=time.time()
            tAV1 = {
                "ecTimeCreated" : str(now),
                "ecEntryID" : "ecUnitTest"+str(i),
                "ecDeviceID" : "ecUnitTestDevice",
                "ecEnterpriseName" : "ecUnitTestEnterprise",
                "ecAppName" : "ecUnitTestProject",
                "ecAltitude" : str(1.0+i/1000),
                "ecLatitude" : "54.0",
                "ecLongitude" : "0.0",
                "ecUserEmail" : "test@example.com",
                "ecPhotoPath" : "unitTestImage.jpg",
                "testField1" : "test Field 1 "+str(i),
                "testField2" : "test Field 2 "+str(i),
            }
            entryHandler.saveEntry(tAV1)
            i+=1
            logging.info("Saving test value "+str(i))
    
        entries3=entryHandler.getSavedEntries(None, "ecUnitTestProject")
        self.assertEquals(2500,len(entries3))
    
        entries4=entryHandler.getSavedEntries("ecUnitTestEnterprise", "ecUnitTestProject")
        self.assertEquals(2500,len(entries4))
    
        for entry in entries4:
          db.delete(entry.key())
        
    def tearDown(self):
#        q = db.GqlQuery("SELECT __key__ FROM Entry WHERE enterpriseName = :1", "ecUnitTestEnterprise")
#        results = q.fetch(1000)
#        while len(results)==1000:
#            db.delete(results)
#            results=q.fetch(1000)

        q = db.GqlQuery("SELECT __key__ FROM Project WHERE name >= :1 AND name < :2", "ecUnitTest", u"ecUnitTest" + u"\ufffd")
        results = q.fetch(1000)
        db.delete(results)

if __name__ == '__main__':
    unittest.main()

