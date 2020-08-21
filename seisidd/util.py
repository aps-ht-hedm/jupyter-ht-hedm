#!/usr/bin/env python

"""
This module provides utility functions useful for running experiment through
notebook interface.
"""

import yaml

from tabulate             import tabulate
from IPython              import get_ipython
from IPython.core.display import display, HTML


def pso_config(
        psofly,
        omega_start: float,
        omega_end: float,
        n_images: int,
        exposure_time: float,
        speed_scale: float=0.5,        # 0: slowest speed possible, 1: fastest speed possible, 0~1: linear interpolation
        camera_make: str='PointGrey',
    ):
    """
    PSOFly requires careful configuration to synchronize the PSO signal with Aerotech motor rotation.

    Example:
    >> pso_config(psofly, omega_start=0, omega_end=5, n_images=5, exposure_time=acquire_time, speed_scale=0.8)
    >> 6.0152375939849625, 1, 0.06624447237129363
    """
    # calculate the scan_delta (in degrees)
    # -- the rising edge is the beginning of the image acquisition
    scan_delta = abs(omega_start - omega_end)/n_images
    if (psofly.scan_delta.low_limit - scan_delta)*(psofly.scan_delta.high_limit-scan_delta) > 0:
        raise ValueError("Scan Delta out of the permitted range")

    # use the provided exposure time and general gap time (detector delta) to calculate
    # the possible slew speed
    # For Tomo (imaging):
    # -- the exposure time should be as small as possible since over-long exposure can lead
    #    to bluring of the image
    # For Diffraction:
    # -- maximazing exposure time is recomended as it help covering as much omega range as possible
    #    to avoid missing peaks
    # NOTE:
    #   1. Different cameras have different readout time, so the gap time must be larger than the readout
    #      time to avoid losing frames.
    #      -- ff-HEDM (GE): 150 ms
    #      -- ff-HEDM (Varex): 100us   ## !!!need to confirm
    #      -- tomo (PG): 33 ms
    #   2. Aerotech has built-in speed limits, therefore the calcuated slew speed need to be within the
    #      acceptable range (often between 0.001 degree/s ~ 10 degree/s)
    _readout = {
        "PointGrey": 0.033,
        "GE": 0.150,
        "Varex": 0.0001,
    }[camera_make]
    # calculate the acutal slew speed limit cap
    _slew_speed_max = scan_delta/(_readout+exposure_time) if scan_delta/(_readout+exposure_time) < psofly.slew_speed.high_limit else psofly.slew_speed.high_limit
    _slew_speed_min = psofly.slew_speed.low_limit
    # slew speed is defined as a linear scaling bewteen _slew_speed_min and _slew_speed_max
    slew_speed = speed_scale*(_slew_speed_max - _slew_speed_min) + _slew_speed_min
    # now calculate the gap time (det setup)
    detector_setup_time = scan_delta/slew_speed - exposure_time

    return slew_speed, scan_delta, detector_setup_time


def load_config(yamlfile):
    """load yaml to a dict"""
    with open(yamlfile, 'r') as stream:
        _dict = yaml.safe_load(stream)
    return _dict


def dict_to_msg(input_dict):
    """
    Unfold a nested dictionary to a string.
    To the maximum of 3 levels.
    """
    msg = ""
    for ikey, ivalue in input_dict.items():
        if isinstance(ivalue, dict):
            msg += f"{ikey}:\n"
            for iikey, iivalue in ivalue.items():
                if isinstance(iivalue, dict):
                    _msg_temp = "\n".join(("    {} = {}".format(*iii) for iii in iivalue.items()))
                    msg += f"  {iikey}:\n{_msg_temp} \n"
                else:
                    _msg_temp = f"  {iikey} = {iivalue} \n"
                    msg += _msg_temp
            # msg += "\n"   # toggle this to add lines between blocks
        else:
            _msg_temp = f"{ikey} = {ivalue} \n"
            msg += _msg_temp
    return msg


def innotebook():
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter


def print_dict(input_dict):
    """tabulated HTML output of dictionary"""
    if innotebook():
        outstr = tabulate({
            'name':        list(input_dict.keys()), 
            'description': list(input_dict.values()),
            }, headers="keys", tablefmt='html')
        display(HTML(outstr))
    else:
        print(tabulate({
            'name':        list(input_dict.keys()), 
            'description': list(input_dict.values()),
            }, headers="keys"))


def repeat_exp(plan_func, n=1):
    """
    Quick wrapper to repeat certain experiment, e.g.
    >> RE(repeat_exp(tomo_scan('tomo_scan_config.yml')), 2)
    """
    for _ in range(n):
        yield from plan_func


def is_light_on():
    """
    Return the status of the light inside the hutch
    True: Light is on
    Flase: Light is off
    """

    # Typical diode readings:
    #     Lights on:           ~  0.411 V
    #     Lights fully dimmed: ~  0.302 V
    #     Lights off:          ~ -0.090 V

    from epics import caget
    _diode_voltage = caget("6idADAM:adam_6017:1:AI0")
    if _diode_voltage >0.2:
        return True
    elif _diode_voltage <0.2:
        return False
