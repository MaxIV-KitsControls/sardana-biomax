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
FORMULA_READ = 'FormulaRead'
FORMULA_WRITE = 'FormulaWrite'
TANGO_ATTR_ENC = 'TangoAttributeEncoder'
TANGO_ATTR_ENC_THRESHOLD = 'TangoAttributeEncoderThreshold'
TANGO_ATTR_ENC_SPEED = 'TangoAttributeEncoderSpeed'

TAU_ATTR = 'TauAttribute'
TAU_ATTR_ENC = 'TauAttributeEnc'
MOVE_TO = 'MoveTo'
MOVE_TIMEOUT = 'MoveTimeout'

# based on the tango attr motor controller

class PI625(MotorController):
    """This controller offers as many motors as the user wants.
    Each channel has three _MUST_HAVE_ extra attributes:
    +) TangoAttribute - Tango attribute to retrieve the value of the counter
    +) FormulaRead - Formula evaluate using 'VALUE' as the tango read attribute value
    +) FormulaWrite - Formula to evaluate using 'VALUE' as the motor position
    As examples you could have:
    ch1.TangoExtraAttribute = 'my/tango/device/attribute1'
    ch1.FormulaRead = '-1 * VALUE'
    ch2.FormulaWrite = '-1 * VALUE'
    ch2.TangoExtraAttribute = 'my/tango/device/attribute2'
    ch2.FormulaRead = 'math.sqrt(VALUE)'
    ch2.FormulaWrite = 'math.pow(VALUE,2)'

    +) TangoAttributeEncoder - Used in case you have another attribute as encoder
    +) TangoAttributeEncoderThreshold - Threshold used for the 'MOVING' state.
    +) TangoAttributeEncoderSpeed - Speed in units/second of the encoder so 'MOVING' state is computed (sec).
    """
                     
    MaxDevice = 1024

    axis_attributes ={TANGO_ATTR:
                        {Type: str
                         , Description: 'The first Tango Attribute to read (e.g. my/tango/dev/attr)'
                         ,Access: DataAccess.ReadWrite},
                      FORMULA_READ:
                        {Type: str
                         ,Description : 'The Formula to get the desired position from attribute value.\ne.g. "math.sqrt(VALUE)"'
                         ,Access: DataAccess.ReadWrite},
                      FORMULA_WRITE:
                        {Type : str
                         ,Description : 'The Formula to set the desired value from motor position.\ne.g. "math.pow(VALUE,2)"'
                         ,Access : DataAccess.ReadWrite},
                      TANGO_ATTR_ENC:
                        {Type : str
                         ,Description : 'The Tango Attribute used as encoder"'
                         ,Access : DataAccess.ReadWrite},
                      TANGO_ATTR_ENC_THRESHOLD:
                        {Type : float
                         ,Description : 'Maximum difference for considering the motor stopped"'
                         ,Access : DataAccess.ReadWrite},
                      TANGO_ATTR_ENC_SPEED:
                        {Type : float
                         ,Description : 'Units per second used to wait encoder value within threshold after a movement."'
                         ,Access : DataAccess.ReadWrite}
                     }
    
    def __init__(self, inst, props, *args, **kwargs):
        MotorController.__init__(self, inst, props, *args, **kwargs)
        self.axisAttributes = {}

    def AddDevice(self, axis):
        self.axisAttributes[axis] = {}
        self.axisAttributes[axis][TAU_ATTR] = None
        self.axisAttributes[axis][FORMULA_READ] = 'VALUE'
        self.axisAttributes[axis][FORMULA_WRITE] = 'VALUE'
        self.axisAttributes[axis][TAU_ATTR_ENC] = None
        self.axisAttributes[axis][TANGO_ATTR_ENC_THRESHOLD] = 0
        self.axisAttributes[axis][TANGO_ATTR_ENC_SPEED] = 1e-6
        self.axisAttributes[axis][MOVE_TO] = None
        self.axisAttributes[axis][MOVE_TIMEOUT] = None

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
            tau_attr = self.axisAttributes[axis][TANGO_ATTR]
            if tau_attr is None:
                raise Exception("attribute proxy is None")
            return tau_attr.read().value
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
                tau_attr = self.axisAttributes[axis][TANGO_ATTR]
                tau_attr.write(pos)
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
            self.axisAttributes[axis][name] = value
            # att names: TANGO_ON_TARGET, TANGO_ON_ATTR, TANGO_LIMIT
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
