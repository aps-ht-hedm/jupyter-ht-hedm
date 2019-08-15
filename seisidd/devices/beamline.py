#!/usr/bin/env python

"""
This module contains beamline specific control macros and functions.
"""

from ophyd   import MotorBundle
from ophyd   import EpicsMotor
from ophyd   import Component


class Slits(MotorBundle):
    """Control the four blades that form the beam"""

    left   = Component(EpicsMotor, "PV_left",   name='left'  )
    right  = Component(EpicsMotor, "PV_right",  name='right' )
    top    = Component(EpicsMotor, "PV_top",    name='top'   )
    bottom = Component(EpicsMotor, "PV_bottom", name='bottom')


class Attenuator:
    """Attenuator control"""
    # TODO:
    #   Lack of sufficient information to implement
    #   * set_atten() ?? 
    pass


class Beam:
    """Provide full control of the beam."""

    def __init__(self):
        self.slits = Slits(name='slits')
        self.atten = Attenuator()         # adjustment needed

    @property
    def status(self):
        """Return full beam status"""
        pass

    @property
    def center(self):
        """return estimated center based on slits positions"""
        pass


class EnergyFoil:
    """Energy foil"""
    # TODO:
    #   Requir acutal implementation once the nature of the device is known
    pass


class Counter:
    """Counter"""
    pass


class FastShutter:
    """Fast shutter for taking dark field images"""
    # NOTE:
    #  apstoos provides shutter class for the main/slow beamline shutter,
    #  which can be used as a reference when defining the fast shutter
    pass


if __name__ == "__main__":
    pass