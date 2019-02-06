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

class EnergyUser(PseudoMotorController):
    """
    Pseudo motor controller for handling IVU energy [eV] vs  mono energy [eV], 
    based on the pseudo-controllers for IVU energy (IVUEnergyController) and 
    and mono energy (EnergyController).
    """

    gender = "Insertion Devices"
    model = "IVU Gap"
    organization = "Max IV"

    pseudo_motor_roles = ("energy_user",)
    motor_roles = ("mono_energy", "ivu_energy")

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        self.current_user_energy = 0.0

    def CalcPhysical(self, index, pseudos, physicals):
        return self.CalcAllPhysical(pseudos, physicals)[index - 1]

    def CalcPseudo(self, index, physicals, pseudos):
        return self.CalcAllPseudo(physicals, pseudos)[index - 1]

    def CalcAllPhysical(self, pseudos, physicals):
        self.current_user_energy = pseudos[0]
        
        mono_energy = physicals[0]
        door = PyTango.DeviceProxy('biomax/door/01')
       	
        if self.current_user_energy > 8000 and mono_energy < 8000:
	    door.runmacro(['mirror_strip', 'move', 'Rh'])
            #door.command_inout('RunMacro',['mirror_strip', 'move', 'Rh'])

        elif self.current_user_energy < 8000 and mono_energy > 8000:
	    door.runmacro(['mirror_strip', 'move', 'Si'])
        
        mono_energy_pseudo = self.current_user_energy
        ivu_energy_pseudo = self.current_user_energy
        return (mono_energy_pseudo, ivu_energy_pseudo)

    def CalcAllPseudo(self, physicals, pseudos):
        mono_energy, ivu_energy = physicals
        return (mono_energy,)
