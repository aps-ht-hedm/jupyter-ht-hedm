#!/usr/bin/env python

"""
This module contains detectors customized for APS-MPE group.

NOTE:
* Retiga area detector is not readily available in Ophyd
* Retiga area detector camera needs to be either setup here or PR to ophyd 
* Changed to PointGrey Detectors in this example
"""

from ophyd   import AreaDetector
from ophyd   import SingleTrigger, EpicsSignalWithRBV
from ophyd   import ADComponent
from ophyd   import CamBase, PointGreyDetectorCam  ## no DexelaDetectorCam in Ophyd
from ophyd   import ProcessPlugin
from ophyd   import TIFFPlugin
from ophyd   import HDF5Plugin


class HDF5Plugin6IDD(HDF5Plugin):
    """AD HDF5 plugin customizations (properties)"""
    xml_file_name = ADComponent(EpicsSignalWithRBV, "XMLFileName")


class RetigaDetectorCam(CamBase):
    """Retiga camera """
    # NOTE:
    # Different camera module from different manufacture requires different
    # configuration, see 
    #  https://github.com/bluesky/ophyd/blob/master/ophyd/areadetector/cam.py
    # for more examples on how to make the PointGrey cam
    pass

class RetigaDetectorCam6IDD(RetigaDetectorCam):
    """Retiga detector camera module"""
    # TODO:
    #   We will do this if we have to....
    #   Please, please, please don't purchase this
    pass

class DexelaDetectorCam(CamBase):
    """Dexela detector camera module """
    # NOTE:
    # Different camera module from different manufacture requires different
    # configuration, see 
    #  https://github.com/bluesky/ophyd/blob/master/ophyd/areadetector/cam.py
    # for more examples on how to make the PointGrey cam
    pass

class DexelaDetectorCam6IDD(DexelaDetectorCam):
    """Dexela detector camera module"""
    # TODO:
    #   Missing features from the default settings need to be added here
    #   Check with Jun at the end of Oct for the new Dexela info
    pass


class PointGreyDetectorCam6IDD(PointGreyDetectorCam):
    """PointGrey Grasshopper3 cam plugin customizations (properties)"""
    auto_exposure_on_off    = ADComponent(EpicsSignalWithRBV, "AutoExposureOnOff")
    auto_exposure_auto_mode = ADComponent(EpicsSignalWithRBV, "AutoExposureAutoMode")
    sharpness_on_off        = ADComponent(EpicsSignalWithRBV, "SharpnessOnOff")
    sharpness_auto_mode     = ADComponent(EpicsSignalWithRBV, "SharpnessAutoMode")
    gamma_on_off            = ADComponent(EpicsSignalWithRBV, "GammaOnOff")
    shutter_auto_mode       = ADComponent(EpicsSignalWithRBV, "ShutterAutoMode")
    gain_auto_mode          = ADComponent(EpicsSignalWithRBV, "GainAutoMode")
    trigger_mode_on_off     = ADComponent(EpicsSignalWithRBV, "TriggerModeOnOff")
    trigger_mode_auto_mode  = ADComponent(EpicsSignalWithRBV, "TriggerModeAutoMode")
    trigger_delay_on_off    = ADComponent(EpicsSignalWithRBV, "TriggerDelayOnOff")
    frame_rate_on_off       = ADComponent(EpicsSignalWithRBV, "FrameRateOnOff")
    frame_rate_auto_mode    = ADComponent(EpicsSignalWithRBV, "FrameRateAutoMode")

class PointGreyDetector(SingleTrigger, AreaDetector):
    """PointGrey Detector used at 6-ID-D@APS for tomo and nf-HEDM"""

    cam   = ADComponent(PointGreyDetectorCam6IDD, suffix="cam1:" )  # camera
    proc1 = ADComponent(ProcessPlugin,     suffix="Proc1:")  # processing
    tiff1 = ADComponent(TIFFPlugin,        suffix="TIFF1:")  # tiff output
    hdf1  = ADComponent(HDF5Plugin6IDD,    suffix="HDF1:" )  # HDF5 output

    @property
    def status(self):
        """List all related PVs and corresponding values"""
        # TODO:
        #   provide acutal implementation here
        return "Not implemented yet"

    @property
    def help(self):
        """Return quick summary of the actual specs of the detector"""
        pass

    @property
    def position(self):
        """return the area detector position from the associated motor"""
        pass

    @position.setter
    def position(self, new_pos):
        """move the detector to the new location"""
        # NOTE:
        #   This is for interactive control only, cannot be used in scan plan
        #   We will need to use this position during scan, i.e. near field z scan
        pass

    # TODO:
    #  Additional PVs can be wrapped as property for interactive use when the 
    #  acutal PVs are known.


class DexelaDetector(SingleTrigger, AreaDetector):
    """Dexela detector used at 6-ID-D@APS for ff-HEDM"""

    cam   = ADComponent(DexelaDetectorCam6IDD, suffix="cam1:" )  # camera
    proc1 = ADComponent(ProcessPlugin,         suffix="Proc1:")  # processing
    tiff1 = ADComponent(TIFFPlugin,            suffix="TIFF1:")  # tiff output
    hdf1  = ADComponent(HDF5Plugin6IDD,        suffix="HDF1:" )  # HDF5 output

    @property
    def status(self):
        """List all related PVs and corresponding values"""
        # TODO:
        #   provide acutal implementation here
        return "Not implemented yet"

    @property
    def help(self):
        """Return quick summary of the actual specs of the detector"""

    @property
    def position(self):
        """return the area detector position from the associated motor"""
        pass

    @position.setter
    def position(self, new_pos):
        """move the detector to the new location"""
        # NOTE:
        #   This is for interactive control only, cannot be used in scan plan
        pass

    # TODO:
    #  Additional PVs can be wrapped as property for interactive use when the 
    #  acutal PVs are known.    


if __name__ == "__main__":
    # example on how to make an instance of the PointGrey detector
    det = PointGreyDetector("TBD_PV", name='det')

    # additional setup might be necessary to use the dxchange format for
    # HDF5 output, see 
    # https://github.com/BCDA-APS/use_bluesky/blob/master/notebooks/sandbox/images_darks_flats.ipynb
    # for more details