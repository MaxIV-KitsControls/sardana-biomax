from PyTango import AttrQuality
from PyTango import AttributeProxy
from PyTango import DevFailed

from sardana import State, DataAccess
from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Access, Description

import math
import time


TANGO_ATTR = 'TangoAttribute'
TANGO_ON_TARGET = 'TangoOnTarget'
TANGO_LIMIT = 'Limit'

# based on the tango attr motor controller, removed stuff and adapt to the piezo on_target and limits

class PI625(MotorController):
    """This controller offers as many motors as the user wants.
    Each channel has two _MUST_HAVE_ extra attributes:
    +) TangoAttribute - Tango attribute to retrieve the value of the piezo position
    +) TangoOnTarget - Tango attribute to retrieve the value of the on target piezo parameter
    +) Limit - optional value for the high position limit
    As examples you could have:
    ch1.TangoAttribute = 'my/tango/device/Position'
    ch1.TangoOnTarget =  'my/tango/device/on_target
    ch2.Limit = 42
    """

    MaxDevice = 1024

    axis_attributes ={TANGO_ATTR:
                        {Type: str
                         , Description: 'The piezo position Tango Attribute to read (e.g. my/tango/dev/Position)'
                         ,Access: DataAccess.ReadWrite},
                      TANGO_ON_TARGET:
                        {Type: str
                         , Description: 'The piezo on_target Tango Attribute to read (e.g. my/tango/dev/on_target)'
                         ,Access: DataAccess.ReadWrite},
                     }

    def __init__(self, inst, props, *args, **kwargs):
        MotorController.__init__(self, inst, props, *args, **kwargs)
        self.axisAttributes = {}

    def AddDevice(self, axis):
        self.axisAttributes[axis] = {}
        self.axisAttributes[axis][TANGO_ATTR] = None
        self.axisAttributes[axis][TANGO_ON_TARGET] = None
        self.axisAttributes[axis][TANGO_LIMIT] = 45


    def DeleteDevice(self, axis):
        del self.axisAttributes[axis]

    def StateOne(self, axis):
        try:
            on_target_att = self.axisAttributes[axis][TANGO_ON_TARGET]
            state = State.On
            status = 'ok'
            switch_state = 0
            if on_target_att is None:
                return (State.Alarm, "attribute proxy is None", 0)

            if not on_target_att.read().value:
                state = State.Moving
            else:
                state = State.On
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
        if pos > 0 and pos <= self.axisAttributes[axis][TANGO_LIMIT]:
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
                if name in [TANGO_ATTR, TANGO_ON_TARGET]:
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
