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

from sardana.pool.controller import PseudoMotorController, Startable
import PyTango
import time

class BeamlineEnergy(PseudoMotorController):
    """
    Pseudo motor controller for handling IVU energy [eV] vs  mono energy [eV], 
    based on the pseudo-controllers for IVU energy (IVUEnergyController) and 
    and mono energy (EnergyController).
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
    Pseudo motor controller for handling IVU energy [eV] vs  mono energy [eV], 
    based on the pseudo-controllers for IVU energy (IVUEnergyController) and 
    and mono energy (EnergyController).
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
        self.previous_strip = ""
        self.strip = ""
        #hfm = self.GetMotor(self,"hfm_y") 
        #print hfm #.get_position(self)
        #vfm = self.getMotor("vfm_x").get_position(self)
        #if self.isclose(hfm,hfm_positions['Si']) and self.isclose(vfm,vfm_positions['Si']):
        #    self.previous_strip = "Si"
        #    self.strip = "Si"
        #elif self.isclose(hfm,hfm_positions['Rh']) and self.isclose(vfm,vfm_positions['Rh']):
        #    self.previous_strip = "Rh"
        #    self.strip = "Rh"
        #else:
        #    self.previous_strip = "unknown"
        #    self.strip = "unknown"
        
        self.current_user_energy = 0.0

    def CalcPhysical(self, index, pseudos, physicals):
        return self.CalcAllPhysical(pseudos, physicals)[index - 1]

    def CalcPseudo(self, index, physicals, pseudos):
        return self.CalcAllPseudo(physicals, pseudos)[index - 1]

    def CalcAllPhysical(self, pseudos, physicals):
        if not self.strip:
            hfm = self.GetMotor("hfm_y").get_position(self)
            print hfm
        #print hfm #.get_position(self)
        #vfm = self.getMotor("vfm_x").get_position(self)
        #if self.isclose(hfm,hfm_positions['Si']) and self.isclose(vfm,vfm_positions['Si']):
        #    self.previous_strip = "Si"
        #    self.strip = "Si"
        #elif self.isclose(hfm,hfm_positions['Rh']) and self.isclose(vfm,vfm_positions['Rh']):
        #    self.previous_strip = "Rh"
        #    self.strip = "Rh"
        #else:
        #    self.previous_strip = "unknown"
        #    self.strip = "unknown"
        self.current_user_energy = pseudos[0]
        if self.current_user_energy > 8000:
            self.strip = "Rh"
        else:
            self.strip = "Si"

        curr_hfm_y = physicals[0]
        curr_vfm_x = physicals[1]
        curr_piezo_hfm_fpit = physicals[2]
        curr_piezo_vfm_fpit = physicals[3]

        if self.strip != self.previous_strip:
            self.power_on()
            hfm_y_pseudo = self.hfm_positions[self.strip]
            vfm_x_pseudo = self.vfm_positions[self.strip]
            piezo_hfm_pseudo = curr_piezo_hfm_fpit + self.piezo_hfm_move[self.strip]
            piezo_vfm_pseudo = curr_piezo_vfm_fpit + self.piezo_vfm_move[self.strip]
        else:
            hfm_y_pseudo = curr_hfm_y
            vfm_x_pseudo = curr_vfm_x
            piezo_hfm_pseudo = curr_piezo_hfm_fpit
            piezo_vfm_pseudo = curr_piezo_vfm_fpit
        
        self.power_on()
        self.previous_strip = self.strip
        return (hfm_y_pseudo, vfm_x_pseudo, piezo_hfm_pseudo, piezo_vfm_pseudo)

    def CalcAllPseudo(self, physicals, pseudos):
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

