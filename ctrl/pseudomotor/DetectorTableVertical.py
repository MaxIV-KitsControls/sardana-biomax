###############################################################################
# #     Alignment table controllers for Biomax.
# #
# #     Copyright (C) 2015  MAX IV Laboratory, Lund Sweden.
# #
# #     This program is free software: you can redistribute it and/or modify
# #     it under the terms of the GNU General Public License as published by
# #     the Free Software Foundation, either version 3 of the License, or
# #     (at your option) any later version.
# #
# #     This program is distributed in the hope that it will be useful,
# #     but WITHOUT ANY WARRANTY; without even the implied warranty of
# #     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# #     GNU General Public License for more details.
# #
# #     You should have received a copy of the GNU General Public License
# #     along with this program.  If not, see [http://www.gnu.org/licenses/].
###############################################################################
import math

from sardana.pool.controller import PseudoMotorController


class DetectorTableVertical(PseudoMotorController):
    """
    A pseudo motor controller for handling distance and angle.
    The system uses three real motors tab2_z, tab2_y1 and tab2_y2.
    """
    L = 315.5  # mm
    HX = 73  # mm
    HZ = 428.25  # mm

    gender = "Detector support Table"
    model = "Alignment Table Vertical axis pseudo"
    organization = "Max IV"

    pseudo_motor_roles = ("distance", "angle")
    motor_roles = ("pos_z", "pos_y1", "pos_y2")

    def CalcPhysical(self, index, pseudos, physicals):
        return self.CalcAllPhysical(pseudos, physicals)[index - 1]

    def CalcPseudo(self, index, physicals, pseudos):
        return self.CalcAllPseudo(physicals, pseudos)[index - 1]

    def CalcAllPhysical(self, pseudos, physicals):
        distance, angle = pseudos

        pos_z = (distance + self.HX) * math.cos(math.radians(angle)) + self.HZ * math.sin(math.radians(angle))

        # x = pos_z + self.L / 2

        pos_y1 = (distance + self.HX) * math.sin(math.radians(angle)) + self.HZ * (1 - math.cos(math.radians(angle)))

        pos_y2 = pos_y1 + self.L * math.tan(math.radians(angle))

        return (pos_z, pos_y1, pos_y2)

    def CalcAllPseudo(self, physicals, pseudos):
        pos_z, pos_y1, pos_y2 = physicals

        angle = math.atan(pos_y1 / pos_z)

        distance = math.sqrt(pos_z**2 + pos_y1**2) - self.HX - self.HZ * math.tan(angle)

        return (distance, math.degrees(angle))
