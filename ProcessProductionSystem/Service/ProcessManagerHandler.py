###########################################################################
# $HeadURL: $
###########################################################################

""" Services for ProcessProduction System
"""
__RCSID__ = " $Id: $ "

from DIRAC                                              import gLogger, gConfig, S_OK, S_ERROR
from DIRAC.Core.DISET.RequestHandler                    import RequestHandler
from types import *

from ILCDIRAC.ProcessProductionSystem.DB.ProcessDB import ProcessDB

# This is a global instance of the ProcessDB class
processDB = False

def initializeProcessManagerHandler( serviceInfo ):

  global processDB
  processDB = ProcessDB()
  return S_OK()

class ProcessManagerHandler(RequestHandler):
######################################################################
#               Get methods
######################################################################
  types_getSoftwares = []
  def export_getSoftwares(self):
    """ Get all software as a dictionnary
    """
    return processDB.getSoftwares()
  
  types_getProcessInfo = [StringTypes]
  def export_getProcessInfo(self, ProcessName):
    """Get all info for a given process
    """
    return processDB.getProcessInfo(ProcessName)
  
  types_getTamples = [StringTypes,StringTypes]
  def export_getTemplate(self, ProcessName, WhizVersion):
    """ Get the proper template
    """
    return processDB.getTemplate(ProcessName, WhizVersion)

#######################################################################
#              Add methods
#######################################################################
  types_addSoftware = [ StringTypes, StringTypes, StringTypes, StringTypes]
  def export_addSoftware(self, AppName, AppVersion, Comment, Path):
    """ Add new software in the DB
    """
    return processDB.addSoftware(AppName, AppVersion, Comment, Path)
    
  types_addDependency = [StringTypes,StringTypes,StringTypes,StringTypes]
  def export_addDependency(self, AppName, AppVersion, DepName, DepVersion):
    """ Add a dependency between softwares
    """
    return processDB.addDependency(AppName, AppVersion, DepName, DepVersion)
 
  types_addSteeringFile = [StringTypes, StringTypes]
  def export_addSteeringFile(self,FileName, Path=''):
    """ Declare a steering file
    """
    return processDB.addSteeringFile(FileName, Path)
  
  types_addProductionData = [DictType]
  def export_addProductionData(self,ProdDataDict):
    """ Add a new Production data object
    """
    if (not ProdDataDict.has_key("ProdID") 
        or not ProdDataDict.has_key("Process") 
        or not ProdDataDict.has_key("Path") 
        or not ProdDataDict.has_key("AppName")
        or not ProdDataDict.has_key("AppVersion")):
      return S_ERROR('Incorrect dictionary structure')
    return processDB.addProductionData(ProdDataDict)
  
  types_addProcess = [StringTypes, StringTypes, StringTypes, StringTypes]
  def export_addProcess(self,ProcessName, ProcessDetail, WhizardVers, Template):
    """ Add a new process
    """
    return processDB.addProcess(ProcessName, ProcessDetail, WhizardVers, Template)
  
#######################################################################
#              Change methods
#######################################################################
  types_updateCrossSection = [DictType]
  def export_updateCrossSection(self,ProcessDict):
    """ Update the cross section for the given process and software version
    """
    if not (ProcessDict.has_key('ProdID') and ProcessDict.has_key('AppName') and ProcessDict.has_key('CrossSection')):
      return S_ERROR("Missing essential dictionary info")
    return processDB.updateCrossSection(ProcessDict)
    
  types_changeSoftwareStatus = [StringTypes,StringTypes,StringTypes,BooleanType]
  def export_changeSoftwareStatus(self,AppName,AppVersion,Comment,Status = False):
    """ Change the status of a software, by feault to False
    """
    return processDB.changeSoftwareStatus(AppName, AppVersion, Comment, Status)
  
