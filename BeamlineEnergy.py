###############################################################################
# Mono energy and IVU energy controllers for Biomax.
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

from sardana.pool.controller import PseudoMotorController
import PyTango
import time

class BeamlineEnergy(PseudoMotorController):
    """
    Pseudo motor controller for setting  the energy of the beamline.
    This sets the mono energy, the IVU energy,
    and if needed switches mirror strip.
    """

    gender = "Insertion Devices"
    model = "IVU Gap"
    organization = "Max IV"

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

    gender = "Insertion Devices"
    model = "IVU Gap"
    organization = "Max IV"

    pseudo_motor_roles = ("energy_user",)
    motor_roles = ("hfm_y", "vfm_x", "piezo_hfm_fpit", "piezo_vfm_fpit")

    hfm_positions = {"Si":-1.5, "Rh":10.5}
    vfm_positions = {"Si":3.0, "Rh":-5.0}
    piezo_hfm_move = {"Si":4.8, "Rh":-4.8}
    piezo_vfm_move = {"Si":-10.0, "Rh":10.0}

    def isclose(self, a, b):
        return abs(a-b)<0.1

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        self.strip = ""
        self.current_user_energy = 0.0

    def CalcPhysical(self, index, pseudos, physicals):
        return self.CalcAllPhysical(pseudos, physicals)[index - 1]

    def CalcPseudo(self, index, physicals, pseudos):
        return self.CalcAllPseudo(physicals, pseudos)[index - 1]

    def _checkStrip(self, physicals):
        #hfm = self.GetMotor("hfm_y").get_position(self).get_value()
        #vfm = self.GetMotor("vfm_x").get_position(self).get_value()
        hfm = physicals[0]
        vfm = physicals[1]
        if self.isclose(hfm, self.hfm_positions['Si']) and self.isclose(vfm, self.vfm_positions['Si']):
            self.strip = "Si"
        elif self.isclose(hfm, self.hfm_positions['Rh']) and self.isclose(vfm, self.vfm_positions['Rh']):
            self.strip = "Rh"
        else:
            self.strip = "unknown"

    def CalcAllPhysical(self, pseudos, physicals):
        self._checkStrip(physicals)
        self.current_user_energy = pseudos[0]
        if self.current_user_energy > 8000:
            strip = "Rh"
        else:
            strip = "Si"

        curr_hfm_y = physicals[0]
        curr_vfm_x = physicals[1]
        curr_piezo_hfm_fpit = physicals[2]
        curr_piezo_vfm_fpit = physicals[3]

        if strip != self.strip and self.strip in ['Si', 'Rh']:
            self.power_on()
            hfm_y_pseudo = self.hfm_positions[strip]
            vfm_x_pseudo = self.vfm_positions[strip]
            piezo_hfm_pseudo = curr_piezo_hfm_fpit + self.piezo_hfm_move[strip]
            piezo_vfm_pseudo = curr_piezo_vfm_fpit + self.piezo_vfm_move[strip]
        else:
            hfm_y_pseudo = curr_hfm_y
            vfm_x_pseudo = curr_vfm_x
            piezo_hfm_pseudo = curr_piezo_hfm_fpit
            piezo_vfm_pseudo = curr_piezo_vfm_fpit
        
        self.power_on()
        self.strip = strip
        return (hfm_y_pseudo, vfm_x_pseudo, piezo_hfm_pseudo, piezo_vfm_pseudo)

    def CalcAllPseudo(self, physicals, pseudos):
        self._checkStrip(physicals)
        return (self.current_user_energy,)
    
    def power_on(self):
        try:
            pass
            #self.GetMotor("hfm_y").PowerOn = 1
            #self.vfm_x1.PowerOn = 1
            #self.vfm_x2.PowerOn = 1
        except Exception, e:
            print str(e)

    #def power_off(self):
    #    try:
    #        self.hfm_y.PowerOn = 0
    #        self.vfm_x1.PowerOn = 0
    #        self.vfm_x2.PowerOn = 0
    #    except Exception, e:
    #        self.error(e)

