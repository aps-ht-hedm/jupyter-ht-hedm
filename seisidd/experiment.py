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
    my_experiment = Experiment(Tomography, config, mode='production')

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
        self.beam = setup.get_beam(mode=self._mode)
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
        """Available modes are ['debug', 'dryrun', 'production']"""
        return self._mode

    @mode.setter
    def mode(self, newmode):
        self._mode = newmode
        self.beam = setup.get_beam(mode=self._mode)
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
            acutal shutter    when [production]
            
        NOTE:
            for 6IDD only
            EXAMPLE:
                    shutter_a = ApsPssShutter("2bma:A_shutter:", name="shutter")
                    shutter_a.open()
                    shutter_a.close()
                    shutter_a.set("open")
                    shutter_a.set("close")
                When using the shutter in a plan, be sure to use ``yield from``, such as::
                    def in_a_plan(shutter):
                        yield from abs_set(shutter, "open", wait=True)
                        # do something
                        yield from abs_set(shutter, "close", wait=True)
                    RE(in_a_plan(shutter_a))
        """
        from .devices.beamline import MainShutter6IDD
        from apstools.devices  import SimulatedApsPssShutterWithStatus
        return {
            'debug': SimulatedApsPssShutterWithStatus(name="A_shutter"),
            'dryrun': SimulatedApsPssShutterWithStatus(name="A_shutter"),
            'production': MainShutter6IDD("6ida1:", name='main_shutter'),
        }[mode]

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
        print(f"Experiment configuration:\n{dict_to_msg(cfg[self._mysetup.setup_name])}")
        print(f"Output:\n{dict_to_msg(cfg['output'])}")

    # NOTE
    # The following methods are wraper of the acutal implementation of different scan plans
    # for various experiment setup
    def scan(self, *args, **kwargs):
        """wrapper of the 360 rotation scan plan"""
        if not self._safe2go:
            print("Cowardly doing a sanity check first")
            summarize_plan(self._mysetup.step_scan(self, *args, **kwargs))
            self._safe2go = True
            print("Now call scan one more time to start RE")
        else:
            self.RE(self._mysetup.step_scan(self, *args, **kwargs))

    def collect_white(self, *args, **kwargs):
        """wrapper of the still white field image acquisition"""
        if not self._safe2go:
            print("Cowardly doing a sanity check first")
            summarize_plan(self._mysetup.collect_white(self, *args, **kwargs))
            self._safe2go = True
            print("Now call scan one more time to start RE")
        else:
            self.RE(self._mysetup.collect_white(self, *args, **kwargs))

    def collect_dark(self, *args, **kwargs):
        """wrapper of the still dark field image acquisition"""
        if not self._safe2go:
            print("Cowardly doing a sanity check first")
            summarize_plan(self._mysetup.collect_dark(self, *args, **kwargs))
            self._safe2go = True
            print("Now call scan one more time to start RE")
        else:
            self.RE(self._mysetup.collect_dark(self, *args, **kwargs))

    # NOTE
    # The following methods are direct call to pyepics, bypassing the RunEngine
    # These functions are primarily for beamline scientist to adjust the experiment
    # settings, and these functions are mostly adapted from existing SPEC scripts
    # TODO
    # Need to consult Jun and Peter to get a list of functions that need to be translated
    # input pyepics


class Tomography:
    """Tomography setup for HT-HEDM instrument"""
    setup_name = 'tomo'

    @staticmethod
    def get_beam(mode):
        return {
            'debug':  SimBeam(),
            'dryrun': Beam(),
            'production': Beam(),
        }[mode]

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

    @staticmethod        
    def get_detector(mode):
        """return the 1idPG4 tomo detector for HT-HEDM"""
        det_PV = {
            'debug':       "6iddSIMDET1:",
            'dryrun':      "1idPG4:",
            'production':  "1idPG4:",
            }[mode]
        
        det = {
            'debug'     :  SimDetector      (det_PV, name='det'),
            'dryrun'    :  PointGreyDetector(det_PV, name='det'),
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
        # Reset trigger mode
        det.cam1.trigger_mode.put('Internal')
        det.cam1.frame_rate_on_off.put(1)
        # ---- get camera ready to keep taking image
        det.cam1.acquire_time.put(0.001)
        det.cam1.acquire_period.put(0.02)
        det.cam1.image_mode.put('Continuous')
        # Enable plugins
        det.image1.enable.put(1)
        det.proc1.enable.put(1)
        det.trans1.enable.put(1)
        # ---- get tiff1 primed
        det.tiff1.auto_increment.put(0)
        det.tiff1.capture.put(0)
        det.tiff1.enable.put(1)
        det.tiff1.file_name.put('prime_my_tiff')
        det.cam1.acquire.put(1)
        sleep(0.5) # safe number, for potential delay
        det.tiff1.enable.put(0)
        det.tiff1.auto_increment.put(1)
        # ---- get hdf1 primed
        det.hdf1.auto_increment.put(0)
        det.hdf1.capture.put(0)
        det.hdf1.enable.put(1)
        det.hdf1.file_name.put('prime_my_hdf')
        sleep(0.01) # safe to sleep shorter
        det.cam1.acquire.put(0)
        det.hdf1.enable.put(0)
        det.hdf1.auto_increment.put(1)
        # ---- turn on auto save (supercede by disable, so we are safe)
        det.tiff1.auto_save.put(1)
        det.hdf1.auto_save.put(1)
        # -- realted to proc1
        det.proc1.filter_callbacks.put(1)   # 0 Every array; 1 Array N only (useful for taking bg)
        det.proc1.auto_reset_filter.put(1)  # ALWAYS auto reset filter
        # -- enter stand-by mode
        det.cam1.image_mode.put('Multiple')

        return det

    @staticmethod
    def collect_white(experiment, atfront=True):
        det = experiment.detector
        tomostage = experiment.stage

        cfg_tomo = experiment.config['tomo']

        # move sample out of the way
        _x = cfg_tomo['fronte_white_kx'] if atfront else cfg_tomo['back_white_kx']
        _z = cfg_tomo['fronte_white_kz'] if atfront else cfg_tomo['back_white_kz']
        yield from bps.mv(tomostage.kx, _x)
        yield from bps.mv(tomostage.kz, _z)

        # setup detector
        # Raw images go through the following plugins:
        #       PG1 ==> TRANS1 ==> PROC1 ==> TIFF1
        #        ||                 ||
        #         ==> IMAGE1         ======> HDF1
        yield from bps.mv(det.proc1.nd_array_port, 'TRANS1')       
        yield from bps.mv(det.hdf1.nd_array_port, 'PROC1')
        yield from bps.mv(det.tiff1.nd_array_port, 'PROC1')
        yield from bps.mv(det.trans1.enable, 1)  
        yield from bps.mv(det.proc1.enable, 1)
        yield from bps.mv(det.proc1.enable_filter, 1)
        yield from bps.mv(det.proc1.filter_type, 'Average')
        yield from bps.mv(det.proc1.reset_filter, 1)
        yield from bps.mv(det.proc1.num_filter, cfg_tomo['n_frames'])
        yield from bps.mv(det.cam1.trigger_mode, "Internal")
        yield from bps.mv(det.cam1.image_mode, "Multiple")
        yield from bps.mv(det.cam1.num_images, cfg_tomo['n_frames']*cfg_tomo['n_white'])
        yield from bps.trigger_and_read([det])

        # move sample back
        yield from bps.mv(tomostage.kx, cfg_tomo['initial_kx'])
        yield from bps.mv(tomostage.kz, cfg_tomo['initial_kz'])


    @staticmethod
    def collect_dark(experiment):
        # NOTE
        # 6IDD does not have an actual fast shutter yet, so we are skipping the
        # fast shutter part for now
        det = experiment.detector

        # Raw images go through the following plugins:
        #       PG1 ==> TRANS1 ==> PROC1 ==> TIFF1
        #                 ||          ||
        #                 ==> IMAGE1  ======> HDF1

        yield from bps.mv(det.proc1.nd_array_port, 'TRANS1')  
        yield from bps.mv(det.hdf1.nd_array_port, 'PROC1')
        yield from bps.mv(det.tiff1.nd_array_port, 'PROC1') 
        yield from bps.mv(det.trans1.enable, 1) 
        yield from bps.mv(det.proc1.enable, 1)
        yield from bps.mv(det.proc1.enable_filter, 1)
        yield from bps.mv(det.proc1.filter_type, 'Average')
        yield from bps.mv(det.proc1.reset_filter, 1)
        yield from bps.mv(det.proc1.num_filter, cfg_tomo['n_frames'])
        yield from bps.mv(det.cam1.trigger_mode, "Internal")
        yield from bps.mv(det.cam1.image_mode, "Multiple")
        yield from bps.mv(det.cam1.num_images, cfg_tomo['n_frames']*cfg_tomo['n_dark'])
        yield from bps.trigger_and_read([det])

    @staticmethod
    def scan(experiment):
        det = experiment.detector
        tomostage = experiment.stage
        mode = experiment.mode
        shutter = experiment.shutter
        shutter_suspender = experiment.suspend_shutter
        cfg = experiment.config
        
        # update the cached motor position in the dict in case exp goes wrong
        _cached_position = tomostage.cache_position()

        #########################
        ## step 0: preparation ##
        #########################
        # Store tomo Cam stage XYZ position
        cfg['tomo']['TomoY'] = det.motors.tomoy.position
        cfg['tomo']['TomoX'] = det.motors.tomox.position
        cfg['tomo']['TomoZ'] = det.motors.tomoz.position

        acquire_time   = cfg['tomo']['acquire_time']
        acquire_period = cfg['tomo']['acquire_period']
        n_white        = cfg['tomo']['n_white']
        n_dark         = cfg['tomo']['n_dark']
        angs = np.arange(
            cfg['tomo']['omega_start'], 
            cfg['tomo']['omega_end']+cfg['tomo']['omega_step']/2,
            cfg['tomo']['omega_step'],
        )
        n_projections = len(angs)
        cfg['tomo']['n_projections'] = n_projections
        cfg['tomo']['total_images']  = n_white + n_projections + n_white + n_dark
        fp = cfg['output']['filepath']
        fn = cfg['output']['fileprefix']

        # TODO
        # consider adding an extra step to:
        #   Perform energy calibration, set intended attenuation
        #   set the lenses, change the intended slit size
        #   prime the control of FS
        
        ###################################
        ## step 1: check beam parameters ##
        ###################################
        # set slit sizes
        # These are the 1-ID-E controls
        #   epics_put("1ide1:Kohzu_E_upHsize.VAL", ($1), 10) ##
        #   epics_put("1ide1:Kohzu_E_dnHsize.VAL", (($1)+0.1), 10) ##
        #   epics_put("1ide1:Kohzu_E_upVsize.VAL", ($2), 10) ## VERT SIZE
        #   epics_put("1ide1:Kohzu_E_dnVsize.VAL", ($2)+0.1, 10) ##
        # _beam_h_size    =   cfg['tomo']['beamsize_h']
        # _beam_v_size    =   cfg['tomo']['beamsize_v']
        # yield from bps.mv(beam.s1.h_size, _beam_h_size          )
        # yield from bps.mv(beam.s1.v_size, _beam_v_size          )
        # yield from bps.mv(beam.s2.h_size, _beam_h_size + 0.1    )       # add 0.1 following 1ID convention
        # yield from bps.mv(beam.s2.v_size, _beam_v_size + 0.1    )       # to safe guard the beam?

        if mode in ['dryrun', 'production']:
            # set attenuation
            _attenuation = cfg['tomo']['attenuation']
            yield from bps.mv(beam.att._motor, _attenuation)
            # check energy
            # need to be clear what we want to do here
            # _energy_foil = cfg['tomo']['energyfoil']
            # yield from bps.mv(beam.foil._motor, _energy_foil)      # need to complete this part in beamline.py
            # TODO:
            #   Instead of setting the beam optics, just check the current setup
            #   and print it out for user infomation.
            # current beam size
            # TODO:
            # use softIOC to provide shortcut to resize slits
#             cfg['tomo']['beamsize_h']     = beam.s1.h_size
#             cfg['tomo']['beamsize_v']     = beam.s1.v_size
            # current lenses (proposed...)
            cfg['tomo']['focus_beam']     = beam.l1.l1y == 10  # to see if focusing is used
            # current attenuation
            cfg['tomo']['attenuation']    = beam.att._motor.get()
            # check energy? may not be necessary.
        
        # TODO:
        #   set up FS controls
        #   decide what to do with the focus lenses

        # calculate slew speed for fly scan
        # https://github.com/decarlof/tomo2bm/blob/master/flir/libs/aps2bm_lib.py
        # TODO: considering blue pixels, use 2BM code as ref
        if cfg['tomo']['type'].lower() == 'fly':
            scan_time = (acquire_time+cfg['tomo']['readout_time'])*n_projections
            slew_speed = (angs.max() - angs.min())/scan_time
            cfg['tomo']['slew_speed'] = slew_speed

        # need to make sure that the sample out position is the same for both front and back
        x0, z0 = tomostage.kx.position, tomostage.kz.position
        dfx, dfz = cfg['tomo']['sample_out_position']['kx'], cfg['tomo']['sample_out_position']['kz']
        rotang = np.radians(cfg['tomo']['omega_end']-cfg['tomo']['omega_start'])
        rotm = np.array([[ np.cos(rotang), np.sin(rotang)],
                         [-np.sin(rotang), np.cos(rotang)]])
        dbxz = np.dot(rotm, np.array([dfx, dfz]))
        dbx = dbxz[0] if abs(dbxz[0]) > 1e-8 else 0.0
        dbz = dbxz[1] if abs(dbxz[1]) > 1e-8 else 0.0
        # now put the value to dict
        cfg['tomo']['initial_kx']       = x0
        cfg['tomo']['initial_kz']       = z0
        cfg['tomo']['fronte_white_kx']  = x0 + dfx
        cfg['tomo']['fronte_white_kz']  = z0 + dfz
        cfg['tomo']['back_white_kx']    = x0 + dbx
        cfg['tomo']['back_white_kz']    = z0 + dbz

        #############################################
        ## step 2: print out the cfg for user info ##
        ############################################# 
        experiment.check(cfg)

        # NOTE: file path cannot be used with bps.mv, leading to a timeout error
        for me in [det.tiff1, det.hdf1]:
            me.file_path.put(fp)

        # Reset Aero rotation to ~0 if didn;t clean up after previous scan
        if tomostage.rot.get() > 300:    
            tomostage.rot._motor_cal_set.put(1)
            tomostage.rot.dial_value.put(tomostage.rot.dial_readback.get()-360)
            tomostage.rot._off_value.put(0)
            tomostage.rot._motor_cal_set.put(0) 
        
        ################################
        ## step 3: Check light status ##
        ################################
        while is_light_on():
            print('\a')
            print("Light is on inside the Hutch!!!")
            print("Turn off the light!!!")
            print('\a')
            print('\n')
            sleep(5)

        #########################
        ## step 4: Actual Scan ##
        #########################

        @bpp.finalize_decorator(safe_guard(experiment))
        @bpp.stage_decorator([det])
        @bpp.run_decorator()
        def scan_closure():
            # TODO:
            # Somewhere we need to check the light status
            # open shutter for beam
            if mode.lower() in ['production']:
                yield from bps.mv(shutter, 'open')
                yield from bps.install_suspender(shutter_suspender)
            # config output
            if mode.lower() in ['dryrun','production']:
                for me in [det.tiff1, det.hdf1]:
                    yield from bps.mv(me.file_name, fn)
                    # yield from bps.mv(me.file_path, fp)
                    yield from bps.mv(me.file_write_mode, 2)  # 1: capture, 2: stream
                    yield from bps.mv(me.num_capture, cfg['tomo']['total_images'])
                    yield from bps.mv(me.file_template, ".".join([r"%s%s_%06d",cfg['output']['type'].lower()]))    
            elif mode.lower() in ['debug']:
                for me in [det.tiff1, det.hdf1]:
                    # TODO: file path will lead to time out error in Sim test
                    # yield from bps.mv(me.file_path, '/data')
                    yield from bps.mv(me.file_name, fn)
                    yield from bps.mv(me.file_write_mode, 2) # 1: capture, 2: stream
                    yield from bps.mv(me.auto_increment, 1)
                    yield from bps.mv(me.num_capture, cfg['tomo']['total_images'])
                    yield from bps.mv(me.file_template, ".".join([r"%s%s_%06d",cfg['output']['type'].lower()]))
            
            if cfg['output']['type'] in ['tif', 'tiff']:
                yield from bps.mv(det.tiff1.enable, 1)
                yield from bps.mv(det.tiff1.capture, 1)
                yield from bps.mv(det.hdf1.enable, 0)
            elif cfg['output']['type'] in ['hdf', 'hdf1', 'hdf5']:
                yield from bps.mv(det.tiff1.enable, 0)
                yield from bps.mv(det.hdf1.enable, 1)
                yield from bps.mv(det.hdf1.capture, 1)
            else:
                raise ValueError(f"Unsupported output type {cfg['output']['type']}")

            # setting acquire_time and acquire_period
            yield from bps.mv(det.cam1.acquire_time, acquire_time)
            yield from bps.mv(det.cam1.acquire_period, acquire_period)    
                
            # collect front white field
            yield from bps.mv(det.cam1.frame_type, 0)  # for HDF5 dxchange data structure
            yield from Tomography.collect_white(experiment, atfront=True)
    
            # collect projections
            yield from bps.mv(det.cam1.frame_type, 1)  # for HDF5 dxchange data structure
            if cfg['tomo']['type'].lower() == 'step':
                yield from Tomography.step_scan(experiment)
            elif cfg['tomo']['type'].lower() == 'fly':
                yield from Tomography.fly_scan(experiment)
            else:
                raise ValueError(f"Unsupported scan type: {cfg['tomo']['type']}")
    
            # collect back white field
            yield from bps.mv(det.cam1.frame_type, 2)  # for HDF5 dxchange data structure
            yield from Tomography.collect_white(experiment, atfront=False)
    
            # collect back dark field
            yield from bps.mv(det.cam1.frame_type, 3)  # for HDF5 dxchange data structure
            
            # TODO: no shutter available for Sim testing
            if mode.lower() in ['dryrun', 'production']:
                yield from bps.remove_suspender(shutter_suspender)
                yield from bps.mv(shutter, "close")

            yield from Tomography.collect_dark(experiment)
    
        return (yield from scan_closure())

    @staticmethod
    def step_scan(experiment):
        det = experiment.detector
        tomostage = experiment.stage
        cfg_tomo = experiment.config['tomo']

        # Raw images go through the following plugins:
        #       PG1 ==> TRANS1 ==> PROC1 ==> TIFF1
        #                 ||          ||
        #                 ==> IMAGE1  ======> HDF1
        yield from bps.mv(det.proc1.nd_array_port, 'TRANS1')
        yield from bps.mv(det.hdf1.nd_array_port, 'PROC1')
        yield from bps.mv(det.tiff1.nd_array_port, 'PROC1') 
        yield from bps.mv(det.trans1.enable, 1) 
        yield from bps.mv(det.proc1.enable, 1)
        yield from bps.mv(det.proc1.enable_filter, 1)
        yield from bps.mv(det.proc1.filter_type, 'Average')
        yield from bps.mv(det.proc1.reset_filter, 1)
        yield from bps.mv(det.proc1.num_filter, cfg_tomo['n_frames'])
        yield from bps.mv(det.cam1.num_images, cfg_tomo['n_frames'])

        angs = np.arange(
            cfg_tomo['omega_start'], 
            cfg_tomo['omega_end']+cfg_tomo['omega_step']/2,
            cfg_tomo['omega_step'],
        )
        for ang in angs:
            yield from bps.checkpoint()
            yield from bps.mv(tomostage.rot, ang)
            yield from bps.trigger_and_read([det])

    @staticmethod
    def fly_scan(experiment):
        det = experiment.detector
        psofly = experiment.flycontrol
        cfg_tomo = experiment.config['tomo']

        # Raw images go through the following plugins:
        #       PG1 ==> TRANS1 ==> PROC1 ==> TIFF1
        #                 ||          ||
        #                 ==> IMAGE1  ======> HDF1
        yield from bps.mv(det.proc1.nd_array_port, 'TRANS1')
        yield from bps.mv(det.hdf1.nd_array_port, 'PROC1')
        yield from bps.mv(det.tiff1.nd_array_port, 'PROC1') 
        yield from bps.mv(det.trans1.enable, 1) 
        yield from bps.mv(det.proc1.enable, 1)
        yield from bps.mv(det.proc1.enable_filter, 1)
        yield from bps.mv(det.proc1.filter_type, 'Average')
        yield from bps.mv(det.proc1.reset_filter, 1)
        yield from bps.mv(det.proc1.num_filter, cfg_tomo['n_frames'])
        yield from bps.mv(det.cam1.num_images, cfg_tomo['n_frames'])

        # we are assuming that the global psofly is available
        yield from bps.mv(
            psofly.start,               cfg_tomo['omega_start'],
            psofly.end,                 cfg_tomo['omega_end'],
            psofly.slew_speed,          cfg_tomo['slew_speed'],
            psofly.scan_delta,          cfg_tomo['scan_delta'],
            psofly.detector_setup_time, cfg_tomo['detector_setup_time'],
            )
        # preparation for PSO signal 
        yield from bps.mv(psofly.pulse_type, "Gate")
        yield from bps.mv(psofly.reset_fgpa, "1")  # caput(6idMZ1:SG:BUFFER-1_IN_Signal.PROC, 1), reest FPGA circutry 
        yield from bps.mv(psofly.pso_state,  "0")  # caput(6idMZ1:SG:AND-1_IN1_Signal,        0), disable PSO singal prevent accidental trigger
        # taxi
        yield from bps.mv(stage.rot, cfg_tomo['omega_start'])
        yield from bps.mv(psofly.taxi, "Taxi")     # should be equivalent to: caput(6idhedms1:PSOFly1:taxi, "Taxi")
                                                   # Aerotech cannot be in "stop" when use flyer
        yield from bps.mv(
            det.cam1.num_images, cfg_tomo['n_projections'],
            det.cam1.trigger_mode, "Ext. Standard",
        )
        # ready to fly
        yield from bps.mv(psofly.pso_state,  "1")  # caput(6idMZ1:SG:AND-1_IN1_Signal,        1) , re-enable PSO singal
        # start the fly scan
        yield from bps.trigger(det, group='fly')
        yield from bps.abs_set(psofly.fly, "Fly", group='fly')
        yield from bps.wait(group='fly')
        # safe guard against accidental triggering
        yield from bps.mv(psofly.pso_state,  "0")  # caput(6idMZ1:SG:AND-1_IN1_Signal,        0), disable PSO singal prevent accidental trigger

    @staticmethod
    def safe_guard(experiment):
        """
        A plan that guarantees
        1. reset FPGA board
        2. disable PSO signal to prevent accidental trigger
        3. disable cam and its plugins in case of emergency stop
        """
        det = experiment.tomo_det
        psofly = experiment.fly_control
        
        yield from bps.mv(psofly.reset_fgpa, "1")  # caput(6idMZ1:SG:BUFFER-1_IN_Signal.PROC, 1), reest FPGA circutry 
        yield from bps.mv(psofly.pso_state,  "0")  # caput(6idMZ1:SG:AND-1_IN1_Signal,        0), disable PSO singal prevent accidental trigger
        
        # TODO
        # decided whether it is safe to force reset detector here...

class FarField:
    """Far-Field HEDM scan setup for HT-HEDM instrument"""

    @staticmethod
    def get_stage(mode):
        """return the aerotech stage configuration"""
        return {
            "dryrun":     StageAero(name='ffstage'),
            "production": StageAero(name='ffstage'),
            "debug":      SimStageAero(name='ffstage'),
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


class NearField:
    """Near-Fiedl HEDM scan setup for HT-HEDM instrument"""

    pass


if __name__ == "__main__":
    print("Example usage see corresponding notebooks")
