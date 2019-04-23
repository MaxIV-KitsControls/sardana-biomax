###############################################################################
# Beamline energy and mirror strip energy controllers for Biomax.
##
# Copyright (C) 2018  MAX IV Laboratory, Lund Sweden.
##
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
##
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].
###############################################################################

from sardana.pool.controller import PseudoMotorController, Description, Type, DefaultValue 
import PyTango
from PyTango import AttributeProxy
import time
from sardana.pool.poolpseudomotor import PoolPseudoMotor
from sardana.pool.poolmotor import PoolMotor

class BeamlineEnergy(PseudoMotorController):
    """
    Pseudo motor controller for setting  the energy of the beamline.
    This sets the mono energy, the IVU energy,
    and if needed switches mirror strip.
    """
    gender = "Energy"
    model = "Energy"
    organization = "MAX IV"

    pseudo_motor_roles = ("energy_user",)
    motor_roles = ("mono_energy", "ivu_energy", "mirrorstrip_chooser")

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        
        self.current_user_energy = 0.0

    def CalcPhysical(self, index, pseudos, physicals):
        return self.CalcAllPhysical(pseudos, physicals)[index - 1]

    def CalcPseudo(self, index, physicals, pseudos):
        return self.CalcAllPseudo(physicals, pseudos)[index - 1]

    def CalcAllPhysical(self, pseudos, physicals):
        self.current_user_energy = pseudos[0]
        mono_energy_pseudo = self.current_user_energy
        ivu_energy_pseudo = self.current_user_energy
        mirrorstrip_chooser_pseudo = self.current_user_energy
        return (mono_energy_pseudo, ivu_energy_pseudo, mirrorstrip_chooser_pseudo)

    def CalcAllPseudo(self, physicals, pseudos):
        mono_energy, ivu_energy, mirrorstrip_chooser  = physicals
        return (mono_energy,)




class MirrorStripChooser(PseudoMotorController):
    """
    Pseudo motor controller for handling switching of mirror strip for
    energies under and above 8000eV. 
    """

    gender = "Energy"
    model = "Mirror strip"
    organization = "Max IV"

    pseudo_motor_roles = ("energy_user",)
    motor_roles = ("hfm_y", "vfm_x1", "vfm_x2", "piezo_hfm_fpit", "piezo_vfm_fpit")

    ctrl_properties = {'hfm_pos_Si': {Type:'PyTango.DevDouble',
                                       DefaultValue: -1.5,
                                       Description: 'HFM y position for Si'},
                       'hfm_pos_Rh': {Type:'PyTango.DevDouble',
                                       DefaultValue: 10.5,
                                       Description: 'HFM y position for Rh'},
                       'vfm_1_pos_Si': {Type:'PyTango.DevDouble',
                                       DefaultValue: 3.0,
                                       Description: 'VFM x1 position for Si'},
                       'vfm_1_pos_Rh': {Type:'PyTango.DevDouble',
                                       DefaultValue: -5.0,
                                       Description: 'VFM x1 position for Rh'},
                       'vfm_2_pos_Si': {Type:'PyTango.DevDouble',
                                       DefaultValue: 3.0,
                                       Description: 'VFM x2 position for Si'},
                       'vfm_2_pos_Rh': {Type:'PyTango.DevDouble',
                                       DefaultValue: -5.0,
                                       Description: 'VFM x2 position for Rh'},
                       'piezo_hfm_Si_to_Rh': {Type:'PyTango.DevDouble',
                                       DefaultValue: -4.8,
                                       Description: 'Distance to move Piezo HFM position from Si to Rh'},
                       'piezo_vfm_Si_to_Rh': {Type:'PyTango.DevDouble',
                                       DefaultValue: 10.0,
                                       Description: 'Distance to move Piezo VFM position from Si to Rh'},
                        }


    #hfm_positions = {"Si":-1.5, "Rh":10.5}
    #vfm_positions = {"Si":3.0, "Rh":-5.0}
    #piezo_hfm_move = {"Si":4.8, "Rh":-4.8}
    #piezo_vfm_move = {"Si":-10.0, "Rh":10.0}

    def isclose(self, a, b):
        return abs(a-b)<0.1

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        self.strip = ""
        self.current_user_energy = 0.0
        self.hfm_positions = {"Si":self.hfm_pos_Si, "Rh":self.hfm_pos_Rh}
        self.vfm_1_positions = {"Si":self.vfm_1_pos_Si, "Rh":self.vfm_1_pos_Rh}
        self.vfm_2_positions = {"Si":self.vfm_2_pos_Si, "Rh":self.vfm_2_pos_Rh}
        self.piezo_hfm_move = {"Si":-self.piezo_hfm_Si_to_Rh, "Rh":self.piezo_hfm_Si_to_Rh}
        self.piezo_vfm_move = {"Si":-self.piezo_vfm_Si_to_Rh, "Rh":self.piezo_vfm_Si_to_Rh}


    def CalcPhysical(self, index, pseudos, physicals):
        return self.CalcAllPhysical(pseudos, physicals)[index - 1]

    def CalcPseudo(self, index, physicals, pseudos):
        return self.CalcAllPseudo(physicals, pseudos)[index - 1]

    def _check_strip(self, physicals):
        hfm = physicals[0]
        vfm_1 = physicals[1]
        vfm_2 = physicals[2]
        if self.isclose(hfm, self.hfm_positions['Si']) and self.isclose(vfm_1, self.vfm_1_positions['Si']) and self.isclose(vfm_2, self.vfm_2_positions['Si']):
            self.strip = "Si"
        elif self.isclose(hfm, self.hfm_positions['Rh']) and self.isclose(vfm_1, self.vfm_1_positions['Rh']) and self.isclose(vfm_2, self.vfm_2_positions['Rh']):
            self.strip = "Rh"
        else:
            self.strip = "unknown"

    def CalcAllPhysical(self, pseudos, physicals):
        self._check_strip(physicals)
        new_energy = pseudos[0]
        if new_energy > 8000:
            strip = "Rh"
        else:
            strip = "Si"

        curr_hfm_y = physicals[0]
        curr_vfm_x1 = physicals[1]
        curr_vfm_x2 = physicals[2]
        curr_piezo_hfm_fpit = physicals[3]
        curr_piezo_vfm_fpit = physicals[4]

        if strip != self.strip and self.strip in ['Si', 'Rh']:
            self._log.debug("Moving strip to {}.".format(strip))
            hfm_y_pseudo = self.hfm_positions[strip]
            vfm_x1_pseudo = self.vfm_1_positions[strip]
            vfm_x2_pseudo = self.vfm_2_positions[strip]
            piezo_hfm_pseudo = curr_piezo_hfm_fpit + self.piezo_hfm_move[strip]
            piezo_vfm_pseudo = curr_piezo_vfm_fpit + self.piezo_vfm_move[strip]
        elif self.strip not in ['Si', 'Rh']:
            self._log.warning("The strip mirror is not in one of the predefined start positions. Where are we?")
            hfm_y_pseudo = curr_hfm_y
            vfm_x1_pseudo = curr_vfm_x1
            vfm_x2_pseudo = curr_vfm_x2
            piezo_hfm_pseudo = curr_piezo_hfm_fpit
            piezo_vfm_pseudo = curr_piezo_vfm_fpit
        else:
            self._log.debug("No need to move the strip, staying in place.")
            hfm_y_pseudo = curr_hfm_y
            vfm_x1_pseudo = curr_vfm_x1
            vfm_x2_pseudo = curr_vfm_x2
            piezo_hfm_pseudo = curr_piezo_hfm_fpit
            piezo_vfm_pseudo = curr_piezo_vfm_fpit
        
        self.power_on()
        self.strip = strip
        self.current_user_energy = new_energy
        return (hfm_y_pseudo, vfm_x1_pseudo, vfm_x2_pseudo, piezo_hfm_pseudo, piezo_vfm_pseudo)

    def CalcAllPseudo(self, physicals, pseudos):
        self._check_strip(physicals)
        return (self.current_user_energy,)
    
    def get_pool_motors(self,name):
        motor = self.GetMotor(name)
        motors = []
        if isinstance(motor, PoolMotor):
            motors.append(motor)
        elif isinstance(motor, PoolPseudoMotor):
            motors = motors + list(motor.get_user_elements())
        else:
            self._log.warning("Motor {} is of unknown type".format(name))
        return motors

    def power_on(self):
        motors = []
        motors = motors+self.get_pool_motors('hfm_y')
        motors = motors+self.get_pool_motors('vfm_x1')
        motors = motors+self.get_pool_motors('vfm_x2')
        attrs = []
        all_on = True
        for mot in motors:
            try:
                power_attr = AttributeProxy(mot.name + '/PowerOn')
                attrs.append(power_attr)
                if power_attr.read().value==False:
                    power_attr.write(True)
                    all_on=False
            except PyTango.DevFailed as e:
                self._log.warning("Motor {} doesn't have a PowerOn attribute".format(mot.name))
        starttime = time.time()
        while all_on == False:
            if time.time()-starttime > 2:
                raise PyTango.DevFailed("Timeout while waiting for motors to power on")
            all_on = True
            time.sleep(0.1)
            for attr in attrs:
                if attr.read().value == False:
                    all_on = False
            


