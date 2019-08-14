#!/usr/bin/env python

"""
This module contains detectors customized for APS-MPE group.

NOTE:
    The current design of Ophyd encourages hardwaring PVs
    into the source code.  Therefore, we are hard-coding all
    PVs into the associated class definition.
    Also, the current PVs are for devices at 6BM, which need to
    be switched to 6-ID-D for HT-HEDM.
"""

from ophyd   import AreaDetector
from ophyd   import SingleTrigger, EpicsSignalWithRBV
from ophyd   import ADComponent
from ophyd   import PointGreyDetectorCam
from ophyd   import ProcessPlugin
from ophyd   import TIFFPlugin
from ophyd   import HDF5Plugin


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


class HDF5Plugin6IDD(HDF5Plugin):
    """AD HDF5 plugin customizations (properties)"""
    xml_file_name = ADComponent(EpicsSignalWithRBV, "XMLFileName")


class PointGreyDetector6IDD(SingleTrigger, AreaDetector):
    """Point Gray area detector used at 6IDD"""
    cam   = ADComponent(PointGreyDetectorCam6IDD, "cam1:")  # cam component
    proc1 = ADComponent(ProcessPlugin, suffix="Proc1:")     # proc plugin
    tiff1 = ADComponent(TIFFPlugin,    suffix="TIFF1:")     # tiff plugin
    hdf1  = ADComponent(HDF5Plugin6IDD, suffix="HDF1:")     # HDF5 plugin


if __name__ == "__main__":
    # example usage
    import os
    import epics
    from   pathlib import Path

    ADPV_prefix = "1idPG2"
    det = PointGreyDetector6IDD(f"{ADPV_prefix}:", name='det')

    # we need to manually setup the PVs to store background and projections
    # separately in a HDF5 archive
    # this is the PV we use as the `SaveDest` attribute
    # check the following page for important information
    # https://github.com/BCDA-APS/use_bluesky/blob/master/notebooks/sandbox/images_darks_flats.ipynb
    #
    epics.caput(f"{ADPV_prefix}:cam1:FrameType.ZRST", "/exchange/data_white_pre")
    epics.caput(f"{ADPV_prefix}:cam1:FrameType.ONST", "/exchange/data")
    epics.caput(f"{ADPV_prefix}:cam1:FrameType.TWST", "/exchange/data_white_post")
    epics.caput(f"{ADPV_prefix}:cam1:FrameType.THST", "/exchange/data_dark")
    # ophyd needs this configuration
    epics.caput(f"{ADPV_prefix}:cam1:FrameType_RBV.ZRST", "/exchange/data_white_pre")
    epics.caput(f"{ADPV_prefix}:cam1:FrameType_RBV.ONST", "/exchange/data")
    epics.caput(f"{ADPV_prefix}:cam1:FrameType_RBV.TWST", "/exchange/data_white_post")
    epics.caput(f"{ADPV_prefix}:cam1:FrameType_RBV.THST", "/exchange/data_dark")
    # set the layout file for cam
    # NOTE: use the __file__ as anchor should resolve the directory issue.
    _current_fp = str(Path(__file__).parent.absolute())
    _attrib_fp = os.path.join(_current_fp, 'config/PG2_attributes.xml')
    '''
    det.cam.nd_attributes_file.put(_attrib_fp)
    # set attributes for HDF5 plugin
    _layout_fp = os.path.join(_current_fp, 'config/tomo6bma_layout.xml')
    det.hdf1.xml_file_name.put(_layout_fp)
    # turn off the problematic auto setting in cam
    det.cam.auto_exposure_auto_mode.put(0)  
    det.cam.sharpness_auto_mode.put(0)
    det.cam.gain_auto_mode.put(0)
    det.cam.frame_rate_auto_mode.put(0)
    '''