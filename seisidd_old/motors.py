#!/usr/bin/env python

"""
This module contains motors customized for APS-MPE group.

NOTE:
    The current design of Ophyd encourages hardwaring PVs
    into the source code.  Therefore, we are hard-coding all
    PVs into the associated class definition.
    Also, the current PVs are for devices at 6BM, which need to
    be switched to 6-ID-D for HT-HEDM.
"""

from ophyd   import Device
from ophyd   import MotorBundle
from ophyd   import Component
from ophyd   import EpicsMotor
from ophyd   import EpicsSignal
from ophyd   import EpicsSignalRO

import bluesky.plan_stubs as bps


# ----- Motors ----- #
class TomoStage(MotorBundle):
    # TODO:
    #    Need to find the missing PVs
    # TODO:
    #    Use more meaningful name for motor PVs instead of numbers
    #    This would simplify the interface a lot.
    preci = Component(EpicsMotor, "6bmpreci:m1", name='preci')  # rotation
    samX  = Component(EpicsMotor, "6bma1:m19",   name='samX' )  # coarse motor
    ksamX = Component(EpicsMotor, "6bma1:m11",   name='ksamX')  # fine motor
    samY  = Component(EpicsMotor, "6bma1:m18",   name="samY" )  # coarse motor
    #ksamY = Component(EpicsMotor, "?",   name="ksamY" )
    #samZ  = Component(EpicsMotor, "?",   name="samZ" )
    ksamZ = Component(EpicsMotor, "6bma1:m12",   name='ksamZ')  # fine motor


# ----- Flyscan interface ----- #
# NOTE:
class TaxiFlyScanDevice(Device):
    """
    BlueSky Device for APS taxi & fly scans
    
    Some EPICS fly scans at APS are triggered by a pair of 
    EPICS busy records. The busy record is set, which triggers 
    the external controls to do the fly scan and then reset 
    the busy record. 
    
    The first busy is called taxi and is responsible for 
    preparing the hardware to fly. 
    The second busy performs the actual fly scan. 
    In a third (optional) phase, data is collected 
    from hardware and written to a file.
    """
    taxi = Component(EpicsSignal, "taxi", put_complete=True)
    fly = Component(EpicsSignal, "fly", put_complete=True)
    
    def plan(self):
        yield from bps.mv(self.taxi, self.taxi.enum_strs[1])
        yield from bps.mv(self.fly, self.fly.enum_strs[1])


class EnsemblePSOFlyDevice(TaxiFlyScanDevice):
    """
    PSOfly control wrapper
    """
    motor_pv_name = Component(EpicsSignalRO, "motorName")
    start         = Component(EpicsSignal,   "startPos")
    end           = Component(EpicsSignal,   "endPos")
    slew_speed    = Component(EpicsSignal,   "slewSpeed")

    # scan_delta: output a trigger pulse when motor moves this increment
    scan_delta = Component(EpicsSignal, "scanDelta")

    # advanced controls
    delta_time = Component(EpicsSignalRO, "deltaTime")
    # detector_setup_time = Component(EpicsSignal, "detSetupTime")
    # pulse_type = Component(EpicsSignal, "pulseType")

    scan_control = Component(EpicsSignal, "scanControl")


if __name__ == "__main__":
    tomostage = TomoStage(name='tomostage')
    print(tomostage.preci)
    psofly = EnsemblePSOFlyDevice("6bmpreci:eFly:", name="psofly")
