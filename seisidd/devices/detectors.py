#!/usr/bin/env python

"""
This module contains detectors customized for APS-MPE group.

NOTE:
* Retiga area detector is not readily available in Ophyd
* Retiga area detector camera needs to be either setup here or PR to ophyd 
* Changed to PointGrey Detectors in this example
"""

from ophyd   import AreaDetector
from ophyd   import SingleTrigger, EpicsSignalRO, EpicsSignalWithRBV
from ophyd   import ADComponent
from ophyd   import CamBase, PointGreyDetectorCam  ## no DexelaDetectorCam in Ophyd
from ophyd   import ProcessPlugin
from ophyd   import TIFFPlugin
from ophyd   import HDF5Plugin
from ophyd   import TransformPlugin
from ophyd   import ImagePlugin


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
    # NOTE:
    # - The PV settings are based on QIMAGE2@1-ID-C,APS
    # - The following PVs are defined in CamBase, but the available values
    #   might differe from other cams  // bookkeeping for inconsistent naming
    #    ---------------    |||   ------------
    #    MEDM/GUI/caQTdm    |||    PV/BlueSky
    #    ---------------    |||   ------------
    #   acquire_time        ===   exposure_time
    #   attributes          ===   nd_attributes_file
    #   buffer max/used     ===   pool_max/used_buffers
    #   buffer alloc/free   ===   pool_alloc/free_buffers
    #   buffer max/used     ===   pool_max_buffers
    #   memory max/userd    ===   pool_max/used_mem
    #   image_counter       ===   array_counter
    #   image_rate          ===   array_rate
    #   Sensor size         ===   max_size                  // bundled fields
    #   Region start        ===   min_x/y
    #   Region size         ===   size                      // bundled fields
    #   Image size          ===   array_size                // bundled fields
    #   
    # - Nominal values for special fields
    #   * image_mode
    #       0: Single; 1: Multiple; 2: Continuous; 3: Single Fast
    #   * trigger_mode
    #       0: Freerun;  1: EdgeHi;  2: EdgeLow;   3: PulseHi;     4: PulseLow
    #       5: Software; 6: StrobeHi 7: StrobeLow; 8: Trigger_last
    # DEV:
    # - PVs with ?? requires double check during testing
    #

    _html_docs = ['retigaDoc.html']                                            # ??

    # ---
    # --- Define missing fields in the collect & attribute panel 
    # ---
    auto_exposure = ADComponent(EpicsSignalWithRBV, 'aAutoExposure')           # ??
    
    exposure_max  = ADComponent(EpicsSignalRO, 'ExposureMax_RBV')
    exposure_min  = ADComponent(EpicsSignalRO, 'ExposureMin_RBV')

    exposure_status_message = ADComponent(EpicsSignalRO, 'qExposureStatusMessage_RBV')
    frame_status_message    = ADComponent(EpicsSignalRO, 'qFrameStatusMessage_RBV')

    pool_used_mem_scan = ADComponent(EpicsSignalWithRBV, 'PoolUsedMem.SCAN')   # ??
    # available values for pool_used_mem_scan
    # 0: Passive;    1: Event;      2: I/O Intr;
    # 3: 10 second;  4: 5 second;   5: 2 second;  6: 1 second;  
    # 7: 0.5 second; 8: 0.2 second; 9: 0.1 second

    # ---
    # --- Define missing fields in the Setup panel
    # ---
    asyn_io_connected = ADComponent(EpicsSignalWithRBV, 'AsynIO.CNCT')         # 0: Disconnected; 1: Connected
    reset_cam         = ADComponent(EpicsSignalWithRBV, 'qResetCam')

    # ---
    # --- Define missing fields in the Readout panel
    # ---
    binning = ADComponent(EpicsSignalWithRBV, 'qBinning')
    # 0: 1x1;  1: 2x2; 2: 4x4;  3: 8x8
    # WARNING: 
    # retiga does not have individual binning fields, therefore the predefined
    # bin_x and bin_y will lead to error...
    gain_max   = ADComponent(EpicsSignalRO, 'GainMax_RBV')
    gain_min   = ADComponent(EpicsSignalRO, 'GainMin_RBV')
    
    abs_offset   = ADComponent(EpicsSignalWithRBV, 'qOffset')                    # ??
    image_format = ADComponent(EpicsSignalWithRBV, 'qImageFormat')
    # -- available values for image_format
    #  0: Raw       8;    1: Raw       16;  
    #  2: Mono      8;    3: Mono      16;
    #  4: RGB Plane 8;    5: GBR Plane 16;
    #  6: BGR      24;
    #  7: XRGB     32;
    #  8: RGB      48;
    #  9: BGRX     32;
    # 10: RGB      24;
    readout_speed = ADComponent(EpicsSignalWithRBV, 'qReadoutSpeed')
    # -- available values for readout speed
    # 0: 20 Mhz;  1: 10 Mhz;  2: 5 Mhz

    # ---
    # --- Define missing fileds in the Cooling Panel
    # ---
    cooler = ADComponent(EpicsSignalWithRBV, 'qCoolerActive')
    # -- available values for cooler
    # 0: off;  1: on


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


class GEDetector(SingleTrigger, AreaDetector):
    """Generic detector abstraction for GE"""
    # e.g.  det = GEDetector("GE2:", name='det')
    # TODO
    # we migth need to switch to raw
    cam1  = ADComponent(CamBase, suffix="cam1:")
    proc1 = ADComponent(ProcessPlugin, suffix="Proc1:")
    tiff1 = ADComponent(TIFFPlugin, suffix="TIFF1:")


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

    cam1   = ADComponent(PointGreyDetectorCam6IDD, suffix="cam1:"  )  # camera
    proc1  = ADComponent(ProcessPlugin,            suffix="Proc1:" )  # processing
    tiff1  = ADComponent(TIFFPlugin,               suffix="TIFF1:" )  # tiff output
    hdf1   = ADComponent(HDF5Plugin6IDD,           suffix="HDF1:"  )  # HDF5 output
    trans1 = ADComponent(TransformPlugin,          suffix="Trans1:")  # Transform images
    image1 = ADComponent(ImagePlugin,              suffix="image1:")  # Image plugin, rarely used in plan

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

    def cont_acq(self, _exp, _nframes = -1):
        """
        cont_acq(a, b)
        acuqre 'b' images with exposure of 'a' seconds
        b is default to -1 to continue acquiring until manual interruption
        """
        from time import sleep

        self.cam1.acquire_time.put(_exp)
        self.cam1.acquire_mode.put("continuous")  # To be checked
        if _nframes <= 0:
            # do infinite number of frames....
            print(f"Start taking images with {_exp} seconds of exposure\n")
            print(f"CTRL + C tp stop...\n")
            sleep(0.5)
        else:
            self.cam1.acquire_mode.put("multiple") 
            print(f"Start taking {_nframes} images with {_exp} seconds of exposure\n")
            print(f"CTRL + C to stop...\n")
            self.cam1.n_images.put(_nframes)
            sleep(0.5) # To be updated
        self.cam1.acquire.put(1)


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


class SimDetectorCam6IDD(PointGreyDetectorCam):
    """
    Using SimDetector as PointGrey:
    cam plugin customizations (properties)
    """
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


class SimDetector(SingleTrigger, AreaDetector):
    """
    Simulated Detector used at 6-ID-D@APS
    This is based on the Point Grey detector
    """

    cam1  = ADComponent(SimDetectorCam6IDD, suffix="cam1:" )  # camera
    proc1 = ADComponent(ProcessPlugin,      suffix="Proc1:")  # processing
    tiff1 = ADComponent(TIFFPlugin,         suffix="TIFF1:")  # tiff output
    hdf1  = ADComponent(HDF5Plugin6IDD,     suffix="HDF1:" )  # HDF5 output

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


if __name__ == "__main__":
    # example on how to make an instance of the PointGrey detector
    det = PointGreyDetector("TBD_PV", name='det')

    # additional setup might be necessary to use the dxchange format for
    # HDF5 output, see 
    # https://github.com/BCDA-APS/use_bluesky/blob/master/notebooks/sandbox/images_darks_flats.ipynb
    # for more details
