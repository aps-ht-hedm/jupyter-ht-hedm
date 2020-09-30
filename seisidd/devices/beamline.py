#!/usr/bin/env python

"""
This module contains beamline specific control macros and functions.
"""

from ophyd   import Device
from ophyd   import MotorBundle
from ophyd   import EpicsMotor
from ophyd   import Component
from ophyd   import EpicsSignal, EpicsSignalRO

from apstools.devices import ShutterBase


class MainShutter6IDD(ShutterBase):
    """
    Ophyd class for the main shutter at 6IDD
    
    NOTE:
    There is some dealy (>2s) during the opening and closing of the main shutter, therefore
    frequent toggling of the main shutter is highly discouraged.
    """

    open_signal  = Component(EpicsSignal, "AcO8")
    close_signal = Component(EpicsSignal, "AcO7")
    state_signal = EpicsSignalRO("PA:06ID:STA_D_SDS_OPEN_PL.VAL")
    delay_time   = 1.5  # seconds

    @property
    def state(self):
        return self.state_signal.get()
    
    def open(self, timeout=10):
        self.open_signal.put(1)  # send out open request
        if self.delay_time > 0:
            import time
            time.sleep(self.delay_time)
        if self.open_signal.get() == 1:
            self.open_signal.put(0)  # cancel the open request, shutter is open now

    def close(self, timeout=10):
        self.close_signal.put(1)  # send out the close request
        if self.delay_time > 0:
            import time
            time.sleep(self.delay_time)
        if self.close_signal.get() == 1:
            self.close_signal.put(0)  # cancle the close request, shutter is closed now


class SlitUpstream(MotorBundle):
    """Upstream slit that controls the four blades that form the beam"""
    #   The slit PVs are not meaningful at all, the actual name will depend on set up
    #   Here is the upstream slit PVs at 1-ID-E   ("motorPV.LVIO" for soft limit check) 
    #   1ide1:m20
    #   1ide1:m21
    #   1ide1:m22
    #   1ide1:m23
    #   didn't found actual control in the scripts, manually adjusted??

    h_ib    =   Component(EpicsMotor, "6idhedm:m4",                  name='h_ib'     )   # horizontal in board
    h_ob    =   Component(EpicsMotor, "6idhedm:m5",                  name='h_ob'     )   # horizontal out board
    # h_size  =   Component(EpicsMotor, "1ide1:Kohzu_E_upHsize.VAL",  name='h_size'   )   # horizontal size !!!!!need to check this
    v_tp    =   Component(EpicsMotor, "6idhedm:m2",                  name='v_tp'     )   # vertial top
    v_bt    =   Component(EpicsMotor, "6idhedm:m3",                  name='v_bt'     )   # vertial bottom
    # v_size  =   Component(EpicsMotor, "1ide1:Kohzu_E_upVsize.VAL",  name='v_size'   )   # vertical size !!!!!need to check this
        

class SlitDownstream(MotorBundle):
    """Downstream slit that controls the four blades that form the beam"""
    h_ib    =   Component(EpicsMotor, "6idhedm:m35",                 name='h_ib'     )
    h_ob    =   Component(EpicsMotor, "6idhedm:m36",                 name='h_ob'     )
    # h_size  =   Component(EpicsMotor, "1ide1:Kohzu_E_dnHsize.VAL",  name='h_size'   )   # horizontal size !!!!!need to check this
    v_tp    =   Component(EpicsMotor, "6idhedm:m33",                 name='v_tp'     )
    v_bt    =   Component(EpicsMotor, "6idhedm:m34",                 name='v_bt'     )
    # v_size  =   Component(EpicsMotor, "1ide1:Kohzu_E_upVsize.VAL",  name='v_size'   )   # vertical size !!!!!need to check this

    
### Per Peter, only motion in the y direction is allowed to avoid accidents
### consider comment out all the other PV accesses.
class FocusLens1(MotorBundle):
    """Lens 1 that focuses the beam"""
    # TODO: 
    # Need to figure out the actual set up and motor PVs
    # Each lens is sitting on at least 5 motors (x, y, (z), tiltZ, tiltX, rot)
    # l1x     =   Component(EpicsMotor, "6idhedm:m10",         name='l1x'      )
    l1y     =   Component(EpicsMotor, "6idhedm:m11",         name='l1y'      )   
    # l1z     =   Component(EpicsMotor, "6idhedm:m9",          name='l1z'      )
    # l1rot   =   Component(EpicsMotor, "6idhedm:m12",         name='l1rot'    )
    # l1tx    =   Component(EpicsMotor, "6idhedm:m13",         name='l1tx'     )
    # l1tz    =   Component(EpicsMotor, "6idhedm:m14",         name='l1tz'     )


class FocusLens2(MotorBundle):
    """Lens 2 that focuses the beam"""
    # TODO: 
    # Need to figure out the actual set up and motor PVs
    # Each lens is sitting on at least 5 motors (x, y, (z), tiltZ, tiltX, rot)
    # l2x     =   Component(EpicsMotor, "6idhedm:m16",         name='l2x'      )
    l2y     =   Component(EpicsMotor, "6idhedm:m17",         name='l2y'      )   
    # l2z     =   Component(EpicsMotor, "6idhedm:m15",         name='l2z'      )
    # l2rot   =   Component(EpicsMotor, "6idhedm:m18",       name='l2rot'    )
    # l2tx    =   Component(EpicsMotor, "6idhedm:m19",     name='l2tx'     )
    # l2tz    =   Component(EpicsMotor, "6idhedm:m20",     name='l2tz'     )


class FocusLens3(MotorBundle):
    """Lens 3 that focuses the beam"""
    # TODO: 
    # Need to figure out the actual set up and motor PVs
    # Each lens is sitting on at least 5 motors (x, y, (z), tiltZ, tiltX, rot)
    # l3x     =   Component(EpicsMotor, "PV_lens3_x",         name='l3x'      )
    l3y     =   Component(EpicsMotor, "PV_lens3_y",         name='l3y'      )   
    # l3z     =   Component(EpicsMotor, "PV_lens3_z",         name='l3z'      )
    # l3rot   =   Component(EpicsMotor, "PV_lens3_rot",       name='l3rot'    )
    # l3tx    =   Component(EpicsMotor, "PV_lens3_tiltx",     name='l3tx'     )
    # l3tz    =   Component(EpicsMotor, "PV_lens3_tiltz",     name='l3tz'     )


class FocusLens4(MotorBundle):
    """Lens 4 that focuses the beam"""
    # TODO: 
    # Need to figure out the actual set up and motor PVs
    # Each lens is sitting on at least 5 motors (x, y, (z), tiltZ, tiltX, rot)
    # l4x     =   Component(EpicsMotor, "PV_lens4_x",         name='l4x'      )
    l4y     =   Component(EpicsMotor, "PV_lens4_y",         name='l4y'      )   
    # l4z     =   Component(EpicsMotor, "PV_lens4_z",         name='l4z'      )
    # l4rot   =   Component(EpicsMotor, "PV_lens4_rot",       name='l4rot'    )
    # l4tx    =   Component(EpicsMotor, "PV_lens4_tiltx",     name='l4tx'     )
    # l4tz    =   Component(EpicsMotor, "PV_lens4_tiltz",     name='l4tz'     )


class Attenuator(Device):
    """Attenuator control"""
    
    _motor = Component(EpicsMotor, "6idhedm:m6", name='_motor')
    
    # TODO:
    #   Lack of sufficient information to implement
    #   * set_atten() ?? 
    #   The attenuators are Cu foils on a wheel.
    #   Here are the PVs for 1-ID:
    #       epics_put("1id:9440:1:bo_0.VAL", $1, 1)
    #       epics_put("1id:9440:1:bo_1.VAL", $2, 1)
    #       epics_put("1id:9440:1:bo_2.VAL", $3, 1)
    #       epics_put("1id:9440:1:bo_4.VAL", $4, 1)
    #   Per conversation with Peter, this is legacy control from 5 or more years ago
    #   The new set up will have the attenuators on the wheel similar to the Energy foil
    #   we might have something like:   
    #   def atten(self, att_level):
    #       att_range = {0,1,2,4,5,6,8,10,20,30}
    #       if att_level in att_range 
    #           yield from bps.mv(self.attenuation, att_level)
    #       else
    #           yield from bps.mv(self.attenuation, )
    #           print("Requested attenuation out of range")
    #           return()
    #
    # TODO:
    #  class level lookup table to map att_level to attenuation
    # TODO:
    #  consult Peter and write a class/static function to return the attenuation level based on materials
    
    _att_level_spreadsheet = {
        0   :   0     ,
        1   :   50    ,
        2   :   50    ,
        3   :   50    ,   
        4   :   50    ,   
        5   :   50    ,
        6   :   50    ,
        7   :   50    ,
        8   :   50    ,
        9   :   50    ,
        10  :   50    ,
        11  :   50    ,
        12  :   50    ,
        13  :   50    ,
        14  :   50    ,
        15  :   50    ,
        16  :   50    ,
        17  :   50    ,
        18  :   50    ,
        19  :   50    ,
        20  :   50    ,
        21  :   50    ,
        22  :   50    ,
        23  :   50
    }

    # This is the total range for current att_levels
    # TODO:
    #   update this range with actual setup
    _att_range = tuple(range(24))  

    # initialize and find the current attenuation
    # it may be better to initialize atten at maximum
#     def __init__(self, att_level=0):
#         self._att_level = att_level
#         self._motor = 
    
# Let pyepics handles the feedback
#     @property
#     def att_level(self):
#         return self._att_level

#     @att_level.setter
#     def att_level(self, new_att_level):
#         if new_att_level in Attenuator._att_range:
#             self._motor.mv(new_att_level)       # may need to do (new_att_level-12) depending on motor setup
#             self._att_level = new_att_level
#             print(f"TODO: need some informative meesage about changes in the attenuation")
#         else:
#             raise ValueError(f"Requested attentuation level {new_att_level} is out of range!!!"
#                                "\n            Please choose attenuation level from (0 1 2 3 ... ... 21 22 23) ")

#     @property
#     def attenuation(self):
#         return f"Current attenuation set to: {Attenuator._att_level_spreadsheet[self._att_level]}"

    # def get_attenuation(self):
    #     current_atten = atten[self.attenuator.position]
    #     return (current_atten)

    # now this seems redundent
    # @property
    # def status(self):
    #     """Return the current attenuator setting"""
    #     self.current_attenuation={
    #         "atten1"    :   self.att.position,
    #     }
    #     print(self.current_attenuation)

    # pass
    

class Beam():
    """Provide full control of the beam."""
    
    #   I'm not quite sure if it is safe to do all this here. /JasonZ
    def __init__(self):
        self.s1         = SlitUpstream(name='s1')
        self.s2         = SlitDownstream(name='s2')
        # consider only get the y motors
        # self.l1y = Component(EpicsMotor, "PV_lens1_y",         name='l1y'      )
        self.l1         = FocusLens1(name='l1')
        self.l2         = FocusLens2(name='l2')
        self.l3         = FocusLens3(name='l3')
        self.l4         = FocusLens4(name='l4')
        self.att        = Attenuator(name='att')
        self.foil       = EnergyFoil(name='foil')         # may need to do the energy calibration outside Beam, manually

    def __repr__(self):
        """Return the current beam status"""
        #   slits sizes and positions
        #   ic readings? maybe
        #   current att level and attenuation
        #   beam energy
        # __repr__ to be implemented
        pass

    @property
    def status(self):
        """Return full beam status"""
        #   Some info to print here:
        #       beam energy, wavelength etc.
        #       slit posiitons, beam size (H&V), actual beam size (on detector?)
        #       beam intensity, IC readings
        #       attenuation used etc.
        pass

    @property
    def center(self):
        """return estimated center based on slits positions"""
        #   Seems like we don't need this any more
        pass

    
class sim_s1(MotorBundle):
    h_ib   = Component(EpicsMotor, "6iddSIM:m16", name='h_ib')
    h_ob   = Component(EpicsMotor, "6iddSIM:m16", name='h_ob')
    h_size = Component(EpicsMotor, "6iddSIM:m16", name='h_size') 
    v_tp   = Component(EpicsMotor, "6iddSIM:m16", name='v_tp')
    v_bt   = Component(EpicsMotor, "6iddSIM:m16", name='v_bt')
    v_size = Component(EpicsMotor, "6iddSIM:m16", name='v_size')   
    
    
class sim_s2(MotorBundle):
    h_ib   = Component(EpicsMotor, "6iddSIM:m16", name='h_ib')
    h_ob   = Component(EpicsMotor, "6iddSIM:m16", name='h_ob')
    h_size = Component(EpicsMotor, "6iddSIM:m16", name='h_size') 
    v_tp   = Component(EpicsMotor, "6iddSIM:m16", name='v_tp')
    v_bt   = Component(EpicsMotor, "6iddSIM:m16", name='v_bt')
    v_size = Component(EpicsMotor, "6iddSIM:m16", name='v_size')  
        
class sim_l1(MotorBundle):
    l1x    = Component(EpicsMotor, "6iddSIM:m16", name='l1x')
    l1y    = Component(EpicsMotor, "6iddSIM:m16", name='l1y')
    l1z    = Component(EpicsMotor, "6iddSIM:m16", name='l1z')
    l1rot  = Component(EpicsMotor, "6iddSIM:m16", name='l1rot')
    l1tx   = Component(EpicsMotor, "6iddSIM:m16", name='l1tx')
    l1tz   = Component(EpicsMotor, "6iddSIM:m16", name='l1tz')

        
class sim_l2(MotorBundle):
    l2x    = Component(EpicsMotor, "6iddSIM:m16", name='l2x')
    l2y    = Component(EpicsMotor, "6iddSIM:m16", name='l2y')
    l2z    = Component(EpicsMotor, "6iddSIM:m16", name='l2z')
    l2rot  = Component(EpicsMotor, "6iddSIM:m16", name='l2rot')
    l2tx   = Component(EpicsMotor, "6iddSIM:m16", name='l2tx')
    l2tz   = Component(EpicsMotor, "6iddSIM:m16", name='l2tz')
        
        
class sim_l3(MotorBundle):
    l3x    = Component(EpicsMotor, "6iddSIM:m16", name='l3x')
    l3y    = Component(EpicsMotor, "6iddSIM:m16", name='l3y')
    l3z    = Component(EpicsMotor, "6iddSIM:m16", name='l3z')
    l3rot  = Component(EpicsMotor, "6iddSIM:m16", name='l3rot')
    l3tx   = Component(EpicsMotor, "6iddSIM:m16", name='l3tx')
    l3tz   = Component(EpicsMotor, "6iddSIM:m16", name='l3tz')
     
        
class sim_l4(MotorBundle):
    l4x    = Component(EpicsMotor, "6iddSIM:m16", name='l4x')
    l4y    = Component(EpicsMotor, "6iddSIM:m16", name='l4y')
    l4z    = Component(EpicsMotor, "6iddSIM:m16", name='l4z')
    l4rot  = Component(EpicsMotor, "6iddSIM:m16", name='l4rot')
    l4tx   = Component(EpicsMotor, "6iddSIM:m16", name='l4tx')
    l4tz   = Component(EpicsMotor, "6iddSIM:m16", name='l4tz')


class SimBeam():
    """Provide full control of the beam."""

    #   I'm not quite sure if it is safe to do all this here. /JasonZ
    def __init__(self):
        s1 = sim_s1(name='s1')
        s2 = sim_s2(name='s2')
        l1 = sim_l1(name='l1')
        l2 = sim_l2(name='l2')
        l3 = sim_l3(name='l3')
        l4 = sim_l4(name='l4')
        
    def __repr__(self):
        """Return the current beam status"""
        #   slits sizes and positions
        #   ic readings? maybe
        #   current att level and attenuation
        #   beam energy

        # __repr__ to be implemented

    @property
    def status(self):
        """Return full beam status"""
        #   Some info to print here:
        #       beam energy, wavelength etc.
        #       slit posiitons, beam size (H&V), actual beam size (on detector?)
        #       beam intensity, IC readings
        #       attenuation used etc.
        pass

    @property
    def center(self):
        """return estimated center based on slits positions"""
        #   Seems like we don't need this any more
        pass    


class EnergyFoil(Device):
    """Energy foil
    # TODO:
    #   Requir acutal implementation once the nature of the device is known
    #   The following info is from 1ID
    #   Motor 55 in B Crate: (5Ph OM motor, Res=-0.360, Speed=60)
    #   Pos {Element} Thck K-edge, magic#, [range], I_SCU1, Harm, HEM(keV)
    #  0  {Air}
    #  6  {Bi}          90.524   1.22  [0.52, 1.9] 361.8 A, 7th SCU1, HEM=90.555
    #  3  {Yb} 0.25mm   61.332   1.42  [0.55, 2.1] 391.0 A, 5th SCU1 HEM=61.300
    #  1  {Au}          80.725   1.45?  [0.6, ], 426.7 7th SCU1, HEM=80.725
    # -1  {Tb} 0.1mm    51.996   0.76  [0.2,  1.0]  197.8 A, 3rd SCU1, HEM=51.971
    # -8  {Hf}          65.351   1.18  [0.5, 1.7] 354.7 A 5th SCU1, HEM=65.300
    # -2  {Re}          71.676   1.300 [0.60, 2.2] 303 A, 5th SCU1 HEM=71.595
    # -4  {Pb} 0.25mm   88.005   1.42  [0.54, 2.1]   377.15 A 7th SCU1
    # -6  {Ho} 0.1mm    55.618   0.82  [0.3, 1.3]   448 A, 3rd SCU1, HEM=55.575
    #-10  {Ir}          76.112   1.60  [0.5, 1.7]   269.9 A, 5th SCU1, HEM=76.091
    #  5  {Pt}          78.395   1.29  [0.5, 2.2]   443.7 A, 7th SCU1, HEM=78.376
    #  8  {Tm}          59.390   0.79  [0.3, 1.3]   409.1 A, 5th SCU1, HEM=59.305
    # 10  {Ta}          5   0.79  [0.3, 1.3]   409.1 A, 5th SCU1, HEM=5
    # 270 (-90)      {Ir} 0.125mm  76.111     
    """
    _motor = Component(EpicsMotor, "6idhedm:m7", name='_motor')
    
#     def __init__(self):
#         self.foil           = EnergyFoil.get_energyfoil()
#         self.beam_energy    = EnergyFoil.get_energy()
    
#     def get_energyfoil(Emon_foil="air"):        # pass the config yml file to select the foil, or,
#                                                 # set up a default foil to use?
#         print("E calibration foil in")

#         if (Emon_foil=="air") mv foil  0 ;  # air
#         if (Emon_foil=="Tb") mv foil  -1 ;  # Tb
#         if (Emon_foil=="Yb") mv foil   3 ;  # Yb
#         if (Emon_foil=="Bi") mv foil   6 ;  # Bi
#         if (Emon_foil=="Ho") mv foil  -6 ;  # Ho
#         if (Emon_foil=="Pb") mv foil  -4 ;  # Pb
#         if (Emon_foil=="Re") mv foil  -2 ;  # Re
#         if (Emon_foil=="Au") mv foil   1 ;  # Au
#         if (Emon_foil=="Pt") mv foil   5 ;  # Pt
#         if (Emon_foil=="Ir") mv foil -10 ;  # Ir
#         if (Emon_foil=="Hf") mv foil  -8 ;  # Hf
#         if (Emon_foil=="Tm") mv foil   8 ;  # Tm
#         if (Emon_foil=="Ta") mv foil  10 ;  # Ta

    def get_energy():
        #move out the attenuators and then "count_em"
        pass


#   Check to see how the counter performed.
class Counter:
    """Counter"""
    pass


class FastShutter:
    """Fast shutter for taking dark field images"""
    # NOTE:
    #  apstools provides shutter class for the main/slow beamline shutter,
    #  which can be used as a reference when defining the fast shutter
    #  The FS is totally different from what we thought, Let talk more before implement.  /JasonZ
    pass


if __name__ == "__main__":
    pass