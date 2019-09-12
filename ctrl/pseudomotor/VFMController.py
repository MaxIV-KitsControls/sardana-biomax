###############################################################################
##     Mirror controllers for Biomax. 
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
from sardana.pool.controller import PseudoMotorController
from sardana.pool.controller import Type
from sardana.pool.controller import Description

VFM_XDISTANCE = 0.472
VFM_YDISTANCE = 0.4975
VFM_Y2Y3DISTANCE =  0.260

class VFMXYaw(PseudoMotorController):
    """A pseudo motor controller for handling x and yaw pseudo 
       motors of the Vertical Focusing Mirror. The system uses to real motors mir1x1 (vfm_x1) and mir1x2(vfm_x2)."""

    gender = "Mirror"
    model = "Vertical Focusing Mirror Horizontal Movement"
    organization = "Max IV"

    pseudo_motor_roles = ("vfm_x", "vfm_yaw")
    motor_roles = ("vfm_x1", "vfm_x2")

    def CalcPhysical(self, index, pseudos, physicals):
        return self.CalcAllPhysical(pseudos, physicals)[index - 1]

    def CalcPseudo(self, index, physicals, pseudos):
        return self.CalcAllPseudo(physicals, pseudos)[index - 1]

    def CalcAllPhysical(self, pseudos, physicals):
        x, yaw = pseudos
        vfm_xdistance = VFM_XDISTANCE

        #vfm_x1 = 2*x -vmf_x2 = 2*x -yaw*vfm_xdistance - vfm_x1
        vfm_x1 = x - (yaw * vfm_xdistance) / 2

        #vfm_x2 = yaw*vfm_xdistance + vfm_x1 = yaw*vfm_xdistance + x -(yaw*vfm_xdistance)/2
        vfm_x2 = x + (yaw * vfm_xdistance) / 2

        return (vfm_x1, vfm_x2)

    def CalcAllPseudo(self, physicals, pseudos):
        vfm_x1, vfm_x2 = physicals
        vfm_xdistance = VFM_XDISTANCE

        vfm_x = (vfm_x1 + vfm_x2) / 2
        vfm_yaw = (vfm_x2 - vfm_x1) / vfm_xdistance

        return (vfm_x, vfm_yaw)


class VFMYPitchRoll(PseudoMotorController):
    """A pseudo motor controller for handling y, pitch and roll pseudo 
       motors of the Vertical Focusing Mirror. The system uses to real motors mir1y1, mir1y2 and mir1y3 
       ("vfm_y1", "vfm_y2", "vfm_y3")."""

    gender = "Mirror"
    model = "Vertical Focusing Mirror Vertical Movement"
    organization = "Max IV"

    pseudo_motor_roles = ("vfm_y", "vfm_pit", "vfm_rol")
    motor_roles = ("vfm_y1", "vfm_y2", "vfm_y3")

    def CalcPhysical(self, index, pseudos, physicals):
        return self.CalcAllPhysical(pseudos, physicals)[index - 1]

    def CalcPseudo(self, index, physicals, pseudos):
        return self.CalcAllPseudo(physicals, pseudos)[index - 1]

    def CalcAllPhysical(self, pseudos, physicals):
        vfm_y, vfm_pit, vfm_rol = pseudos

        vfm_ydistance = VFM_YDISTANCE
        vfm_y2y3distance = VFM_Y2Y3DISTANCE

        vfm_y1 = vfm_y + vfm_pit * vfm_ydistance / 2
        vfm_y2 = vfm_rol * vfm_y2y3distance / 2 + vfm_y - vfm_pit * vfm_ydistance / 2
        vfm_y3 = vfm_y - vfm_pit * vfm_ydistance / 2 - vfm_rol * vfm_y2y3distance / 2

        return (vfm_y1, vfm_y2, vfm_y3)

    def CalcAllPseudo(self, physicals, pseudos):
        vfm_y1, vfm_y2, vfm_y3 = physicals

        vfm_ydistance = VFM_YDISTANCE
        vfm_y2y3distance = VFM_Y2Y3DISTANCE

        vfm_y = (vfm_y1 + (vfm_y2 + vfm_y3)/2)/2
        vfm_pit = (-(vfm_y2 + vfm_y3) / 2 + vfm_y1) / vfm_ydistance
        vfm_rol = (vfm_y2 - vfm_y3) / vfm_y2y3distance

        return (vfm_y, vfm_pit, vfm_rol)
