#!/usr/bin/env python

"""
This module contains motors customized for APS-MPE group.

TODO:
* The motor controls here also include those defined through FPGA.
* Additional work is required once the acutal PVs are knwon.
"""


from ophyd   import Device
from ophyd   import MotorBundle
from ophyd   import Component
from ophyd   import EpicsMotor
from ophyd   import EpicsSignal
from ophyd   import EpicsSignalRO


class StageAero(MotorBundle):
    """
    Motor stacks used for HT-HEDM

        _______________________________
        | fine translation:  kx,ky,kz |
        ===============================
        | air-bearing rotation: rot   |
        ===============================
        | coarse translation: x, y, z |
        -------------------------------
    TODO:
        We may have Kouzu stages for tilt, need to check this.

    """

    #   TODO:
    #   update with acutal PV
    kx_trans = Component(EpicsMotor, "$TRKX_PV", name='kx_trans')  # x motion with kohzu stage
    ky_trans = Component(EpicsMotor, "$TRKY_PV", name='ky_trans')  # y motion with kohzu stage
    kz_trans = Component(EpicsMotor, "$TRKZ_PV", name='kz_trans')  # z motion with kohzu stage

    rot_y    = Component(EpicsMotor, "$ROT_PV", name='rot_y'  )  # rotation with aero stage
    x_trans  = Component(EpicsMotor, "$TRX_PV", name='x_trans')  # x motion with aero stage
    y_trans  = Component(EpicsMotor, "$TRY_PV", name='y_trans')  # y motion with aero stage
    z_trans  = Component(EpicsMotor, "$TRZ_PV", name='z_trans')  # z motion with aero stage

    @property
    def status(self):
        """return full pv list and corresponding values"""
        # TODO:
        #   once acutal PVs are known, the implementation should go here
        #   my thought is to list useful PV status for users,
        #   a full list should be implemented in the Ultima for dev     /JasonZ
        pass

    def cache_position(self):
        """quickly cache all motor positions"""
        #   Add other motors if any (i.e. Kohzu tilt)
        # TODO:
        #   We need to consider what to do when cached positions are not the same
        #   as the physical positions when a motor is manually moved
        #   calibrate in medm?      /JasonZ
        self.position_cached = {
            "kx_trans": self.kx_trans.position,
            "ky_trans": self.ky_trans.position,
            "kz_trans": self.kz_trans.position,
            "rot_y":    self.rot_y.position   ,
            "x_trans ": self.x_trans.position ,
            "y_trans ": self.y_trans.position ,
            "z_trans ": self.z_trans.position ,
        }

    def resume_position(self):
        """move motors to previously cached position"""
        #   Add other motors if any (i.e. Kohzu tilt)
        self.kx_trans.mv(self.position_cached['kx_trans'])
        self.ky_trans.mv(self.position_cached['ky_trans'])
        self.kz_trans.mv(self.position_cached['kz_trans'])
        self.rot_y.mv(   self.position_cached['rot_y'   ])
        self.x_trans .mv(self.position_cached['x_trans '])
        self.y_trans .mv(self.position_cached['y_trans '])
        self.z_trans .mv(self.position_cached['z_trans '])


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
    delta_time          = Component(EpicsSignalRO, "deltaTime"   )
    detector_setup_time = Component(EpicsSignal,   "detSetupTime")
    pulse_type          = Component(EpicsSignal,   "pulseType"   )
    scan_control        = Component(EpicsSignal,   "scanControl" )
    

if __name__ == "__main__":
    # example usage
    tomostage = StageAero(name='tomostage')
    psofly = EnsemblePSOFlyDevice("acutal PV prefix", name="psofly")