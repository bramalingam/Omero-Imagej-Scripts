import os
from os import path

from java.lang import Long
from java.lang import String
from java.lang.Long import longValue
from java.util import ArrayList
from jarray import array

# Omero Dependencies
from omero.gateway import Gateway
from omero.gateway import LoginCredentials
from omero.gateway import SecurityContext
from omero.gateway.exception import DSAccessException
from omero.gateway.exception import DSOutOfServiceException
from omero.gateway.facility import BrowseFacility
from omero.gateway.facility import DataManagerFacility
from omero.gateway.model import DatasetData
from omero.gateway.model import ExperimenterData
from omero.gateway.model import ProjectData
from omero.log import Logger
from omero.log import SimpleLogger
from omero.model import Pixels

# Setup
# =====

# Drop omero_client.jar and Blitz.jar under the jars folder of FIJI

# Parameters
# ==========

# open Omero Image
# ================

HOST = "omero-balaji.docker.openmicroscopy.org"
USERNAME = "member-all-1"
PASSWORD = "ome"
PORT = 4064

datasetId = "2"
imageId = "1"
groupId = "-1"




def openImagePlus(HOST,USERNAME,PASSWORD,groupId,imageId):
	
	options = ""
	options += "location=[OMERO] open=[omero:server="
	options += HOST
	options += "\nuser="
	options += USERNAME
	options += "\npass="
	options += PASSWORD
	options += "\ngroupID="
	options += groupId
	options += "\niid="
	options += imageId
	options += "]"
	options += " windowless=true "

	print options
	from ij import IJ

	IJ.runPlugIn("loci.plugins.LociImporter", options);

def omeroConnect():

	# Omero Connect with credentials and simpleLogger
	cred = LoginCredentials()
	cred.getServer().setHostname(HOST)
	cred.getServer().setPort(PORT)
	cred.getUser().setUsername(USERNAME)
	cred.getUser().setPassword(PASSWORD)
	simpleLogger = SimpleLogger()
	gateway = Gateway(simpleLogger)
	gateway.connect(cred)
	return gateway

# List all ImageId's under a Project/Dataset
def getImageIds(gateway, datasetId):

	browse = gateway.getFacility(BrowseFacility)
	user = gateway.getLoggedInUser()
	ctx = SecurityContext(user.getGroupId())
	ids = ArrayList(1)
	val = Long(datasetId)
	ids.add(val)
	images = browse.getImagesForDatasets(ctx, ids)
	j = images.iterator()
	imageIds = []
	while j.hasNext():
		image = j.next()
		imageIds.append(String.valueOf(image.getId()))
	return imageIds


def uploadImage(gateway):

	user = gateway.getLoggedInUser()
	ctx = SecurityContext(user.getGroupId())
	sessionKey = gateway.SessionId(user)

	config = Importconfig()

	config.email.set("")
	config.sendFiles.set(true)
	config.sendReport.set(false)
	config.contOnError.set(false)
	config.debug.set(false)
	config.hostname.set(HOSTNAME)
	config.sessionKey.set(sessionKey)
	config.targetClass.set("omero.model.Dataset")
	config.targetId.set(datasetId)

	loci.common.DebugTools.enableLogging("DEBUG")

	store = config.createStore()
#    store.logVersionInfo(config.getIniVersionNumber())
	reader = OMEROWrapper(config)

	library = ImportLibrary(store,reader)
	errorHandler = ErrorHandler(config)

	
# Prototype analysis example
gateway = omeroConnect()
imageIds = getImageIds(gateway,datasetId);
imageIds.sort()
imageId = imageIds[2]
print imageId
openImagePlus(HOST,USERNAME,PASSWORD,groupId,imageId)
gateway.disconnect()	
	

