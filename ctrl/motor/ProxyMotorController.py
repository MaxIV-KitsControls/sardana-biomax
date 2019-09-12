from PyTango import AttrQuality
from PyTango import DeviceProxy
from PyTango import DevFailed
from PyTango import DevState

from sardana import State, DataAccess
from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Description, DefaultValue, Access, FGet, FSet

import math
import time

TANGO_UPPER_LIMIT = 'UpperLimit'
TANGO_LOWER_LIMIT = 'LowerLimit'

# based on the tango attr motor controller, removed stuff and adapt to ivu needs

class ProxyMotorController(MotorController):
    """The controller has a _MUST_HAVE_ property:
    +) MotorName - Tango device name for the motor that we want to be a proxy
    As examples you could have:
    MotorName = 'my/tango/device'
   
    The channel has some _MUST_HAVE_ extra attributes:
    +) UpperLimit and LowerLimit - optional values for the position limits
    As examples you could have:
    ch1.UpperLimit = 38  # this is default value
    ch1.LowerLimit = 4  # this is default value

    """

    gender = "Proxy"
    model = ""
    organization = "MaxIV"

    MaxDevice = 1


    ctrl_properties = {
                        'MotorName':
                        {Type: str, 
                         Description: 'The motor we are controlling (e.g. my/tango/dev)',
                         DefaultValue: ""
                         },
                        'InterlockDevice':
                        {Type: str, 
                         Description: 'The name of the device of which the State is checked.',
                         DefaultValue: ""
                         }
                      }

    axis_attributes = {
                         TANGO_UPPER_LIMIT:
                         {Type: float,
                         Description: 'Upper limit of the gap movement',
                         DefaultValue: 38,
                         Access: DataAccess.ReadWrite,
                         FGet: 'get_upperlimit',
                         FSet: 'set_upperlimit'
                         },
                         TANGO_LOWER_LIMIT:
                         {Type: float,
                         Description: 'Lower limit of the gap movement',
                         DefaultValue: 4,
                         Access: DataAccess.ReadWrite,
                         FGet: 'get_lowerlimit',
                         FSet: 'set_lowerlimit'
                         }
                       }

    def __init__(self, inst, props, *args, **kwargs):
        MotorController.__init__(self, inst, props, *args, **kwargs)
        self.axisAttributes = {}
        self.interlockProxy = None
        try:
            print self.MotorName, self.InterlockDevice
            self.motorProxy = DeviceProxy(self.MotorName)
            if self.InterlockDevice!="":
                self.interlockProxy = DeviceProxy(self.InterlockDevice)
        except DevFailed, df:
            de = df[0]
            self._log.error("__init__ DevFailed: (%s) %s" % (de.reason, de.desc))
            self._log.error("__init__ DevFailed: %s" % str(df))
        except Exception, e:
            self._log.error("__init__ Exception: %s" % str(e))


    def AddDevice(self, axis):
        self.axisAttributes[axis] = {}
        self.axisAttributes[axis][TANGO_UPPER_LIMIT] = 38
        self.axisAttributes[axis][TANGO_LOWER_LIMIT] = 4

    def DeleteDevice(self, axis):
        del self.axisAttributes[axis]

   # def SetPar(self, axis, name, value):
   #     self.axisAttributes[axis][name] = value

    #def GetPar(self, axis, name):
    #    return self.axisAttributes[axis][name]

    def get_upperlimit(self, axis):
        return self.axisAttributes[axis][TANGO_UPPER_LIMIT]
    
    def get_lowerlimit(self, axis):
        return self.axisAttributes[axis][TANGO_LOWER_LIMIT]

    def set_upperlimit(self, axis, value):
        self.axisAttributes[axis][TANGO_UPPER_LIMIT] = value
    
    def set_lowerlimit(self, axis, value):
        self.axisAttributes[axis][TANGO_LOWER_LIMIT] = value

    def StateOne(self, axis):
        try:
            if self.interlockProxy is not None:
                ilockstate = self.interlockProxy.State()
                if ilockstate in [DevState.ALARM, DevState.FAULT, DevState.UNKNOWN, DevState.INIT]:
                    state = State.Disable
                    status = 'The device is interlocked.' 
                    return (state, status, 0)
			
            state = self.motorProxy.State()
            status = self.motorProxy.Status()
            return (state, status, 0)
        except Exception, e:
            self._log.error(" (%d) error getting state: %s" % (axis, str(e)))
            return (State.Alarm, "Exception: %s" % str(e), 0)

    def PreReadAll(self):
        pass

    def PreReadOne(self, axis):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, axis):
        try:
            motor = self.motorProxy
            if motor is None:
                raise Exception("device proxy is None")
            return motor.Position
        except Exception, e:
            self._log.error("(%d) error reading: %s" % (axis, str(e)))
            raise e

    def PreStartAll(self):
        pass

    def PreStartOne(self, axis, pos):
        return not self.motorProxy is None

    def StartOne(self, axis, pos):
        if pos > self.axisAttributes[axis][TANGO_LOWER_LIMIT] and pos <= self.axisAttributes[axis][TANGO_UPPER_LIMIT]:
            try:
                motor = self.motorProxy
                motor.Position = pos
            except Exception, e:
                self._log.error("(%d) error writing: %s" % (axis, str(e)))
        else:
            raise Exception("Requested position out of limits")

    def StartAll(self):
        pass

    def AbortOne(self, axis):
        try:
            self.motorProxy.Abort()
        except Exception, e:
            self._log.error("(%d) error aborting: %s" % (axis, str(e)))
    
    def StopOne(self, axis):
        try:
            self.motorProxy.Stop()
        except Exception, e:
            self._log.error("(%d) error stopping: %s" % (axis, str(e)))

    def SetPar(self, axis, name, value):
        self.axisAttributes[axis][name] = value

    def GetPar(self, axis, name):
        return self.axisAttributes[axis][name]

    def SendToCtrl(self, in_data):
        return ""
