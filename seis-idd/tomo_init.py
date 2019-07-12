#!/usr/bin/env python

# ----- Ipython control config and standard library import ----- #
import os
import socket
import getpass
import bluesky
import ophyd
import apstools
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime


# --- keywords tracking
keywords_vars = {}  # {name: short description}
keywords_func = {}  # {name: short descciption}
from utility import print_dict
list_predefined_vars = lambda : print_dict(keywords_vars)
list_predefined_func = lambda : print_dict(keywords_func)


# --- get system info
HOSTNAME = socket.gethostname() or 'localhost'
USERNAME = getpass.getuser() or '6-BM-A user'
keywords_vars['HOSTNAME'] = 'host name'
keywords_vars['USERNAME'] = 'PI/user name'


# --- setup metadata handler
from databroker import Broker
metadata_db = Broker.named("mongodb_config")
keywords_vars['metadata_db'] = 'Default metadata handler'


# --- setup RunEngine
from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
keywords_func['get_runengine'] = 'Get a bluesky RunEngine'
def get_runengine(db=None):
    """
    Return an instance of RunEngine.  It is recommended to have only
    one RunEngine per session.
    """
    RE = RunEngine({})
    db = metadata_db if db is None else db
    RE.subscribe(db.insert)
    RE.subscribe(BestEffortCallback())
    return RE

RE = get_runengine()
keywords_vars['RE'] = 'Default RunEngine instance'


# --- import utility functions
from utility import load_config
keywords_func['load_config'] = load_config.__doc__


# --- load devices info from yaml file
_devices = load_config('seis-idd/config/tomo_devices.yml')


# --- exp safeguard suspender
from bluesky.suspenders import SuspendFloor


# --- define shutter
keywords_func['get_shutter'] = 'Return a connection to a sim/real shutter'
def get_shutter(mode='debug'):
    """
    return
        simulated shutter <-- dryrun, debug
        acutal shutter    <-- production
    """
    import apstools.devices as APS_devices
    aps = APS_devices.ApsMachineParametersDevice(name="APS")

    if mode.lower() in ['debug', 'dryrun']:
        A_shutter = APS_devices.SimulatedApsPssShutterWithStatus(name="A_shutter")
    elif mode.lower() == 'production':
        A_shutter = APS_devices.ApsPssShutterWithStatus(
            _devices['A_shutter'][0],
            _devices['A_shutter'][1],
            name="A_shutter",
        )
        suspend_APS_current = SuspendFloor(aps.current, 2, resume_thresh=10)
        RE.install_suspender(suspend_APS_current)
    else:
        raise ValueError(f"🙉: invalide mode, {mode}")

    return A_shutter

A_shutter = get_shutter(mode='debug')
keywords_vars['A_shutter'] = "shutter instance"
# no scans until A_shutter is open
suspend_A_shutter = None  # place holder
keywords_vars['suspend_A_shutter'] = "no scans until A_shutter is open"


# --- define motor
from ophyd import MotorBundle
from ophyd import Component
from ophyd import EpicsMotor
from ophyd import sim

class TomoStage(MotorBundle):
    #rotation
    preci = Component(EpicsMotor, _devices['tomo_stage']['preci'], name='preci')    
    samX  = Component(EpicsMotor, _devices['tomo_stage']['samX' ], name='samX' )
    ksamx = Component(EpicsMotor, _devices['tomo_stage']['ksamx'], name='ksamx')
    samY  = Component(EpicsMotor, _devices['tomo_stage']["samY" ], name="samY" )

keywords_func['get_motors'] = 'Return a connection to sim/real tomostage motor'
def get_motors(mode="debug"):
    """
    sim motor <-- debug
    aerotech  <-- dryrun, production
    """
    if mode.lower() == 'debug':
        tomostage = TomoStage(name='tomostage')
    elif mode.lower() in ['dryrun', 'production']:
        tomostage = MotorBundle(name="tomostage")
        tomostage.preci = sim.motor
        tomostage.samX  = sim.motor
        tomostage.samY  = sim.motor
    else:
        raise ValueError(f"🙉: invalide mode, {mode}")
    return tomostage

tomostage = get_motors(mode='debug')
keywords_vars['tomostage'] = 'sim/real tomo stage'
preci = tomostage.preci
keywords_vars['preci'] = 'rotation control'
samX = tomostage.samX
keywords_vars['samX'] = 'tomo stage x-translation'
ksamx = tomostage.ksamx
keywords_vars['ksamx'] = '?'
samY = tomostage.samY
keywords_vars['samY'] = 'tomo stage y-translation'


# --- define psofly control 
from ophyd import EpicsSignal
from ophyd import EpicsSignalRO
from ophyd import Device
import bluesky.plan_stubs as bps

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
    fly = Component(EpicsSignal, "fly", put_complete=True)
    
    def plan(self):
        yield from bps.mv(self.taxi, self.taxi.enum_strs[1])
        yield from bps.mv(self.fly, self.fly.enum_strs[1])

class EnsemblePSOFlyDevice(TaxiFlyScanDevice):
    motor_pv_name = Component(EpicsSignalRO, "motorName")
    start = Component(EpicsSignal, "startPos")
    end = Component(EpicsSignal, "endPos")
    slew_speed = Component(EpicsSignal, "slewSpeed")

    # scan_delta: output a trigger pulse when motor moves this increment
    scan_delta = Component(EpicsSignal, "scanDelta")

    # advanced controls
    delta_time = Component(EpicsSignalRO, "deltaTime")
    # detector_setup_time = Component(EpicsSignal, "detSetupTime")
    # pulse_type = Component(EpicsSignal, "pulseType")

    scan_control = Component(EpicsSignal, "scanControl")

keywords_func['get_fly_motor'] = 'Return a connection to fly IOC control'
def get_fly_motor(mode='debug'):
    """
    sim motor <-- debug
    fly motor <-- dryrun, production
    """
    if mode.lower() == 'debug':
        psofly = sim.flyer1
    elif mode.lower() in ['dryrun', 'production']:
        psofly = EnsemblePSOFlyDevice(_devices['tomo_stage']['psofly'], name="psofly")
    else:
        raise ValueError(f"🙉: invalide mode, {mode}")
    return psofly

psofly = get_fly_motor(mode='debug')
keywords_vars['psofly'] = 'fly control instance'


# --- define detector


