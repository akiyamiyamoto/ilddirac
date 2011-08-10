'''
Created on Jul 28, 2011

@author: Stephane Poss
'''
from DIRAC.Core.Workflow.Module                     import ModuleDefinition
from DIRAC.Core.Workflow.Parameter                  import Parameter

from DIRAC import S_OK,S_ERROR, gLogger
import inspect, sys, string, types, os


class Application:
  """ General application definition. Any new application should inherit from this class.
  """
  #need to define slots
  ## __slots__ = []
  def __init__(self,paramdict = None):
    ##Would be cool to have the possibility to pass a dictionary to set the parameters, a bit like the current interface
    
    #application nane (executable)
    self.appname = None
    #application version
    self.version = None
    #Number of evetns to process
    self.nbevts = 0
    #Steering file (duh!)
    self.steeringfile = None
    #Input sandbox: steering file automatically added to SB
    self.inputSB = []
    #Log file
    self.logfile = None
    #Energy to use (duh! again)
    self.energy = 0
    #Detector type (ILD or SID)
    self.detectortype = None
    #Data type : gen, SIM, REC, DST
    self.datatype = None
    #Prod Parameters: things that appear on the prod details
    self.prodparameters = {}
    
    #Application parameters: used when defining the steps in the workflow
    self.parameters = {}
    self.linkedparameters = {}
        
    #Module name and description: Not to be set by the users, internal call only, used to get the Module objects
    self._modulename = ''
    self._moduledescription = ''
    self._modules = []
    self.importLocation = "ILCDIRAC.Workflow.Modules"
        
    #System Configuration: comes from Job definition
    self._systemconfig = ''
    
    #Internal member: hold the list of the job's application set before self: used when using getInputFromApp
    self._jobapps = []
    self._jobsteps = []
    #input application: will link the OutputFile of the guys in there with the InputFile of the self 
    self._inputapp = []
    #Needed to link the parameters.
    self.inputappstep = None
    
    ####Following are needed for error report
    self.log = gLogger
    self.errorDict = {}
    
    ### Next is to use the setattr method.
    self._setparams(paramdict)
  
  def __repr__(self):
    """ String representation of the application
    """
    str  = "%s"%self.appname
    if self.version:
      str += " %s"%self.version
    return str
  
  def _setparams(self,params):
    """ Try to use setattr(self,param) and raise AttributeError in case it does not work. Even better, try to call the self.setParam(). Use eval() for that.
    """
    return S_OK()  
    
    
  def setName(self,name):
    """ Define name of application
    """
    self._checkArgs({ name : types.StringTypes } )
    self.appname = name
    return S_OK()  
    
  def setVersion(self,version):
    """ Define version to use
    """
    self._checkArgs({ version : types.StringTypes } )
    self.version = version
    return S_OK()  
    
  def setSteeringFile(self,steeringfile):
    """ Set the steering file, and add it to sandbox
    """
    self._checkArgs({ steeringfile : types.StringTypes } )
    self.steeringfile = steeringfile
    if os.path.exists(steeringfile) or steeringfile.lower().count("lfn:"):
      self.inputSB.append(steeringfile) 
    return S_OK()  
    
  def setLogFile(self,logfile):
    """ Define application log file
    """
    self._checkArgs({ logfile : types.StringTypes } )
    self.logfile = logfile
    return S_OK()  
  
  def setNbEvts(self,nbevts):
    """ Set the number of events to process
    """
    self._checkArgs({ nbevts : types.IntType })
    self.nbevts = nbevts  
    return S_OK()  
    
  def setEnergy(self,energy):
    """ Set the energy to use
    """
    self._checkArgs({ energy : types.IntType })
    self.energy = energy
    return S_OK()  
    
  def setOutputFile(self,ofile):
    """ Set the output file
    """
    self._checkArgs({ ofile : types.StringTypes } )
    self.parameters['OutputFile']['value']=ofile
    self.prodparameters[ofile]={}
    if self.detectortype:
      self.prodparameters[ofile]['detectortype'] = self.detectortype
    if self.datatype:
      self.prodparameters[ofile]['datatype']= self.datatype
    return S_OK()  
  
  def setInputFile(self,inputfile):
    """ Set the input file to use: stdhep, slcio, root, whatever
    """
    self._checkArgs({ inputfile : types.StringTypes } )
    self.inputfile = inputfile
    if os.path.exists(inputfile) or inputfile.lower().count("lfn:"):
      self.inputSB.append(inputfile)  
    return S_OK()
  
  def getInputFromApp(self,app):
    """ Called to link applications
    
    >>> mokka = Mokka()
    >>> marlin = Marlin()
    >>> marlin.getInputFromApp(mokka)
    
    """
    self._inputapp.append(app)
    return S_OK()  


########################################################################################
#    More private methods: called by the applications of the jobs, but not by the users
########################################################################################
  def _getParameters(self):
    """ Called from Job class
    """
    return self.parameters

  def _createModule(self):
    """ Create Module definition. As it's generic code, all apps will use this.
    """
    module = ModuleDefinition(self._modulename)
    module.setDescription(self._moduledescription)
    body = 'from %s.%s import %s\n' % (self.importLocation, self._modulename, self._modulename)
    module.setBody(body)
    return module
  
  def _getUserOutputDataModule(self):
    """ This is separated as not all applications require user specific output data (i.e. GetSRMFile and Overlay). Only used in UserJobs.
    
    The UserJobFinalization only runs last. It's called every step, but is running only if last.
    """
    module = ModuleDefinition('UserJobFinalization')
    module.setDescription('Uploads user output data files with specific policies.')
    body = 'from %s.%s import %s\n' % (self.importLocation, 'UserJobFinalization', 'UserJobFinalization')
    module.setBody(body)
    return module
  
  def _getComputeOutputDataListModule(self):
    """ This is separated from the applications as this is used in production jobs only.
    """
    module = ModuleDefinition("ComputeOutputDataList")
    module.setDescription("Compute the output data list to be treated by the last finalization")
    body = 'from %s.%s import %s\n' % (self.importLocation, "ComputeOutputDataList", "ComputeOutputDataList" )
    module.setBody(body)
    return module
  
  def _applicationModule(self):
    """ Create the module for the application, and add the parameters to it. Overloaded by every application class.
    """
    return None
  
  def _applicationModuleValues(self,moduleinstance):
    """ Set the values for the modules parameters. Needs to be overloaded for each application.
    """
    pass

  def _userjobmodules(self,step):
    """ Method used to return the needed module for UserJobs. It's different from the ProductionJobs (userJobFinalization for instance)
    """
    self.log.error("This application does not implement the modules, you get an empty list")
    return self._modules
  
  def _prodjobmodules(self,step):
    """ Same as above, but the other way around.
    """
    self.log.error("This application does not implement the modules, you get an empty list")
    return self._modules
  
  def _checkConsistency(self):
    """ Called from Job Class, overloaded by every class. Used to check that everything is fine, in particular that all required parameters are defined.
    Should also call L{_checkRequiredApp} when needed.
    """
    return S_OK()

  def _checkRequiredApp(self):
    """ Called by L{_checkConsistency} when relevant
    """
    if self._inputapp:
      for app in self._inputapp:
        if not app in self._jobapps:
          return S_ERROR("job order not correct: If this app uses some input coming from an other app, the app in question must be passed to job.append() before.")
        else:
          idx = self._jobapps.index(app)
          self.inputappstep = self._jobsteps[idx]
          
    return S_OK()
  
  def _addBaseParameters(self,step):
    """ Add to step the default parameters: appname, version, steeringfile, nbevts, energy, logfile, inputfile, outputfile
    """
    step.addParameter(Parameter("ApplicationName",   "", "string", "", "", False, False, "Application Name"))
    step.addParameter(Parameter("ApplicationVersion","", "string", "", "", False, False, "Application Version"))
    step.addParameter(Parameter("SteeringFile",      "", "string", "", "", False, False, "Steering File"))
    step.addParameter(Parameter("LogFile",           "", "string", "", "", False, False, "Log File"))
    step.addParameter(Parameter("NbEvts",             0,    "int", "", "", False, False, "Number of events to process"))
    step.addParameter(Parameter("Energy",             0,    "int", "", "", False, False, "Energy"))
    step.addParameter(Parameter("InputFile",         "", "string", "", "", False, False, "Input File"))
    step.addParameter(Parameter("OutputFile",        "", "string", "", "", False, False, "Output File"))
    return S_OK()
  
  def _addParametersToStep(self,step):
    """ Method to be overloaded by every application. Add the parameters to the given step. Should call L{_addBaseParameters}.
    Called from Job
    """
    return self._addBaseParameters(step)
  
  def _setStepParametersValues(self,stepinstance):
    """ Method to be overloaded by every application. For all parameters that are not to be linked, set the values in the step instance
    Called from Job
    """
    return S_OK()

  def _resolveLinkedStepParameters(self,stepinstance):
    """ Method to be overloaded by every application that resolve what are the linked parameters (e.g. OuputFile and InputFile) See L{StdhepCut} for example.
    Called from Job.
    """
    return S_OK()

  def _analyseJob(self,job):
    """ Called from Job, only gives the application the knowledge of the Job (application, step, system config)
    """
    self.job = job
    
    self._systemconfig = job.systemConfig
    
    self._jobapps      = job.applicationlist
    
    self._jobsteps     = job.steps
    
    return S_OK()

  def _checkArgs( self, argNamesAndTypes ):
    """ Private method to check the validity of the parameters
    """

    # inspect.stack()[1][0] returns the frame object ([0]) of the caller
    # function (stack()[1]).
    # The frame object is required for getargvalues. Getargvalues returns
    # a typle with four items. The fourth item ([3]) contains the local
    # variables in a dict.

    args = inspect.getargvalues( inspect.stack()[ 1 ][ 0 ] )[ 3 ]

    #

    for argName, argType in argNamesAndTypes.iteritems():

      if not args.has_key(argName):
        self._reportError(
          'Method does not contain argument \'%s\'' % argName,
          __name__,
          **self._getArgsDict( 1 )
        )

      if not isinstance( args[argName], argType):
        self._reportError(
          'Argument \'%s\' is not of type %s' % ( argName, argType ),
          __name__,
          **self._getArgsDict( 1 )
        )

  def _getArgsDict( self, level = 0 ):
    """ Private method
    """

    # Add one to stack level such that we take the caller function as the
    # reference point for 'level'

    level += 1

    #

    args = inspect.getargvalues( inspect.stack()[ level ][ 0 ] )
    dict = {}

    for arg in args[0]:

      if arg == "self":
        continue

      # args[3] contains the 'local' variables

      dict[arg] = args[3][arg]

    return dict

  #############################################################################
  def _reportError( self, message, name = '', **kwargs ):
    """Internal Function. Gets caller method name and arguments, formats the 
       information and adds an error to the global error dictionary to be 
       returned to the user. 
       Stolen from DIRAC Job Class
    """
    className = name
    if not name:
      className = __name__
    methodName = sys._getframe( 1 ).f_code.co_name
    arguments = []
    for key in kwargs:
      if kwargs[key]:
        arguments.append( '%s = %s ( %s )' % ( key, kwargs[key], type( kwargs[key] ) ) )
    finalReport = 'Problem with %s.%s() call:\nArguments: %s\nMessage: %s\n' % ( className, methodName, string.join( arguments, ', ' ), message )
    if self.errorDict.has_key( methodName ):
      tmp = self.errorDict[methodName]
      tmp.append( finalReport )
      self.errorDict[methodName] = tmp
    else:
      self.errorDict[methodName] = [finalReport]
    self.log.verbose( finalReport )
    return S_ERROR( finalReport )
