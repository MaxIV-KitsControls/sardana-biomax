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


class AlignmentTableVertical(PseudoMotorController):
    """
    A pseudo motor controller for handling vertical motors of
    the Alignment Table. The system uses two
    real motors tab1_y1 and tab1_y2.
    """
    Z1Z2 = 1070  # mm

    gender = "Support Table"
    model = "Alignment Table Vertical axis pseudo"
    organization = "Max IV"

    pseudo_motor_roles = ("pos_y", "pitch")
    motor_roles = ("mot1", "mot2")

    def CalcPhysical(self, index, pseudos, curr_physical):
        return self.CalcAllPhysical(pseudos, curr_physical)[index - 1]

    def CalcPseudo(self, index, physicals, pseudos):
        return self.CalcAllPseudo(physicals, pseudos)[index - 1]

    def CalcAllPhysical(self, pseudos, curr_physical):
        pos_y, pitch = pseudos

        pitch = math.radians(pitch)
        mot1 = pos_y + math.tan(pitch) * self.Z1Z2 / 2
        mot2 = pos_y - math.tan(pitch) * self.Z1Z2 / 2

        return (mot1, mot2)

    def CalcAllPseudo(self, physicals, pseudos):
        mot1, mot2 = physicals

        pos_y = (mot1 + mot2) / 2
        pitch = math.degrees(math.atan((mot1 - mot2) / self.Z1Z2))

        return (pos_y, pitch)


class AlignmentTableHorizontal(PseudoMotorController):
    """
    A pseudo motor controller for handling horizontal motors of
    the Alignment Table. The system uses two
    real motors tab1_x1 and tab1_x2.
    """
    Y1Y2 = 1070  # mm

    gender = "Support Table"
    model = "Alignment Table Horizontal axis pseudo"
    organization = "Max IV"

    pseudo_motor_roles = ("pos_x", "yaw")
    motor_roles = ("mot1", "mot2")

    def CalcPhysical(self, index, pseudos, physicals):
        return self.CalcAllPhysical(pseudos, physicals)[index - 1]

    def CalcPseudo(self, index, physicals, pseudos):
        return self.CalcAllPseudo(physicals, pseudos)[index - 1]

    def CalcAllPhysical(self, pseudos, physicals):
        pos_x, yaw = pseudos

        yaw = math.radians(yaw)

        mot1 = pos_x - math.tan(yaw) * self.Y1Y2 / 2
        mot2 = pos_x + math.tan(yaw) * self.Y1Y2 / 2

        return (mot1, mot2)

    def CalcAllPseudo(self, physicals, pseudos):
        mot1, mot2 = physicals

        pos_x = (mot1 + mot2) / 2
        yaw = math.degrees(math.atan((mot2 - mot1) / self.Y1Y2))

        return (pos_x, yaw)
