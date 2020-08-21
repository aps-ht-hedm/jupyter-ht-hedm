#!/usr/bin/env python

"""
This module contains motors customized for APS-MPE group.

TODO:
* The motor controls here also include those defined through FPGA.
* Additional work is required once the acutal PVs are knwon.
"""


from ophyd   import    Device
from ophyd   import    MotorBundle
from ophyd   import    Component
from ophyd   import    EpicsMotor
from ophyd   import    EpicsSignal
from ophyd   import    EpicsSignalRO


class StageAero(MotorBundle):
    """
    Motor stacks used for HT-HEDM

        ___________________________________
        |   fine translation:  kx,ky,kz   |
        |   fine tilt: kx_tilt, kz_tilt   |
        ===================================
        |    air-bearing rotation: rot    |
        ===================================
        |  coarse translation below Aero: | 
        |     x_base, y_base, z_base      |
        -----------------------------------

    """

    #   TODO:
    #   update with acutal PV
    kx          = Component(EpicsMotor, "6idhedm:m42", name='kx_trans')  # x motion with kohzu stage
    ky          = Component(EpicsMotor, "6idhedm:m40", name='ky_trans')  # y motion with kohzu stage
    kz          = Component(EpicsMotor, "6idhedm:m41", name='kz_trans')  # z motion with kohzu stage
    kx_tilt     = Component(EpicsMotor, "6idhedm:m43", name='kx_tilt')   # kohzu tilt motion along x
    kz_tilt     = Component(EpicsMotor, "6idhedm:m44", name='kz_tilt')   # kohzu tilt motion along z

    rot         = Component(EpicsMotor, "6idhedms1:m1",  name='rot_y'  )    # rotation with aero stage

    x_base      = Component(EpicsMotor, "6idhedm:m37",  name='x_trans')    # x motion below aero stage
    tiltx_base  = Component(EpicsMotor, "6idhedm:m38",  name='tiltx_base')    # y motion below aero stage
    tiltz_base  = Component(EpicsMotor, "6idhedm:m39",  name='tiltz_base')    # z motion below aero stage

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
        """cache current motor positions"""
        #   Add other motors if any (i.e. Kohzu tilt)
        # TODO:
        #   We need to consider what to do when cached positions are not the same
        #   as the physical positions when a motor is manually moved
        self.position_cached = {
            "kx"            : self.kx.position,
            "ky"            : self.ky.position,
            "kz"            : self.kz.position,
            "kx_tilt"       : self.kx_tilt.position,
            "kz_tilt"       : self.kz_tilt.position,

            "rot"           : self.rot.position   ,

            "x_base"        : self.x_base.position ,
            "tiltx_base"    : self.tiltx_base.position ,
            "tiltz_base"    : self.tiltz_base.position ,
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
        self.tiltx_base.mv(self.position_cached['tiltx_base'])
        self.tiltx_base.mv(self.position_cached['tiltz_base'])

        
class TomoCamStage(MotorBundle):
    """
    Motor stacks used for Tomo Camera

        _____________
        |   Tomo Y  |
        =============
        |   Tomo X  |
        =============
        |   Tomo Z  |
        -------------

    """

    #   TODO:
    #   update with acutal set up
    tomoy          = Component(EpicsMotor, "6idhedm:m48", name='tomoy')  # x motion with kohzu stage
    tomox          = Component(EpicsMotor, "6idhedm:m45", name='tomox')  # y motion with kohzu stage
    tomoz          = Component(EpicsMotor, "6idhedm:m46", name='tomoz')  # z motion with kohzu stage
    
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
        """cache current motor positions"""
        #   Add other motors if any (i.e. Kohzu tilt)
        # TODO:
        #   We need to consider what to do when cached positions are not the same
        #   as the physical positions when a motor is manually moved
        self.position_cached = {
            "tomoy"            : self.tomoy.position,
            "tomox"            : self.tomox.position,
            "tomoz"            : self.tomoz.position,
        }
 

class NFCamStage(MotorBundle):
    """
    Motor stacks used for NF Camera
    To be determined
        _____________
        |   NF Y  |
        =============
        |   NF X  |
        =============
        |   NF Z  |
        -------------

    """

    #   TODO:
    #   update with acutal set up
#     tomoy          = Component(EpicsMotor, "6idhedm:m48", name='tomoy')  # x motion with kohzu stage
#     tomox          = Component(EpicsMotor, "6idhedm:m45", name='tomox')  # y motion with kohzu stage
#     tomoz          = Component(EpicsMotor, "6idhedm:m46", name='tomoz')  # z motion with kohzu stage
    
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
        """cache current motor positions"""
        #   Add other motors if any (i.e. Kohzu tilt)
        # TODO:
        #   We need to consider what to do when cached positions are not the same
        #   as the physical positions when a motor is manually moved
#         self.position_cached = {
#             "tomoy"            : self.tomoy.position,
#             "tomox"            : self.tomox.position,
#             "tomoz"            : self.tomoz.position,
#         }
        pass
    

    def resume_position(self):
        """move motors to previously cached position"""
        #   Add other motors if any (i.e. Kohzu tilt)
#         self.tomoy.mv(self.position_cached['tomoy'])
#         self.tomox.mv(self.position_cached['tomox'])
#         self.tomoz.mv(self.position_cached['tomoz'])
        pass
      

class SimStageAero(MotorBundle):
    """
    Simulated Motor stacks used for HT-HEDM
    i.e.:   6iddSIM:m1
    Sim motors assigned as follows:
        kx          = m1
        ky          = m2
        kz          = m3
        rot         = m4

        kx_tilt     = m16
        kz_tilt     = m16
        x_base      = m16
        tiltx_base  = m16
        tiltz_base  = m16

        ___________________________________
        |   fine translation:  kx,ky,kz   |
        |   fine tilt: kx_tilt, kz_tilt   |
        ===================================
        |    air-bearing rotation: rot    |
        ===================================
        |  coarse translation below Aero: | 
        |  x_base, tiltx_base, tiltz_base |
        -----------------------------------

    """

    #   TODO:
    #   update with acutal PV
    kx          = Component(EpicsMotor, "6iddSIM:m1", name='kx_trans')  # x motion with kohzu stage
    ky          = Component(EpicsMotor, "6iddSIM:m2", name='ky_trans')  # y motion with kohzu stage
    kz          = Component(EpicsMotor, "6iddSIM:m3", name='kz_trans')  # z motion with kohzu stage
    kx_tilt     = Component(EpicsMotor, "6iddSIM:m16", name='kx_tilt')   # kohzu tilt motion along x
    kz_tilt     = Component(EpicsMotor, "6iddSIM:m16", name='kz_tilt')   # kohzu tilt motion along z

    rot         = Component(EpicsMotor, "6iddSIM:m4",  name='rot_y'  )    # rotation with aero stage

    x_base      = Component(EpicsMotor, "6iddSIM:m16",  name='x_trans')    # x motion below aero stage
    tiltx_base  = Component(EpicsMotor, "6iddSIM:m16",  name='tiltx_trans')    # y motion below aero stage
    tiltz_base  = Component(EpicsMotor, "6iddSIM:m16",  name='tiltz_trans')    # z motion below aero stage

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
        """cache current motor positions"""
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
            "tiltx_base"   : self.tiltx_base.position ,
            "tiltz_base"   : self.tiltz_base.position ,
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
        self.tiltx_base.mv(self.position_cached['tiltx_base'])
        self.tiltz_base.mv(self.position_cached['tiltz_base'])


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
    fly  = Component(EpicsSignal, "fly",  put_complete=True)
#     slew_speed_max = Component(EpicsSignalRO, "slewSpeed.DRVH")
#     slew_speed_min = Component(EpicsSignalRO, "slewSpeed.DRVL")
    
    # TODO
    # hardwiring the PV for now, need to know how to access these information through Ophyd
#     slew_speed_max = EpicsSignalRO("6idhedms1:PSOFly1:slewSpeed.DRVH")
#     slew_speed_min = EpicsSignalRO("6idhedms1:PSOFly1:slewSpeed.DRVL")
    
    reset_fpga = EpicsSignal("6idMZ1:SG:BUFFER-1_IN_Signal.PROC", put_complete=True, name = 'reset_fpga')
    pso_state  = EpicsSignal("6idMZ1:SG:AND-1_IN1_Signal",        put_complete=True, name = 'pso_state')  # only accept str as its input
    
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