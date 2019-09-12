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


class Energy(PseudoMotorController):
    """
    Energy pseudo motor controller for handling energy calculation given the positions
    of all the motors involved (and viceversa).
    TODO: at this stage x2per is not updated
    """
    gender = "Energy"
    model = "HDCM Energy"
    organization = "Max IV"

    pseudo_motor_roles = ("mono_energy",)
    # Bragg angle or Goniometer actuator, 2nd Crystal Motorised Perpendicular Translation (Tx)
    motor_roles = ("mono_bragg", "mono_x2per")

    # energy2wavelength
    # E = hc/lambd = h*c*c1 /e*lambda  = 12398.41856/lambda

    class_prop = {'h': {'Type': 'PyTango.DevDouble',
                        'Description': 'planck, [Js]',
                        'DefaultValue': 6.62606957E-34
                        },
                  'c': {'Type': 'PyTango.DevDouble',
                        'Description': 'light, [m/s]',
                        'DefaultValue': 2.99792458E+8
                        },
                  'hc': {'Type': 'PyTango.DevDouble',
                         'Description': 'planck*light',
                         'DefaultValue': 12398.41856
                         },
                  'c1': {'Type': 'PyTango.DevDouble',
                         'Description': 'Amstrong conversion factor',
                         'DefaultValue': 1E10
                         },
                  'e': {'Type': 'PyTango.DevDouble',
                        'Description': 'electron charge [C]',
                        'DefaultValue': 1.602146565E-19
                        },
                  'dist': {'Type': 'PyTango.DevDouble',
                           'Description': '2d, distance crystal planse Si(111), [Amstrong]',
                           'DefaultValue': 6.2712
                           },
                  'off': {'Type': 'PyTango.DevDouble',
                          'Description': 'horizontal beam offset, h = 2a*cos(bragg), [mm]',
                          'DefaultValue': 10
                          },
                  }

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
    # def getAxisPar(self, axis, name):
    #     name = name.lower()
    #     if name == 'update_x2per':
    #         return self.update_x2per

    # def setAxisPar(self, axis, name, value):
    #     name = name.lower()
    #     if name == 'update_x2per':
    #         self.update_x2per = value

    def CalcPseudo(self, index, physicals, curr_pseudo_pos):
        return self.CalcAllPseudo(physicals, curr_pseudo_pos)[index - 1]

    def CalcPhysical(self, index, pseudos, curr_physical_pos):
        return self.CalcAllPhysical(pseudos, curr_physical_pos)[index - 1]

    def CalcAllPhysical(self, pseudos, curr_physical_pos):
        mono_energy = pseudos[0]
        self._log.info('energy: %f', mono_energy)
        self._log.info('phys1: %f', curr_physical_pos[0])
        self._log.info('phys2: %f', curr_physical_pos[1])

#        bragg = math.asin(self.hc/(self.dist*self.e*mono_energy))*1000 #*1000 to mrad
        if mono_energy == 0:
            bragg = 0
        else:
            bragg = math.degrees(math.asin(self.hc / (self.dist * mono_energy))) #*1000 to mrad

        x2per = self.off/(2*(math.cos((bragg)*(math.pi/180))))

        #x2per = curr_physical_pos[1]
        return (bragg, x2per)

    def CalcAllPseudo(self, physicals, curr_pseudo_pos):
        mono_bragg, mono_x = physicals

        if mono_bragg == 0:
            energy = 0
        else:
            energy = math.fabs(self.hc / (self.dist * math.cos(math.radians(90 - mono_bragg)))) #/1000 to rad

        return (energy,)


class Wavelength(PseudoMotorController):
    """
    Wavelength pseudo motor controller for handling energy/wavelength conversion
    """
    gender = "Energy"
    model = "HDCM Wavelength"
    organization = "Max IV"

    pseudo_motor_roles = ("wavelength",)
    motor_roles = ("mono_bragg", "mono_x2per")


    class_prop = {'h':{'Type':'PyTango.DevDouble',
                 'Description':'planck, [Js]',
                 'DefaultValue':6.62606957E-34
                    },
                  'c':{'Type':'PyTango.DevDouble',
                 'Description':'light, [m/s]',
                 'DefaultValue':2.99792458E+8
                    },
                  'hc':{'Type':'PyTango.DevDouble',
                 'Description':'planck*light',
                 'DefaultValue':12398.41856
                    },  
                  'c1':{'Type':'PyTango.DevDouble',
                 'Description':'Amstrong conversion factor',
                 'DefaultValue':1E10
                    },
                   'e':{'Type':'PyTango.DevDouble',
                 'Description':'electron charge [C]',
                 'DefaultValue':1.602146565E-19
                    },
                  'dist':{'Type':'PyTango.DevDouble',
                 'Description':'2d, distance crystal planse Si(111), [Amstrong]',
                 'DefaultValue':6.2712
                    },
                  'off':{'Type':'PyTango.DevDouble',
                 'Description':'horizontal beam offset, h = 2a*cos(bragg), [mm]',
                 'DefaultValue':10
                },
                }
    axis_extra_attributes = {"DiffrOrder":
                              {'Type':'PyTango.DevDouble',
                               'R/W Type':'PyTango.READ_WRITE',
                               'DefaultValue':1.0
                                  },
                            }


    def CalcPhysical(self, index, pseudos, curr_physical_pos):
        return self.CalcAllPhysical(pseudos, curr_physical_pos)[index - 1]

    def CalcPseudo(self, index, physicals, curr_pseudo_pos):
        return self.CalcAllPseudo(physicals, curr_pseudo_pos)[index - 1]

    def CalcAllPhysical(self, pseudos, curr_physical_pos):
        wavelength, = pseudos

#        bragg = math.asin(self.hc/(self.dist*self.e*mono_energy))*1000 #*1000 to mrad
        if wavelength == 0:
            mono_energy = 0
            bragg = 0
        else:
            mono_energy = (self.hc / wavelength)
            bragg = math.asin(self.hc / (self.dist * mono_energy)) * 180 / math.pi  # *1000 to mrad

        x2per = self.off / 2 * math.cos(bragg)

        return (bragg, x2per)

    def CalcAllPseudo(self, physicals, curr_pseudo_pos):
        mono_bragg, mono_x = physicals

        if mono_bragg == 0:
            wavelength = 0
        else:
            energy = math.fabs(self.hc / (self.dist * math.cos((90 - mono_bragg) * math.pi / 180)))
            # /1000 to rad
            wavelength = (self.hc / energy)
        return (wavelength,)
