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

        ___________________________________
        |   fine translation:  kx,ky,kz   |
        |   fine tilt: kx_tilt, kz_tilt   |
        ===================================
        |   air-bearing rotation: rot     |
        ===================================
        |  coarse translation below Aero: | 
        |     x_base, y_base, z_base      |
        -----------------------------------

    """

    #   TODO:
    #   update with acutal PV
    kx      = Component(EpicsMotor, "$TRKX_PV", name='kx_trans')  # x motion with kohzu stage
    ky      = Component(EpicsMotor, "$TRKY_PV", name='ky_trans')  # y motion with kohzu stage
    kz      = Component(EpicsMotor, "$TRKZ_PV", name='kz_trans')  # z motion with kohzu stage
    kx_tilt = Component(EpicsMotor, "$TTKX_PV", name='kx_tilt')   # kohzu tilt motion along x
    kz_tilt = Component(EpicsMotor, "$TTKZ_PV", name='kz_tilt')   # kohzu tilt motion along z

    rot     = Component(EpicsMotor, "$ROT_PV", name='rot_y'  )    # rotation with aero stage

    x_base  = Component(EpicsMotor, "$TRX_PV", name='x_trans')    # x motion below aero stage
    y_base  = Component(EpicsMotor, "$TRY_PV", name='y_trans')    # y motion below aero stage
    z_base  = Component(EpicsMotor, "$TRZ_PV", name='z_trans')    # z motion below aero stage

    @property
    def status(self):
        """return full pv list and corresponding values"""
        # TODO:
        #   once acutal PVs are known, the implementation should go here
        #   my thought is to list useful PV status for users,
        #   a full list should be implemented in the Ultima for dev     /JasonZ
        #   Maybe print StateAero.position_cached ?
        pass

    def cache_position(self):
        """quickly cache all motor positions"""
        #   Add other motors if any (i.e. Kohzu tilt)
        # TODO:
        #   We need to consider what to do when cached positions are not the same
        #   as the physical positions when a motor is manually moved
        self.position_cached = {
            "kx"       : self.kx.position,
            "ky"       : self.ky.position,
            "kz"       : self.kz.position,
            "kx_tilt"  : self.kx_tilt.position,
            "kz_tilt"  : self.kz_tilt.position,

            "rot"      : self.rot.position   ,

            "x_base"   : self.x_base.position ,
            "y_base"   : self.y_base.position ,
            "z_base"   : self.z_base.position ,
        }

    def resume_position(self):
        """move motors to previously cached position"""
        #   Add other motors if any (i.e. Kohzu tilt)
        self.kx.mv(self.position_cached['kx'])
        self.ky.mv(self.position_cached['ky'])
        self.kz.mv(self.position_cached['kz'])
        self.kx_tilt.mv(self.position_cached['kx_tilt'])
        self.kz_tilt.mv(self.position_cached['kz_tilt'])

        self.rot.mv(self.position_cached['rot'])

        self.x_base.mv(self.position_cached['x_base'])
        self.y_base.mv(self.position_cached['y_base'])
        self.z_base.mv(self.position_cached['z_base'])


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