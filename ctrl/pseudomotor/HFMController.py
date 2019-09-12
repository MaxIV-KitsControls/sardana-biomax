###############################################################################
##    Mirror controllers for Biomax. 
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


class HFMPosition(PseudoMotorController):
    """A pseudo motor controller for handling x and yaw pseudo
       motors of the Horizontal Focusing Mirror. The system uses to real motors mirxx and mirxx."""

    gender = "Mirror"
    model = "Horizontal Focusing Mirror"
    organization = "Max IV"

    pseudo_motor_roles = ("mir1x", "mir1yaw")
    motor_roles = ("mir1x1", "mir1x2")

    def CalcPhysical(self, index, pseudos, physicals):
        return self.CalcAllPhysical(pseudos, physicals)[index - 1]

    def CalcPseudo(self, index, physicals, pseudos):
        return self.CalcAllPseudo(physicals, pseudos)[index - 1]

    def CalcAllPhysical(self, pseudos, physicals):
        hfm_x, hfm_yaw = pseudos
        return (hfm_x, hfm_yaw)

    def CalcAllPseudo(self, physicals, pseudos):
        hfm_x1, hfm_x2 = physicals

        return (hfm_x1, hfm_x2)
