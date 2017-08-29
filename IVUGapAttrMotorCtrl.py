from PyTango import AttrQuality
from PyTango import AttributeProxy
from PyTango import DevFailed

from sardana import State, DataAccess
from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Access, Description

import math
import time


TANGO_ATTR = 'TangoAttribute'
TANGO_UPPER_LIMIT = 'UpperLimit'
TANGO_LOWER_LIMIT = 'LowerLimit'

# based on the tango attr motor controller, removed stuff and adapt to ivu needs

class IVUGapAttrMotorController(MotorController):
    """Each channel has a _MUST_HAVE_ extra attribute:
    +) TangoAttribute - Tango attribute to retrieve the value of the piezo position
    +) UpperLimit and LowerLimit - optional values for the position limits
    As examples you could have:
    ch1.TangoAttribute = 'my/tango/device/Gap'
    ch1.UpperLimit = 38  # this is default value
    ch1.LowerLimit = 4  # this is default value

    """

    gender = "IVU"
    model = ""
    organization = "MaxIV"

    MaxDevice = 1

    axis_attributes ={TANGO_ATTR:
                        {Type: str
                         , Description: 'The piezo position Tango Attribute to read (e.g. my/tango/dev/Gap)'
                         ,Access: DataAccess.ReadWrite},
                     }

    def __init__(self, inst, props, *args, **kwargs):
        MotorController.__init__(self, inst, props, *args, **kwargs)
        self.axisAttributes = {}

    def AddDevice(self, axis):
        self.axisAttributes[axis] = {}
        self.axisAttributes[axis][TANGO_ATTR] = None
        self.axisAttributes[axis][TANGO_UPPER_LIMIT] = 38
        self.axisAttributes[axis][TANGO_LOWER_LIMIT] = 4

    def DeleteDevice(self, axis):
        del self.axisAttributes[axis]

    def StateOne(self, axis):
        try:
            tau_attr = self.axisAttributes[axis][TANGO_ATTR]
            quality = tau_attr.read().quality
            if quality == AttrQuality.ATTR_CHANGING:
                state = State.Moving
                status = 'Moving'
            elif quality == AttrQuality.ATTR_VALID:
                state = State.On
                status = 'On'
            elif quality == AttrQuality.ATTR_WARNING:
                state = State.Alarm
                status = 'Alarm'
            elif quality == AttrQuality.ATTR_ALARM:
                state = State.Fault
                status = 'Fault'
            else:
                state = State.Unknown
                status = 'Unknown'

            switch_state = 0

            return (state, status, switch_state)
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
            pos_attr = self.axisAttributes[axis][TANGO_ATTR]
            if pos_attr is None:
                raise Exception("attribute proxy is None")
            return pos_attr.read().value
        except Exception, e:
            self._log.error("(%d) error reading: %s" % (axis, str(e)))
            raise e

    def PreStartAll(self):
        pass

    def PreStartOne(self, axis, pos):
        return not self.axisAttributes[axis][TANGO_ATTR] is None

    def StartOne(self, axis, pos):
        if pos > self.axisAttributes[axis][TANGO_LOWER_LIMIT] and pos <= self.axisAttributes[axis][TANGO_UPPER_LIMIT]:
            try:
                pos_attr = self.axisAttributes[axis][TANGO_ATTR]
                pos_attr.write(pos)
            except Exception, e:
                self._log.error("(%d) error writing: %s" % (axis, str(e)))
        else:
            raise Exception("Requested position out of limits")

    def StartAll(self):
        pass

    def AbortOne(self, axis):
        pass

    def StopOne(self, axis):
        pass

    def SetPar(self, axis, name, value):
        self.axisAttributes[axis][name] = value

    def GetPar(self, axis, name):
        return self.axisAttributes[axis][name]

    def GetAxisExtraPar(self, axis, name):
        return self.axisAttributes[axis][name]

    def SetAxisExtraPar(self, axis, name, value):
        try:
            self._log.debug("SetExtraAttributePar [%d] %s = %s" % (axis, name, value))
            if name == 'Limit':
                self.axisAttributes[axis][name] = value
            else:
                if name in [TANGO_ATTR]:
                    try:
                        self.axisAttributes[axis][name] = AttributeProxy(value)
                    except Exception, e:
                        self.axisAttributes[axis][name] = None
                        raise e
        except DevFailed, df:
            de = df[0]
            self._log.error("SetExtraAttribute DevFailed: (%s) %s" % (de.reason, de.desc))
            self._log.error("SetExtraAttribute DevFailed: %s" % str(df))
        except Exception, e:
            self._log.error("SetExtraAttribute Exception: %s" % str(e))

    def SendToCtrl(self, in_data):
        return ""
