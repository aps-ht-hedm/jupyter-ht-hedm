#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module provide high-level class that provides simplified APIs for
conducting different experiment.
"""

import os
import pathlib
import bluesky
import ophyd
import epics
import databroker
import numpy as np

from   bluesky.callbacks.best_effort import BestEffortCallback
from   bluesky.suspenders            import SuspendFloor
from   bluesky.simulators            import summarize_plan

from   time                          import sleep

from  .devices.beamline              import Beam, SimBeam
from  .devices.beamline              import FastShutter
from  .devices.motors                import StageAero, SimStageAero
from  .devices.motors                import EnsemblePSOFlyDevice
from  .devices.detectors             import PointGreyDetector, DexelaDetector, SimDetector  
from  .util                          import dict_to_msg
from  .util                          import load_config
from  .util                          import is_light_on

import bluesky.preprocessors as bpp
import bluesky.plan_stubs    as bps


__author__ = "Chen Zhang and Quan(Jason) Zhou"
__copyright__ = "Copyright 2020, The HT-HEDM Project"
__credits__ = ["Chen Zhang", "Quan(Jason) Zhou", "Pete Jemine"]
__license__ = "MIT-3.0"
__version__ = "0.0.1"
__maintainer__ = "Chen Zhang"
__email__ = "kedokudo@protonmail.com"
__status__ = "Alpha"


# NOTE:
# Given that all three setup is centered around a (multiplicative of) 360 rotation, we are
# using a factory pattern to form a loose couple between the acutal scan and the Ophyd
# representation of the instrument.


class Experiment:
    """
    Experiment class that takes in various setup for different type of scan

    Usage:
    my_experiment = Experiment(Tomography, mode='production')

    """

    def __init__(self, setup, config, mode: str='debug'):
        # configuration of the experiment
        self._config = load_config(config) if type(config) != dict else config

        # double check mode input since setup will not check it again
        if mode.lower() in ['debug', 'dryrun', 'production']:
            self._mode = mode.lower()
        else:
            raise ValueError(f"Invalide mode -> {mode}")

        # get the hardware from different setup
        self._mysetup = setup
        self.stage = setup.get_stage(mode=self._mode)
        self.flycontrol = setup.get_flycontrol(mode=self._mode)
        self.detector = setup.get_detector(mode=self._mode)
        self._safe2go = False
        # TODO 
        # components need to be implemented for each setup in the future
        # 1. beam
        # 2. calirabtion?
        # 3. representation? summary of setup condition?

        # get the scan plan from different setup

        # setup the RunEngine
        self.RE = bluesky.RunEngine({})
        try:
            # NOTE
            # The MongoDB configuration file should be
            #    $HOME/.config/databroker/mongodb_config.yml
            # Check the MongoDB container running state if RE cannot locate
            # the service (most likely a host name or port number error)
            self.db = databroker.Broker.named("mongodb_config")
            self.RE.subscribe(self.db.insert)
        except:
            print("MongoDB metadata recording stream is not configured properly")
            print("Please double check the MongoBD server and try a manual setup")
        finally:
            print("It is recommended to have only one RunEngine per experiment/notebook")
            print("You can expose the RunEngine to global scope via: RE=$ExperimentName.RE")

        # get all beamline level control
        self.shutter = Experiment.get_main_shutter(mode)
        self.suspend_shutter = SuspendFloor(self.shutter.pss_state, 1)
        if self._mode == 'production':
            from apstools.devices import ApsMachineParametersDevice
            self._aps = ApsMachineParametersDevice(name="APS")
            self.suspend_APS_current = SuspendFloor(self._aps.current, 2, resume_thresh=10)
            self.RE.install_suspender(self.suspend_APS_current)

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, new_config):
        """Provide record of configuration changes"""
        print("Original experiment configuration:")
        print(self._config)
        self._config = load_config(new_config) if type(new_config) != dict else new_config
        print("New configuration")
        print(self._config)
        self._safe2go = False  # forced sanity before actual run

    @property
    def mode(self):
        return f"current mode is {self._mode}, available options are ['debug', 'dryrun', 'production']"

    @mode.setter
    def mode(self, newmode):
        self._mode = newmode
        self.shutter = Experiment.get_main_shutter(self._mode)
        self.stage = self._mysetup.get_stage(mode=self._mode)
        self.flycontrol = self._mysetup.get_flycontrol(mode=self._mode)
        self.detector = self._mysetup.get_detector(mode=self._mode)
        self._safe2go = False  # forced sanity before actual run

    @staticmethod
    def get_main_shutter(mode):
        """
        return
            simulated shutter when [dryrun, debug]
            acutal shutter    when [productio]
        
        TODO:
            need to update with acutal PV for 6-ID-D
        """
        if mode.lower() in ['debug', 'dryrun']:
            from apstools.devices import SimulatedApsPssShutterWithStatus
            A_shutter = SimulatedApsPssShutterWithStatus(name="A_shutter")
        elif mode.lower() == 'production':
            from apstools.devices import ApsPssShutterWithStatus
            A_shutter = ApsPssShutterWithStatus(
                "PA:01ID",                          # This is for 1ID
                "PA:01ID:STA_A_FES_OPEN_PL",        # This is for 1ID
                name="A_shutter",
            )
        else:
            raise ValueError(f"Invalide mode, {mode}")
        
        return A_shutter

    @staticmethod
    def get_fast_shutter(mode):
        """Return fast shutter"""
        # TODO: implement the fast shutter, then instantiate it here
        pass

    def check(self, cfg):
        """Return user input before run"""
        # NOTE
        # This is mostly as a sanity check, but can also double as a way to
        # record user configuration in the notebook
        cfg = load_config(cfg) if type(cfg) != dict else cfg
        print(f"Tomo configuration:\n{dict_to_msg(cfg['tomo'])}")
        print(f"Output:\n{dict_to_msg(cfg['output'])}")

    # NOTE
    # The following methods are wraper of the acutal implementation of different scan plans
    # for various experiment setup
    def scan(self, *args, **kwargs):
        """wrapper of the 360 rotation scan plan"""
        if not self._safe2go:
            summarize_plan(self._mysetup.step_scan(self, *args, **kwargs))
            self._safe2go = True
        else:
            self.RE(self._mysetup.step_scan(self, *args, **kwargs))

    def collect_white(self, *args, **kwargs):
        """wrapper of the still white field image acquisition"""
        if not self._safe2go:
            summarize_plan(self._mysetup.collect_white(self, *args, **kwargs))
            self._safe2go = True
        else:
            self.RE(self._mysetup.collect_white(self, *args, **kwargs))

    def collect_dark(self, *args, **kwargs):
        """wrapper of the still dark field image acquisition"""
        if not self._safe2go:
            summarize_plan(self._mysetup.collect_dark(self, *args, **kwargs))
            self._safe2go = True
        else:
            self.RE(self._mysetup.collect_dark(self, *args, **kwargs))

    # NOTE
    # The following methods are direct call to pyepics, bypassing the RunEngine


class Tomography:
    """Tomography setup for HT-HEDM instrument"""

    @staticmethod
    def get_stage(mode):
        """return the aerotech stage configuration"""
        return {
            "dryrun":     StageAero(name='tomostage'),
            "production": StageAero(name='tomostage'),
            "debug":      SimStageAero(name='tomostage'),
            }[mode]
    
    @staticmethod
    def get_flycontrol(mode):
        # the mode check should be done at the experiment level
        from ophyd import sim
        return {
            'debug':       sim.flyer1,
            'dryrun':      EnsemblePSOFlyDevice("6idhedms1:PSOFly1:", name="psofly"),
            'production':  EnsemblePSOFlyDevice("6idhedms1:PSOFly1:", name="psofly"),
            }[mode]
            
    def get_detector(self, mode):
        """return the 1idPG4 tomo detector for HT-HEDM"""
        det_PV = {
            'debug':       "6iddSIMDET1:",
            'dryrun':      "1idPG4:",
            'production':  "1idPG4:",
            }[mode]
        
        det = {
            'debug':       SimDetector(det_PV,  name='det'),
            'dryrun':      PointGreyDetector(det_PV, name='det'),
            'production':  PointGreyDetector(det_PV, name='det'),
            }[mode]
        
        # setup HDF5 layout using a hidden EPICS PV
        # -- enumerator type
        # -- need to set both write and RBV field
        # -- we are using dxchange data strcuture instead of Nexus
        epics.caput(f"{det_PV}cam1:FrameType.ZRST",     "/exchange/data_white_pre")
        epics.caput(f"{det_PV}cam1:FrameType.ONST",     "/exchange/data")
        epics.caput(f"{det_PV}cam1:FrameType.TWST",     "/exchange/data_white_post")
        epics.caput(f"{det_PV}cam1:FrameType.THST",     "/exchange/data_dark")        
        epics.caput(f"{det_PV}cam1:FrameType_RBV.ZRST", "/exchange/data_white_pre")
        epics.caput(f"{det_PV}cam1:FrameType_RBV.ONST", "/exchange/data")
        epics.caput(f"{det_PV}cam1:FrameType_RBV.TWST", "/exchange/data_white_post")
        epics.caput(f"{det_PV}cam1:FrameType_RBV.THST", "/exchange/data_dark")

        # set the attribute file (det.cam) and the layout file (det.hdf1)
        _current_fp = str(pathlib.Path(__file__).parent.absolute())
        _attrib_fp = os.path.join(_current_fp, 'config/PG4_attributes.xml')
        _layout_fp = os.path.join(_current_fp, 'config/tomo6idd_layout.xml')
        det.cam1.nd_attributes_file.put(_attrib_fp)
        det.hdf1.xml_file_name.put(_layout_fp)

        # turn off the problematic auto setting in cam1
        # NOTE:
        #   These settings should have been cached after a succesful run. We are just ensuring that
        #   the correct settings are used for the camera to prevent potential loss of cached settings
        # -- related to auto-* 
        det.cam1.auto_exposure_auto_mode.put(0)  
        det.cam1.sharpness_auto_mode.put(0)
        det.cam1.gain_auto_mode.put(0)
        det.cam1.frame_rate_auto_mode.put(0)
        # -- prime camera
        # NOTE:
        # By default, all file plugins have no idea the images dimension&size, therefore we need to pump
        # in an image to let the file plugins know what to expect
        # ---- get camera ready to keep taking image
        det.cam1.acquire_time.put(0.001)
        det.cam1.acquire_period.put(0.005)
        det.cam1.image_mode.put('Continuous')
        # ---- get tiff1 primed
        det.tiff1.auto_increment.put(0)
        det.tiff1.capture.put(0)
        det.tiff1.enable.put(1)
        det.tiff1.file_name.put('prime_my_tiff')
        det.cam1.acquire.put(1)
        sleep(0.01)
        det.cam1.acquire.put(0)
        det.tiff1.enable.put(0)
        det.tiff1.auto_increment.put(1)
        # ---- get hdf1 primed
        det.hdf1.auto_increment.put(0)
        det.hdf1.capture.put(0)
        det.hdf1.enable.put(1)
        det.hdf1.file_name.put('prime_my_hdf')
        det.cam1.acquire.put(1)
        sleep(0.01)
        det.cam1.acquire.put(0)
        det.hdf1.enable.put(0)
        det.hdf1.auto_increment.put(1)
        # ---- turn on auto save (supercede by disable, so we are safe)
        det.tiff1.auto_save.put(1)
        det.hdf1.auto_save.put(1)
        # -- realted to proc1
        det.proc1.filter_callbacks.put(1)   # 0 Every array; 1 Array N only (useful for taking bg)
        det.proc1.auto_reset_filter.put(1)  # ALWAYS auto reset filter
        # -- ?? more to come
        # -- enter stand-by mode
        det.cam1.image_mode.put('Multiple')

        return det


class FarField:
    """Far-Field HEDM scan setup for HT-HEDM instrument"""

    pass


class NearField:
    """Near-Fiedl HEDM scan setup for HT-HEDM instrument"""

    pass


if __name__ == "__main__":
    print("Example usage see corresponding notebooks")
