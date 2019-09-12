###############################################################################
##     Energy and wavelength controllers for Biomax.
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
from sardana.pool.controller import DefaultValue
from sardana.pool.controller import DataAccess
from sardana.pool.controller import Access
from PyTango import *

import math
import numpy as np


# coefficients of the Al/Ti polynomial model obtained by least squares
# minimization between experimentally determined and fitted attenuation
# lenghts (in um) as a function of photon energy (in keV)
Al_coeff = [ 2.70033918627e-07, -2.98687890398e-05, \
            0.00123604226164, -0.0258445478508, \
            0.443366527092, -1.88717819273, \
            6.51896436249, -8.15712686311 ]

Ti_coeff = [-2.1861658157e-06, 0.00012895778718, \
            0.013506837223, 0.0575801845364, \
            -0.126481012773, 0.569768177628 ]

# Al/Ti models for calculating att. lenght (in um) as a function of E (in keV)
Al_model, Ti_model = np.array(Al_coeff), np.array(Ti_coeff)

# bcu wheel lengths:
bcu_att1_lengths = [float(l) for l in range(0, 600, 60)]
bcu_att2_lengths = [float(l) for l in range(0, 750, 75)]
bcu_att3_lengths = [float(l) for l in range(0, 60, 6)]


# define the bcu_wheel class
class bcu_wheel(object):
    '''
    contains all the information about a bcu_wheel such as:
    position - an integer from 0 to 9
    angles - a list of floats: all available wheel angles (positions)
    lengths - an array of lengths (thicknesses) at each wheel position
    transmission - an array of floats (0,1]: transmission values for the given energy
    energy - a float: the energy of the X-rays (in keV)
    model - the model coeff for the wheel material (for calculating att. length)
    att_l - a float: the att. length of the material for the given energy
    '''
    def __init__(self, lengths, model, energy):
        '''
        initializes the bcu_wheel object: sets the position to 0,
        calculates the att_l and the transmission values for the given energy
        lengths - a list of floats (available lengths in um)
        model - a np.array of model coefficients
        energy - a float (in keV)
        '''
        self.energy = energy
        self.lengths = np.array(lengths)
        self.model = model
        self.position = 0
        self.angles = [float(a) for a in range(0, 360, 36)]
        self.att_l = np.polyval(self.model, self.energy)
        self.transmission = np.exp(-self.lengths/self.att_l)

    def set_position(self, new_position):
        '''
        new_position - an integer between 0 and 9
        '''
        assert type(new_position) == int, 'wrong input type. position must be an int'
        assert new_position <= 9 and new_position >= 0, 'new position out of range'
        self.position = new_position

    def set_energy(self, new_energy):
        '''
        updates the value of the energy, recalculates the att. length and the
        transmission values
        '''
        assert new_energy <= 30.0 and new_energy >= 5.0, 'new energy value out of range'
        self.energy = new_energy
        self.att_l = np.polyval(self.model, self.energy)
        self.transmission = np.exp(-self.lengths/self.att_l)

    def get_position(self):
        return self.position

    def get_angle(self):
        return self.angles[self.position]

    def get_transmission(self):
        return self.transmission[self.position]



class Transmission(PseudoMotorController):
    """
    Energy pseudo motor controller for handling energy calculation given the positions
    of all the motors involved (and viceversa).
    TODO: at this stage x2per is not updated
    """
    gender = "Transmission"
    model = "BCU Transmission"
    organization = "Max IV"

    pseudo_motor_roles = ("bcu_transmission",)
    # Bragg angle or Goniometer actuator, 2nd Crystal Motorised Perpendicular Translation (Tx)
    motor_roles = ("bcu_att1", "bcu_att2", "bcu_att3")

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        self.energy_attr = None
        self.bcu_att1_wheel = None
        self.bcu_att2_wheel = None
        self.bcu_att3_wheel = None

    def initialize_proxy(self):
        '''Energy motor migth not be ready during __init__'''
        self.energy_attr = AttributeProxy('b311a-o/opt/mono-ener/Position')
        E = self.energy_attr.read().value / 1000  # to keV
        E = float("{0:.3f}".format(E))
        # construct the 3 bcu_att wheels
        # bcu_att1: Al
        self.bcu_att1_wheel = bcu_wheel(bcu_att1_lengths, Al_model, E)
        # bcu_att2: Ti
        self.bcu_att2_wheel = bcu_wheel(bcu_att2_lengths, Ti_model, E)
        # bcu_att3: Al
        self.bcu_att3_wheel = bcu_wheel(bcu_att3_lengths, Al_model, E)

    def set_all_positions(self, p1, p2, p3):
        '''
        sets all the three wheels to positions p1, p2, and p3
        '''
        self.bcu_att1_wheel.set_position(p1)
        self.bcu_att2_wheel.set_position(p2)
        self.bcu_att3_wheel.set_position(p3)
        
    def get_tot_transmission(self):
        '''
        gets the total combined transmission for the given wheel configuration
        and energy value
        '''
        tot_trans = self.bcu_att1_wheel.get_transmission() * \
                    self.bcu_att2_wheel.get_transmission() * \
                    self.bcu_att3_wheel.get_transmission() * 100.0
        return tot_trans
        
    def set_transmission(self, transmission, E):
        '''
        sets the transmission for the specified E
        transmission - a float (transmission in %)
        E - a float (photon energy in keV)

        returns a tuple of a tuple of the 3 bcu_att wheel angles (in degrees)
        and the true value of the transmission (in %):
        ((bcu_att1, bcu_att2, bcu_att3), act_trans)
        '''
        # a brute force algorithm for finding the wheel combination that best matches
        # the desired transmission for the given X-ray energy
        # the starting positions of all 3 wheels are  0
        pos = [0, 0, 0]
        best_trans = 100.0
        # test all wheel position combinations and pick the best one
        for p1 in range(10):
            for p2 in range(10):
                for p3 in range(10):
                    # set the wheels to the desired positions and
                    # calculate the total transmission
                    self.set_all_positions(p1, p2, p3)
                    tot_trans = self.get_tot_transmission()
                    if abs(transmission - tot_trans) < abs(transmission - best_trans):
                        best_trans = tot_trans
                        pos = [p1, p2, p3]

        # set the wheels to the optimal positions and get the value of the
        # actual total transmission and the angles of the 3 wheels
        self.set_all_positions(pos[0], pos[1], pos[2])
        actual_trans = self.get_tot_transmission()
        angles = (self.bcu_att1_wheel.get_angle(), self.bcu_att2_wheel.get_angle(), self.bcu_att3_wheel.get_angle())
        return (angles, actual_trans)

    def CalcPseudo(self, index, physicals, curr_pseudo_pos):
        return self.CalcAllPseudo(physicals, curr_pseudo_pos)[index - 1]

    def CalcPhysical(self, index, pseudos, curr_physical_pos):
        return self.CalcAllPhysical(pseudos, curr_physical_pos)[index - 1]

    def CalcAllPhysical(self, pseudos, curr_physical_pos):
        transmission = pseudos[0]  # [%]

        current_energy = self.energy_attr.read().value / 1000  # to keV
        current_energy = float("{0:.3f}".format(current_energy))

        # update the wheel transmission based on current energy
        if self.bcu_att1_wheel.energy != current_energy:
            self.bcu_att1_wheel.set_energy(current_energy)
            self.bcu_att2_wheel.set_energy(current_energy)
            self.bcu_att3_wheel.set_energy(current_energy)

        angles, actual_trans = self.set_transmission(transmission, current_energy)

        return angles  #deg


    def CalcAllPseudo(self, physicals, curr_pseudo_pos):
        if self.energy_attr is None:
            self.initialize_proxy()
        bcu_att1, bcu_att2, bcu_att3 = physicals
        current_energy = self.energy_attr.read().value / 1000
        current_energy = float("{0:.3f}".format(current_energy))
        print bcu_att1, bcu_att2, bcu_att3, current_energy
        # make sure the energy setting of the wheels is correct and if not
        # update this parameter
        if self.bcu_att1_wheel.energy != current_energy:
            self.bcu_att1_wheel.set_energy(current_energy)
            self.bcu_att2_wheel.set_energy(current_energy)
            self.bcu_att3_wheel.set_energy(current_energy)
        
        # get the wheel positions from the motor angle values (round to the closest 36 degree increment)
        # then set the bcu wheels to those positions and return the total transmission for the whole
        # configuration and energy value
        def calc_pos(motor_angle):
            '''
            get the closest position for the given motor angle value
            '''
            if motor_angle > 342:
                position = 0
            elif motor_angle % 36 > 18:
                position = math.ceil(motor_angle / 36)
            else:
                position = math.floor(motor_angle / 36)
            return position

        # get all the wheel positions and set the wheels
        pos1, pos2, pos3 = calc_pos(bcu_att1), calc_pos(bcu_att2), calc_pos(bcu_att3)
        try:
            self.set_all_positions(int(pos1), int(pos2), int(pos3))
            transmission = self.get_tot_transmission()
        except Exception as ex:
            print ex
        return (transmission,)

