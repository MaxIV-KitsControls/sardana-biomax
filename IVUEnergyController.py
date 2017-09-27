###############################################################################
##     Energy and wavelength controllers for Biomax. 
##
##     Copyright (C) 2017  MAX IV Laboratory, Lund Sweden.
##
##     This program is free software: you can redistribute it and/or modify
##     it under the terms of the GNU General Public License as published by
##     the Free Software Foundation, either version 3 of the License, or
##     (at your option) any later version.
##
##     This program is distributed in the hope that it will be useful,
##     but WITHOUT ANY WARRANTY; without even the implied warranty of
##     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##     GNU General Public License for more details.
##
##     You should have received a copy of the GNU General Public License
##     along with this program.  If not, see [http://www.gnu.org/licenses/].
###############################################################################

from sardana import State
from sardana.pool.controller import PseudoMotorController
from sardana.pool.controller import Type
from sardana.pool.controller import Description
import PyTango
from numpy import interp

class IVUEnergy(PseudoMotorController):
    """
    Pseudo motor controller for handling gap [mm] vs energy [eV] calculation, based on
    supplied table.
    """
    gender = "Insertion Devices"
    model = "IVU Gap"
    organization = "Max IV"

    ctrl_properties = {"energy_position_table" : {"Type" : PyTango.DevVarDoubleArray, "Description" : "Energy vs Position table"}}

    pseudo_motor_roles = ("ivu_gap_energy",)
    motor_roles = ("ivu_gap_position",)
    ## [keV] vs [mm]
    # energy_position_table = [[5, 6, 7, 8, 9, 10], [5, 10, 15, 20, 25]]

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        if self.energy_position_table is None:
            raise Exception("Energy vs Position table property needs to be set")
        
        self.min_energy = self.energy_position_table[0][0]
        self.min_energy = self.energy_position_table[0][-1]

        self.min_position = self.energy_position_table[1][0]
        self.max_position = self.energy_position_table[1][-1]

    def CalcPseudo(self, index, physicals, curr_pseudo_pos):
        return self.CalcAllPseudo(physicals, curr_pseudo_pos)[index - 1]

    def CalcPhysical(self, index, pseudos, curr_physical_pos):
        return self.CalcAllPhysical(pseudos, curr_physical_pos)[index - 1]

    def CalcAllPhysical(self, pseudos, curr_physical_pos):
        ivu_gap_energy = pseudos[0]
        self._log.info('IVU Gap as energy: %f', ivu_gap_energy)
        self._log.info('IVU Gap as position: %f', curr_physical_pos[0])

        ivu_gap_position = interp(ivu_gap_energy, energy_position_table[0], energy_position_table[1])

        if self.min_position < ivu_gap_position < self.max_position:
            return (ivu_gap_position,)
        else:
            raise Exception("Requested position out of limits")

    def CalcAllPseudo(self, physicals, curr_pseudo_pos):
        ivu_gap_position = physicals[0]
        
        ivu_gap_energy = interp(ivu_gap_position, energy_position_table[1], energy_position_table[0])

        return (ivu_gap_energy,)
