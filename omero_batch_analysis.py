import os
from os import path

from java.lang import Long
from java.lang import String
from java.lang.Long import longValue
from java.util import ArrayList
from jarray import array
from java.lang.reflect import Array
import java

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

from ome.formats.importer import ImportConfig
from ome.formats.importer import OMEROWrapper
from ome.formats.importer import ImportLibrary
from ome.formats.importer import ImportCandidates
from ome.formats.importer.cli import ErrorHandler
from ome.formats.importer.cli import LoggingImportMonitor
import loci.common
from loci.formats.in import DefaultMetadataOptions
from loci.formats.in import MetadataLevel
from ij import IJ

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
        
        IJ.runPlugIn("loci.plugins.LociImporter", options);

def omeroConnect():
    
    # Omero Connect with credentials and simpleLogger
    cred = LoginCredentials()
        cred.getServer().setHostname(HOST)
        cred.getServer().setPort(PORT)
        cred.getUser().setUsername(USERNAME.strip())
        cred.getUser().setPassword(PASSWORD.strip())
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


def uploadImage(path, gateway):
    
    user = gateway.getLoggedInUser()
        ctx = SecurityContext(user.getGroupId())
        sessionKey = gateway.getSessionId(user)
        
        config = ImportConfig()
        
        config.email.set("")
        config.sendFiles.set('true')
        config.sendReport.set('false')
        config.contOnError.set('false')
        config.debug.set('false')
        config.hostname.set(HOST)
        config.sessionKey.set(sessionKey)
        config.targetClass.set("omero.model.Dataset")
        config.targetId.set(datasetId)
        
        loci.common.DebugTools.enableLogging("DEBUG")
        
        store = config.createStore()
        reader = OMEROWrapper(config)
        
        library = ImportLibrary(store,reader)
        errorHandler = ErrorHandler(config)
        
        library.addObserver(LoggingImportMonitor())
        candidates = ImportCandidates (reader, path, errorHandler)
        reader.setMetadataOptions(DefaultMetadataOptions(MetadataLevel.ALL))
        success = library.importCandidates(config, candidates)
        return success

# Setup
# =====

# Drop omero_client.jar and Blitz.jar under the jars folder of FIJI

# Parameters
# ==========

# open Omero Image
# ================

#OMERO Server details
HOST = "omero-latest-analysis.docker.openmicroscopy.org"
PORT = 4064
datasetId = "1"
groupId = "-1"

#Credentials stored in a text file
#Format : username = USERNAME
#Format : password = PASSWORD
CREDENTIALS = "/Users/bramalingam/Desktop/FijiDemonstration/credentials.txt"

# File path to the ImageJ/FIJI macro
macroFilePath = "/Users/bramalingam/Desktop/FijiDemonstration/bg_subtract.ijm"
operation = "_bg_subtract"
# Bio-Formats exports the processed images to the following path
paths= "/Users/bramalingam/Desktop/FijiDemonstration/"

#for demo alone
myvars = {}
myfile = open(CREDENTIALS)
for line in myfile:
    name, var = line.partition("=")[::2]
    myvars[name.strip()] = var.strip()
USERNAME = myvars['username']
PASSWORD = myvars['password']

# Prototype analysis example
gateway = omeroConnect()
imageIds = getImageIds(gateway,datasetId);
imageIds.sort()

for imageId in imageIds:
    #	imageId = imageIds[2]
    print imageId
        openImagePlus(HOST,USERNAME,PASSWORD,groupId,imageId)
        IJ.run("Enhance Contrast", "saturated=0.35");
        #Plug Your analysis here#
        
        IJ.runMacroFile(macroFilePath)
        
        #	Save resultant image using Bio-Formats
        imp = IJ.getImage();
        path = paths + imp.getTitle() + operation + ".ome.tiff";
        print(path)
        options = "save=[" + path + "] export compression=Uncompressed"
        IJ.run(imp, "Bio-Formats Exporter", options);
        imp.changes = False
        imp.close()
        
        #	Upload image to OMERO
        str2d = java.lang.reflect.Array.newInstance(java.lang.String,[1])
        str2d [0] = path
        success = uploadImage(str2d, gateway)

print("Done")
#success = uploadImage(str2d, gateway)
gateway.disconnect()	



