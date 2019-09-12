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

from numpy import interp
import PyTango
import json

class IVUEnergy(PseudoMotorController):
    """
    Pseudo motor controller for handling gap [mm] vs energy [eV] calculation, based on
    supplied table.
    
    for getting the arrays form the beamline excell file:
    import csv
    f = open('fit_table_EnergyGap.csv', 'rU')
    reader = csv.reader(f, delimiter=',', quotechar='\r')

    x = []
    y = []

    for row in reader:
        x.append(float(row[0]))
        y.append(float(row[1]))
    """

    gender = "Insertion Devices"
    model = "IVU Gap"
    organization = "Max IV"

    ctrl_properties = {"energy_array" : {"Type" : str,
                                                  "Description" : "Energy values array",
                                                  "DefaultValue": "[5400, 19550]"
                                        },
                       "position_array" : {"Type" : str,
                                                    "Description" : "Gap position values array",
                                                    "DefaultValue": "[4.9976, 6.9786]"}
                       }

    pseudo_motor_roles = ("ivu_gap_energy",)
    motor_roles = ("ivu_gap_position",)
    ## [keV] vs [mm]
    # energy_position_table = [[5, 6, 7, 8, 9, 10], [5, 10, 15, 20, 25]]

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        if self.energy_array is None:
            raise Exception("Energy vs Position table property needs to be set")

        # it is an string! no matter the Type...
        self.energy_array = json.loads(self.energy_array)
        self.position_array = json.loads(self.position_array)

        self.min_energy = self.energy_array[0]
        self.max_energy = self.energy_array[-1]
        self.current_energy = 0.0
        self.min_position = min(self.position_array)
        self.max_position = max(self.position_array)

    def CalcPseudo(self, index, physicals, curr_pseudo_pos):
        return self.CalcAllPseudo(physicals, curr_pseudo_pos)[index - 1]

    def CalcPhysical(self, index, pseudos, curr_physical_pos):
        return self.CalcAllPhysical(pseudos, curr_physical_pos)[index - 1]

    def CalcAllPhysical(self, pseudos, curr_physical_pos):
        ivu_gap_energy = pseudos[0]
        self.current_energy = ivu_gap_energy
        ivu_gap_position = interp(ivu_gap_energy, self.energy_array, self.position_array)

        if self.min_position <= ivu_gap_position <= self.max_position:
            return (ivu_gap_position,)
        else:
            raise Exception("Requested position out of limits")

    def CalcAllPseudo(self, physicals, curr_pseudo_pos):
        return (self.current_energy,)
