#!/usr/bin/env python

"""
This module contains beamline specific control macros and functions.
"""

from ophyd   import MotorBundle
from ophyd   import EpicsMotor
from ophyd   import Component


class SlitUpstream(MotorBundle):
    """Upstream slit that controls the four blades that form the beam"""
    #   The slit PVs are not meaningful at all, the actual name will depend on set up
    #   Here is the upstream slit PVs at 1-ID-E   ("motorPV.LVIO" for soft limit check) 
    #   1ide1:m20
    #   1ide1:m21
    #   1ide1:m22
    #   1ide1:m23
    #   didn't found actual control in the scripts, manually adjusted??

    left   = Component(EpicsMotor, "PV_left",   name='left'  )
    right  = Component(EpicsMotor, "PV_right",  name='right' )
    top    = Component(EpicsMotor, "PV_top",    name='top'   )
    bottom = Component(EpicsMotor, "PV_bottom", name='bottom')

class SlitDownstream(MotorBundle):
    """Downstream slit that controls the four blades that form the beam"""

    left   = Component(EpicsMotor, "PV_left",   name='left'  )
    right  = Component(EpicsMotor, "PV_right",  name='right' )
    top    = Component(EpicsMotor, "PV_top",    name='top'   )
    bottom = Component(EpicsMotor, "PV_bottom", name='bottom')

class FocusLenses(MotorBundle):
    """Lens that focuses the beam"""
    # TODO: 
    # Need to figure out the actual set up and motor PVs
    # Each lens is sitting on at least 5 motors (x, y, (z), tiltZ, tiltX, rot)
    # Let's discuss how to do this...
    lens1 = Component(EpicsMotor, "PV_lens1",   name='lens1'  )
    lens2 = Component(EpicsMotor, "PV_lens2",   name='lens2'  )
    lens3 = Component(EpicsMotor, "PV_lens3",   name='lens3'  )
    lens4 = Component(EpicsMotor, "PV_lens4",   name='lens4'  )

class Attenuator(MotorBundle):
    """Attenuator control"""
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
    #   We should also have a attenuation look up table

    #   initialize and find the current attenuation
    def __init__(self):
        self.attenuation    = Attenuator.get_attenuation()


    def get_attenuation(self):
        current_atten = atten[self.attenuator.position]
        return (current_atten)

    # now this seems redundent
    @property
    def status(self):
        """Return the current attenuator setting"""
        self.current_attenuation={
            "atten1"    :   self.att.position,
        }
        print(self.current_attenuation)

    pass


class Beam:
    """Provide full control of the beam."""

    def __init__(self):
        self.up_slit    = SlitUpstream(     name = 'slit_upstream')
        self.down.slit  = SlitDownstream(   name = 'slit_downstream')
        self.atten      = Attenuator(       name = 'atten')         # adjustment needed

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
        pass


class EnergyFoil:
    """Energy foil"""
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
    def __init__(self):
        self.foil           = EnergyFoil.get_energyfoil()
        self.beam_energy    = EnergyFoil.get_energy()
    
    def get_energyfoil(Emon_foil="air"):        # pass the config yml file to select the foil, or,
                                                # set up a default foil to use?
        print("E calibration foil in")

        if (Emon_foil=="air") mv foil  0 ;  # air
        if (Emon_foil=="Tb") mv foil  -1 ;  # Tb
        if (Emon_foil=="Yb") mv foil   3 ;  # Yb
        if (Emon_foil=="Bi") mv foil   6 ;  # Bi
        if (Emon_foil=="Ho") mv foil  -6 ;  # Ho
        if (Emon_foil=="Pb") mv foil  -4 ;  # Pb
        if (Emon_foil=="Re") mv foil  -2 ;  # Re
        if (Emon_foil=="Au") mv foil   1 ;  # Au
        if (Emon_foil=="Pt") mv foil   5 ;  # Pt
        if (Emon_foil=="Ir") mv foil -10 ;  # Ir
        if (Emon_foil=="Hf") mv foil  -8 ;  # Hf
        if (Emon_foil=="Tm") mv foil   8 ;  # Tm
        if (Emon_foil=="Ta") mv foil  10 ;  # Ta

    def get_energy()
        move out the attenuators and then "count_em"


    """

    pass


class Counter:
    """Counter"""
    pass


class FastShutter:
    """Fast shutter for taking dark field images"""
    # NOTE:
    #  apstoos provides shutter class for the main/slow beamline shutter,
    #  which can be used as a reference when defining the fast shutter
    #  The FS is totally different from what we thought, Let talk more before implement.  /JasonZ
    pass


if __name__ == "__main__":
    pass