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
    """Experiment class that takes in various setup for different type of scan"""

    def __init__(self, setup, mode: str='debug'):
        pass

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


class Tomography:
    """Tomography setup for HT-HEDM instrument"""

    pass


class FarField:
    """Far-Field HEDM scan setup for HT-HEDM instrument"""

    pass


class NearField:
    """Near-Fiedl HEDM scan setup for HT-HEDM instrument"""

    pass


if __name__ == "__main__":
    print("Example usage see corresponding notebooks")
