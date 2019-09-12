###############################################################################
##    Slit controllers for Biomax. 
##
##     Copyright (C) 2015  MAX IV Laboratory, Lund Sweden.
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
from sardana.pool.controller import MotorController, PseudoMotorController

from sardana.pool.controller import Type
from sardana.pool.controller import Description


class SlitController(PseudoMotorController):
    """A Slit pseudo motor controller for handling gap and offset pseudo 
       motors. The system uses to real motors sl2t (top slit) and sl2b (bottom
       slit).Based on Slit.py from Alba"""

    gender = "Slit"
    model = "Common direction slit"
    organization = "Max IV"

    pseudo_motor_roles = ("pos", "gap")
    motor_roles = ("slit_1", "slit_2")

    class_prop = {'sign':{'Type':'PyTango.DevDouble','Description':'Gap = sign * calculated gap\nOffset = sign * calculated offet','DefaultValue':1},}

    def CalcPhysical(self, index, pseudos, physicals):
        return self.CalcAllPhysical(pseudos, physicals)[index - 1]

    def CalcPseudo(self,index,physicals, pseudos):
        return self.CalcAllPseudo(physicals, pseudos)[index - 1]

    def CalcAllPseudo(self, physicals, pseudos):
        """Calculates the positions of all pseudo motors that belong to the
           pseudo motor system from the positions of the physical motors."""
        slit_1, slit_2 = physicals

        gap = slit_2 - slit_1
        pos = (slit_2 + slit_1)/2

        return (pos, gap)

    def CalcAllPhysical(self, pseudos, physicals):
        """Calculates the positions of all motors that belong to the pseudo
           motor system from the positions of the pseudo motors."""
        pos, gap = pseudos

        #lit_1 = 2*pos -slit_2 = 2*pos - gap -slit_1

        slit_1 = pos - gap / 2
        slit_2 = gap / 2 + pos

        return (slit_1, slit_2)
