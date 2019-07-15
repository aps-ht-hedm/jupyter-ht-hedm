#!/usr/bin/env python

"""
Predefined bluesky scan plans
"""

import bluesky.plans         as bp
import bluesky.preprocessors as bpp
import bluesky.plan_stubs    as bps
from utility import load_config

@bpp.run_decorator()
def collect_white_field(det, tomostage, shutter, config_tomo):
    """
    Collect white/flat field images by moving the sample out of the FOV
    """
    pass


@bpp.run_decorator()
def collect_dark_field(det, tomostage, cfg_tomo):
    """
    Collect dark field images by close the shutter
    """
    pass


@bpp.run_decorator()
def step_scan(det, tomostage, cfg_tomo):
    """
    Collect projects with step motion
    """
    pass


@bpp.run_decorator()
def fly_scan(det, tomostage, cfg_tomo):
    """
    Collect projections with fly motion
    """
    pass


@bpp.run_decorator()
def tomo_scan(det, tomostage, shutter, cfg):
    """
    Tomography scan plan based on given configuration
    """
    cfg = load_config(cfg) if type(cfg) != dict else cfg

    # extract configuration and calculate derived parameters

