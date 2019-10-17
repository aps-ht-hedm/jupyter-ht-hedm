#!/usr/bin/env python

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

from  .devices.beamline              import Beam, SimBeam
from  .devices.beamline              import FastShutter
from  .devices.motors                import StageAero, SimStageAero
from  .devices.motors                import EnsemblePSOFlyDevice
from  .devices.detectors             import PointGreyDetector, DexelaDetector, SimDetector  
from  .util                          import dict_to_msg
from  .util                          import load_config

import bluesky.preprocessors as bpp
import bluesky.plan_stubs    as bps


class Experiment:
    """Generic expriment handler"""

    def __init__(self, mode='debug'):
        self.RE = bluesky.RunEngine({})
        # self.db = databroker.Broker.named("mongodb_config")
        # self.RE.subscribe(self.db.insert)
        self.RE.subscribe(BestEffortCallback())

        self._mode   = mode
        if mode.lower() in ['production']:
            from apstools.devices import ApsMachineParametersDevice
            self._aps    = ApsMachineParametersDevice(name="APS")
            self.shutter = Experiment.get_main_shutter(mode)
            self.suspend_shutter = SuspendFloor(self.shutter.pss_state, 1)

        # TODO:
        # create fast shutter here
        # for 1id the fast shutter PV is 
        # FS1PV: 1id:softGlue:AND-1_IN1_Signal
        # FS2PV: 1id:softGlue:AND-2_IN1_Signal
        # There are also mask PVs to enable and disable FS control with different signals
        # FS1maskPV: 1id:softGlue:AND-1_IN2_Signal
        # FS2maskPV: 1id:softGlue:AND-2_IN2_Signal
        # The mask PV is used to trigger the FS with other hardware triggers
        # mostly along with the detector, so that beam is off when not acquiring
        # i.e. control with sweep: epics_put(sprintf("%s",FS_control_PV), "Sweep", SGtime)
        # still not entirely sure how this works, maybe bluesky already has this trigger mode?


        # monitor APS current
        if mode.lower() in ['dryrun', 'production']:
            self.suspend_APS_current = SuspendFloor(self._aps.current, 2, resume_thresh=10)
            self.RE.install_suspender(self.suspend_APS_current)

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
    
class Tomography(Experiment):
    """Tomography experiment control for 6-ID-D."""
    
    def __init__(self, mode='debug'):
        Experiment.__init__(self, mode)
        self._mode = mode
        # instantiate device
        self.tomo_stage  = Tomography.get_tomostage(self._mode)
        self.fly_control = Tomography.get_flycontrol(self._mode)
        self.tomo_det    = Tomography.get_detector(self._mode)
        self.tomo_beam   = Tomography.get_tomobeam(self._mode)
        # TODO:
        # we need to do some initialization with Beam based on 
        # a cached/lookup table
    
    @property
    def mode(self):
        return f"current mode is {self._mode}, available options are ['debug', 'dryrun', 'production']"
    
    @mode.setter
    def mode(self, newmode):
        self._mode       = newmode
        self.shutter     = Experiment.get_main_shutter(self._mode)
        self.tomo_stage  = Tomography.get_tomostage(self._mode)
        self.fly_control = Tomography.get_flycontrol(self._mode)
        self.tomo_det    = Tomography.get_detector(self._mode)
        self.tomo_beam   = Tomography.get_tomobeam(self._mode)
         
    def check(self, cfg):
        """Return user input before run"""
        print(f"Tomo configuration:\n{dict_to_msg(cfg['tomo'])}")
        print(f"Output:\n{dict_to_msg(cfg['output'])}")


    def __repr__(self):
        """Return summary of the current experiment status"""
        """
        beam  = self.tomo_beam
        stage = self.tomo_stage
        # get the current beamline optics
        # TODO: need to figure out how to get the beam energy
        # commented out for sim testing
        
        _beamline_status = (
                           f"Beam Size is:   {beam.s1.h_size}x{beam.s1.v_size} (HxV) \n"
                           f"Attenuation is: {beam.att_level}                        \n"
                           f"Beam Energy is: {beam.energy}                           \n"   
                           f"Focus Lenses Positions: l1y @ {beam.l1.l1y}             \n"    
                           f"                        l2y @ {beam.l2.l2y}             \n"    
                           f"                        l3y @ {beam.l3.l3y}             \n"    
                           f"                        l4y @ {beam.l4.l4y}             \n"         
                           )
        

        _status_msg = (
                        (f"Here is the current beamline status:\n")            +
                        _beamline_status                                       +
                        (f"\nHere are the current motor positions:\n")         +
                        dict_to_msg(stage.position_cached)                     +
                        (f"\nHere is the current experiment configuration:\n") 
                        # dict_to_msg(cfg['tomo'])                               +
                        # (f"\nHere are the file output info:\n")                +
                        # dict_to_msg(cfg['output'])
                      )
        return _status_msg
        """

        # TODO:
        #   verbose string representation of the experiment and beamline
        #   status as a dictionary -> yaml 

    def calibration(self):
        """Perform beamline calibration"""
        # TODO:
        #  Still not clear how calibration can be done automatically, but
        #  let's keep a function here as a place holder
        #  Check out this auto alignment to see if some functions can be used here
        #  https://github.com/AdvancedPhotonSource/auto_sample_alignment.git
        #  Per conversation with Peter, This package can return the same location on the pin
        #  according to the images.  However, they are requesting more features like determine 
        #  the slit position and size.
        #  Jun and Peter will test this code during the first week of October, let wait for their feedback.
        
        pass

    @staticmethod
    def get_tomobeam(mode):
        """return Tomobeam based on given mode"""
        if mode.lower() in ['dryrun', 'production']:
            beam = Beam()
        elif mode.lower() == 'debug':
            # NOTE:
            #   This is a place holder for maybe additional control of the beam
            #   simulated tomobeam from the virtual beamline
            #   dumped all the simulated beam control to m16
            beam = SimBeam()
        else:
            raise ValueError(f"Invalide mode -> {mode}")
        return beam

    @staticmethod
    def get_tomostage(mode):
        """return tomostage based on given mode"""
        if mode.lower() in ['dryrun', 'production']:
            tomostage = StageAero(name='tomostage')
        elif mode.lower() == 'debug':
            # NOTE:
            #    Using SimStageAero from the Virtual Beamline.
            tomostage = SimStageAero(name='tomostage')
        else:
            raise ValueError(f"Invalide mode -> {mode}")
        return tomostage

    @staticmethod
    def get_flycontrol(mode):
        # We may have a different version of psofly
        if mode.lower() == 'debug':
            # TODO: need better simulated motors
            from ophyd import sim
            psofly = sim.flyer1
        elif mode.lower() in ['dryrun', 'production']:
            psofly = EnsemblePSOFlyDevice("PV_FLY", name="psofly")
        else:
            raise ValueError(f"Invalide mode, {mode}")
        return psofly

    @staticmethod
    def get_detector(mode):
        # TODO: implement real PVs
        if mode.lower() == 'debug':
            det = SimDetector("6iddSIMDET1:", name='det')

            epics.caput("6iddSIMDET1:cam1:FrameType.ZRST", "/exchange/data_white_pre")
            epics.caput("6iddSIMDET1:cam1:FrameType.ONST", "/exchange/data")
            epics.caput("6iddSIMDET1:cam1:FrameType.TWST", "/exchange/data_white_post")
            epics.caput("6iddSIMDET1:cam1:FrameType.THST", "/exchange/data_dark")
            # ophyd need this configuration
            epics.caput("6iddSIMDET1:cam1:FrameType_RBV.ZRST", "/exchange/data_white_pre")
            epics.caput("6iddSIMDET1:cam1:FrameType_RBV.ONST", "/exchange/data")
            epics.caput("6iddSIMDET1:cam1:FrameType_RBV.TWST", "/exchange/data_white_post")
            epics.caput("6iddSIMDET1:cam1:FrameType_RBV.THST", "/exchange/data_dark")
            # set the layout file for cam
            # TODO:  need to udpate with acutal config files for 6-ID-D
            # TODO: commented for Sim test
            # _current_fp = str(pathlib.Path(__file__).parent.absolute())
            # _attrib_fp = os.path.join(_current_fp, 'config/PG2_attributes.xml')
            # _layout_fp = os.path.join(_current_fp, 'config/tomo6bma_layout.xml')
            # det.cam1.nd_attributes_file.put(_attrib_fp)
            # det.hdf1.xml_file_name.put(_layout_fp)
            # turn off the problematic auto setting in cam1
            # det.cam1.auto_exposure_auto_mode.put(0)  
            # det.cam1.sharpness_auto_mode.put(0)
            # det.cam1.gain_auto_mode.put(0)
            # det.cam1.frame_rate_auto_mode.put(0)
        elif mode.lower() in ['dryrun', 'production']:
            #   need to check this name for assigning the detector
            det = PointGreyDetector("PV_DET", name='det')
            # check the following page for important information
            # https://github.com/BCDA-APS/use_bluesky/blob/master/notebooks/sandbox/images_darks_flats.ipynb
            #
            epics.caput("PV_DET:cam1:FrameType.ZRST", "/exchange/data_white_pre")
            epics.caput("PV_DET:cam1:FrameType.ONST", "/exchange/data")
            epics.caput("PV_DET:cam1:FrameType.TWST", "/exchange/data_white_post")
            epics.caput("PV_DET:cam1:FrameType.THST", "/exchange/data_dark")
            # ophyd need this configuration
            epics.caput("PV_DET:cam1:FrameType_RBV.ZRST", "/exchange/data_white_pre")
            epics.caput("PV_DET:cam1:FrameType_RBV.ONST", "/exchange/data")
            epics.caput("PV_DET:cam1:FrameType_RBV.TWST", "/exchange/data_white_post")
            epics.caput("PV_DET:cam1:FrameType_RBV.THST", "/exchange/data_dark")
            # set the layout file for cam
            # TODO:  need to udpate with acutal config files for 6-ID-D
            _current_fp = str(pathlib.Path(__file__).parent.absolute())
            _attrib_fp = os.path.join(_current_fp, 'config/PG2_attributes.xml')
            _layout_fp = os.path.join(_current_fp, 'config/tomo6bma_layout.xml')
            det.cam1.nd_attributes_file.put(_attrib_fp)
            det.hdf1.xml_file_name.put(_layout_fp)
            # turn off the problematic auto setting in cam1
            det.cam1.auto_exposure_auto_mode.put(0)  
            det.cam1.sharpness_auto_mode.put(0)
            det.cam1.gain_auto_mode.put(0)
            det.cam1.frame_rate_auto_mode.put(0)
        else:
            raise ValueError(f"Invalide mode, {mode}")
        return det

    # ----- pre-defined scan plans starts from here
    def collect_white_field(self, cfg_tomo, atfront=True):
        """
        Collect white/flat field images by moving the sample out of the FOV
        """
        # unpack devices
        det = self.tomo_det
        tomostage = self.tomo_stage
    
        # move sample out of the way
        # TODO:
        # the details and fields need to be updated for 6-ID-D
        _x = cfg_tomo['fronte_white_kx'] if atfront else cfg_tomo['back_white_kx']
        _z = cfg_tomo['fronte_white_kz'] if atfront else cfg_tomo['back_white_kz']
        yield from bps.mv(tomostage.kx, _x)  #update with correct motor name
        yield from bps.mv(tomostage.kz, _z)
    
        # setup detector
        # TODO:
        # actual implementation need to be for 6-ID-D
        yield from bps.mv(det.hdf1.nd_array_port, 'PROC1')
        yield from bps.mv(det.tiff1.nd_array_port, 'PROC1') 
        yield from bps.mv(det.proc1.enable, 1)
        yield from bps.mv(det.proc1.reset_filter, 1)
        yield from bps.mv(det.proc1.num_filter, cfg_tomo['n_frames'])
        yield from bps.mv(det.cam1.trigger_mode, "Internal")
        yield from bps.mv(det.cam1.image_mode, "Multiple")
        yield from bps.mv(det.cam1.num_images, cfg_tomo['n_frames']*cfg_tomo['n_white'])
        yield from bps.trigger_and_read([det])
    
        # move sample back to FOV
        # NOTE:
        # not sure is this will work or not...
        # TODO:
        #   need to update all the motor names according to StageAero
        yield from bps.mv(tomostage.kx, cfg_tomo['initial_kx'])
        yield from bps.mv(tomostage.kz, cfg_tomo['initial_kz'])
    
    def collect_dark_field(self, cfg_tomo):
        """
        Collect dark field images by close the shutter
        """
        # TODO:
        #   Need to toggle Fast shutter
        det = self.tomo_det
    
        yield from bps.mv(det.hdf1.nd_array_port, 'PROC1')
        yield from bps.mv(det.tiff1.nd_array_port, 'PROC1') 
        yield from bps.mv(det.proc1.enable, 1)
        yield from bps.mv(det.proc1.reset_filter, 1)
        yield from bps.mv(det.proc1.num_filter, cfg_tomo['n_frames'])
        yield from bps.mv(det.cam1.trigger_mode, "Internal")
        yield from bps.mv(det.cam1.image_mode, "Multiple")
        yield from bps.mv(det.cam1.num_images, cfg_tomo['n_frames']*cfg_tomo['n_dark'])
        yield from bps.trigger_and_read([det])

    def step_scan(self, cfg_tomo):
        """
        Collect projections with step motion
        """
        # unpack devices
        det = self.tomo_det
        tomostage = self.tomo_stage
        
        # TODO:
        # the fields need to be updated for 6-ID-D
        yield from bps.mv(det.hdf1.nd_array_port, 'PROC1')
        yield from bps.mv(det.tiff1.nd_array_port, 'PROC1') 
        yield from bps.mv(det.proc1.enable, 1)
        yield from bps.mv(det.proc1.reset_filter, 1)
        yield from bps.mv(det.proc1.num_filter, cfg_tomo['n_frames'])
   
        angs = np.arange(
            cfg_tomo['omega_start'], 
            cfg_tomo['omega_end']+cfg_tomo['omega_step']/2,
            cfg_tomo['omega_step'],
        )
        for ang in angs:
            yield from bps.checkpoint()
            yield from bps.mv(tomostage.rot, ang)
            yield from bps.trigger_and_read([det])

    def fly_scan(self, cfg_tomo):
        """
        Collect projections with fly motion
        """
        det = self.tomo_det
        psofly = self.fly_control
        
        # TODO:
        #   The fields need to be updated for 6-ID-D
        yield from bps.mv(det.hdf1.nd_array_port, 'PG1')
        yield from bps.mv(det.tiff1.nd_array_port, 'PG1')
    
        # we are assuming that the global psofly is available
        yield from bps.mv(
            psofly.start,           cfg_tomo['omega_start'],
            psofly.end,             cfg_tomo['omega_end'],
            psofly.scan_delta,      abs(cfg_tomo['omega_step']),
            psofly.slew_speed,      cfg_tomo['slew_speed'],
        )
        # taxi
        yield from bps.mv(psofly.taxi, "Taxi")
        yield from bps.mv(
            det.cam1.num_images, cfg_tomo['n_projections'],
            det.cam1.trigger_mode, "Overlapped",
        )
        # start the fly scan
        yield from bps.trigger(det, group='fly')
        yield from bps.abs_set(psofly.fly, "Fly", group='fly')
        yield from bps.wait(group='fly')

    def tomo_scan(self, cfg):
        """
        Tomography scan plan based on given configuration
        """
        # unpack devices
        det                 = self.tomo_det
        tomostage           = self.tomo_stage
        # TODO: commented for Sim test
        # shutter             = self.shutter
        # shutter_suspender   = self.suspend_shutter
        beam                = self.tomo_beam
        
        # load experiment configurations
        cfg = load_config(cfg) if type(cfg) != dict else cfg
        
        # TODO:
        # the following needs to be updated for 6-ID-D

        # update the cached motor position in the dict in case exp goes wrong
        _cached_position = self.tomo_stage.cache_position()
    
        #########################
        ## step 0: preparation ##
        #########################
        acquire_time   = cfg['tomo']['acquire_time']
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

        # consider adding an extra step to:
        #   Perform energy calibration, set intended attenuation
        #   set the lenses, change the intended slit size
        #   prime the control of FS

        #####################################
        ## step 0.1: check beam parameters ##
        #####################################
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

        # # set attenuation
        # _attenuation = cfg['tomo']['attenuation']
        # yield from bps.mv(beam.att.att_level, _attenuation)

        # # check energy
        # # need to be clear what we want to do here
        # _energy_foil = cfg['tomo']['energyfoil']
        # yield from bps.mv(beam.foil, _energy_foil)      # need to complete this part in beamline.py

        # TODO:
        #   Instead of setting the beam optics, just check the current setup
        #   and print it out for user infomation.
        # current beam size

        # cfg['tomo']['beamsize_h']     = beam.s1.h_size
        # cfg['tomo']['beamsize_v']     = beam.s1.v_size

        # current lenses (proposed...)

        # cfg['tomo']['focus_beam']     = beam.l1.l1y == 10  # to see if focusing is used
        
        # current attenuation
        # TODO: Commented for Sim testing
        # cfg['tomo']['attenuation']    = beam.att.att_level
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
        
        ###############################################
        ## step 0.9: print out the cfg for user info ##
        ############################################### 
        self.check(cfg)    

        @bpp.stage_decorator([det])
        @bpp.run_decorator()
        def scan_closure():
            # TODO:
            #   Somewhere we need to check the light status
            # open shutter for beam
            if self._mode.lower() in ['production']:
                yield from bps.mv(shutter, 'open')
                yield from bps.install_suspender(shutter_suspender)
            # config output
            if self._mode.lower() in ['dryrun','production']:
                for me in [det.tiff1, det.hdf1]:
                    yield from bps.mv(me.file_path, fp)
                    yield from bps.mv(me.file_name, fn)
                    yield from bps.mv(me.file_write_mode, 2)
                    yield from bps.mv(me.num_capture, cfg['tomo']['total_images'])
                    yield from bps.mv(me.file_template, ".".join([r"%s%s_%06d",cfg['output']['type'].lower()]))    
            elif self._mode.lower() in ['debug']:
                for me in [det.tiff1, det.hdf1]:
                    # TODO: file path will lead to time out error
                    # yield from bps.mv(me.file_path, '/data')
                    yield from bps.mv(me.file_name, fn)
                    yield from bps.mv(me.file_write_mode, 2)
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
            
            # setting camera parameters
            yield from bps.mv(det.cam1.acquire_time, acquire_time)

            # collect front white field
            yield from bps.mv(det.cam1.frame_type, 0)  # for HDF5 dxchange data structure
            yield from self.collect_white_field(cfg['tomo'], atfront=True)
    
            # collect projections
            yield from bps.mv(det.cam1.frame_type, 1)  # for HDF5 dxchange data structure
            if cfg['tomo']['type'].lower() == 'step':
                yield from self.step_scan(cfg['tomo'])
            elif cfg['tomo']['type'].lower() == 'fly':
                yield from self.fly_scan(cfg['tomo'])
            else:
                raise ValueError(f"Unsupported scan type: {cfg['tomo']['type']}")
    
            # collect back white field
            yield from bps.mv(det.cam1.frame_type, 2)  # for HDF5 dxchange data structure
            yield from self.collect_white_field(cfg['tomo'], atfront=False)
    
            # collect back dark field
            yield from bps.mv(det.cam1.frame_type, 3)  # for HDF5 dxchange data structure
            # TODO: commented for Sim test
            # yield from bps.remove_suspender(shutter_suspender)
            # yield from bps.mv(shutter, "close")
            yield from self.collect_dark_field(cfg['tomo'])
    
        return (yield from scan_closure())
    
    #   summarize_plan with config yml file
    def dryrun(self, scan_config):
        """use summarize_plan for quick analysis"""
        return summarize_plan(self.tomo_scan(scan_config))

    def run(self,scan_config):
        """run tomo_scan with RE"""
        return self.RE(self.tomo_scan(scan_config))


class NearField(Experiment):
    """NF-HEDM control for 6-ID-D"""
    
    def __init__(self, mode='debug'):
        Experiment.__init__(self, mode)
        self._mode = mode
        # instantiate device
        self.nf_stage       = NearField.get_nfstage(self._mode)
        self.fly_control    = NearField.get_flycontrol(self._mode)
        self.nf_det         = NearField.get_detector(self._mode)
        self.nf_beam        = NearField.get_nfbeam(self._mode)
        # TODO:
        # we need to do some initialization with Beam based on 
        # a cached/lookup table
        # 
    def check(self, cfg):
        """Return user input before run"""
        print(f"NearField configuration:\n{dict_to_msg(cfg['nf'])}")
        print(f"Output:\n{dict_to_msg(cfg['output'])}")

    def __repr__(self):
        """Return summary of the current experiment status"""
        """
        beam  = self.nf_beam
        stage = self.nf_stage
        # get the current beamline optics
        # TODO: need to figure out how to get the beam energy
        _beamline_status = (
                           f"Beam Size is:   {beam.s1.h_size}x{beam.s1.v_size} (HxV) \n"
                           f"Attenuation is: {beam.att_level}                        \n"
                           f"Beam Energy is: {beam.energy}                           \n"   
                           f"Focus Lenses Positions: l1y @ {beam.l1.l1y}             \n"    
                           f"                        l2y @ {beam.l2.l2y}             \n"    
                           f"                        l3y @ {beam.l3.l3y}             \n"    
                           f"                        l4y @ {beam.l4.l4y}             \n"         
                           )

        _status_msg = (
                        (f"Here is the current beamline status:\n")            +
                        _beamline_status                                       +
                        (f"\nHere are the current motor positions:\n")         +
                        dict_to_msg(stage.position_cached)                     +
                        (f"\nHere is the current experiment configuration:\n") 
                        # dict_to_msg(cfg['nf'])                                 +
                        # (f"\nHere are the file output info:\n")                +
                        # dict_to_msg(cfg['output'])
                      )
        return _status_msg
        """
        # TODO:
        #   verbose string representation of the experiment and beamline
        #   status as a dictionary -> yaml 

    @staticmethod
    def get_nfbeam(mode):
        """return NFbeam based on given mode"""
        if mode.lower() in ['dryrun', 'production']:
            beam = Beam()
        elif mode.lower() == 'debug':
            # NOTE:
            #   This is a place holder for maybe additional control of the beam
            #   simulated tomobeam from the virtual beamline
            #   dumped all the simulated beam control to m16
            beam = SimBeam()
        else:
            raise ValueError(f"Invalide mode -> {mode}")
        return beam    

    @staticmethod
    def get_nfstage(mode):
        """return nfstage based on given mode"""
        if mode.lower() in ['dryrun', 'production']:
            nfstage = StageAero(name='nfstage')
        elif mode.lower() == 'debug':
            nfstage = SimStageAero(name='nfstage') 
        else:
            raise ValueError(f"Invalide mode -> {mode}")
        return nfstage

    @staticmethod
    def get_flycontrol(mode):
        if mode.lower() == 'debug':
            # TODO: need better simulated motors
            from ophyd import sim
            psofly = sim.flyer1
        elif mode.lower() in ['dryrun', 'production']:
            psofly = EnsemblePSOFlyDevice("PV_FLY", name="psofly")
        else:
            raise ValueError(f"Invalide mode, {mode}")
        return psofly

    @staticmethod
    def get_detector(mode):
        # TODO: implement real PVs
        if mode.lower() == 'debug':
            det = SimDetector("6iddSIMDET1:", name='det')

            epics.caput("6iddSIMDET1:cam1:FrameType.ZRST", "/exchange/data_white_pre")
            epics.caput("6iddSIMDET1:cam1:FrameType.ONST", "/exchange/data")
            epics.caput("6iddSIMDET1:cam1:FrameType.TWST", "/exchange/data_white_post")
            epics.caput("6iddSIMDET1:cam1:FrameType.THST", "/exchange/data_dark")
            # ophyd need this configuration
            epics.caput("6iddSIMDET1:cam1:FrameType_RBV.ZRST", "/exchange/data_white_pre")
            epics.caput("6iddSIMDET1:cam1:FrameType_RBV.ONST", "/exchange/data")
            epics.caput("6iddSIMDET1:cam1:FrameType_RBV.TWST", "/exchange/data_white_post")
            epics.caput("6iddSIMDET1:cam1:FrameType_RBV.THST", "/exchange/data_dark")
            # set the layout file for cam
            # TODO:  need to udpate with acutal config files for 6-ID-D
            _current_fp = str(pathlib.Path(__file__).parent.absolute())
            _attrib_fp = os.path.join(_current_fp, 'config/PG2_attributes.xml')
            _layout_fp = os.path.join(_current_fp, 'config/tomo6bma_layout.xml')
            det.cam1.nd_attributes_file.put(_attrib_fp)
            det.hdf1.xml_file_name.put(_layout_fp)
            # turn off the problematic auto setting in cam
            det.cam1.auto_exposure_auto_mode.put(0)  
            det.cam1.sharpness_auto_mode.put(0)
            det.cam1.gain_auto_mode.put(0)
            det.cam1.frame_rate_auto_mode.put(0)
        elif mode.lower() in ['dryrun', 'production']:
            det = PointGreyDetector("PV_DET", name='det')
            # check the following page for important information
            # https://github.com/BCDA-APS/use_bluesky/blob/master/notebooks/sandbox/images_darks_flats.ipynb
            #
            epics.caput("PV_DET:cam1:FrameType.ZRST", "/exchange/data_white_pre")
            epics.caput("PV_DET:cam1:FrameType.ONST", "/exchange/data")
            epics.caput("PV_DET:cam1:FrameType.TWST", "/exchange/data_white_post")
            epics.caput("PV_DET:cam1:FrameType.THST", "/exchange/data_dark")
            # ophyd need this configuration
            epics.caput("PV_DET:cam1:FrameType_RBV.ZRST", "/exchange/data_white_pre")
            epics.caput("PV_DET:cam1:FrameType_RBV.ONST", "/exchange/data")
            epics.caput("PV_DET:cam1:FrameType_RBV.TWST", "/exchange/data_white_post")
            epics.caput("PV_DET:cam1:FrameType_RBV.THST", "/exchange/data_dark")
            # set the layout file for cam
            # TODO:  need to udpate with acutal config files for 6-ID-D
            _current_fp = str(pathlib.Path(__file__).parent.absolute())
            _attrib_fp = os.path.join(_current_fp, 'config/PG2_attributes.xml')
            _layout_fp = os.path.join(_current_fp, 'config/tomo6bma_layout.xml')
            det.cam1.nd_attributes_file.put(_attrib_fp)
            det.hdf1.xml_file_name.put(_layout_fp)
            # turn off the problematic auto setting in cam
            det.cam1.auto_exposure_auto_mode.put(0)  
            det.cam1.sharpness_auto_mode.put(0)
            det.cam1.gain_auto_mode.put(0)
            det.cam1.frame_rate_auto_mode.put(0)
        else:
            raise ValueError(f"Invalide mode, {mode}")
        return det

    ############################
    ## Near Field Calibration ##
    ############################
    #   NOT to be used in scan plans
    def calibration(self):
        """Image calibration for the two NF z positions"""
        det     = self.nf_det
        # add the z motor?
        # add the beamstp motor?
        pass

    # ----- pre-defined scan plans starts from here
    @bpp.run_decorator()
    def fly_scan(self, cfg_nf):
        """
        Collect projections with fly motion
        """
        det     = self.nf_det
        psofly  = self.fly_control
        
        # TODO:
        #   Need to set up FS control for the scan
        #   During fly scan, the FS is always open

        # TODO:
        #   The fields need to be updated for 6-ID-D
        yield from bps.mv(det.hdf1.nd_array_port, 'PG1')
        yield from bps.mv(det.tiff1.nd_array_port, 'PG1')
    
        # we are assuming that the global psofly is available
        yield from bps.mv(
            psofly.start,           cfg_nf['omega_start'],
            psofly.end,             cfg_nf['omega_end'],
            psofly.scan_delta,      abs(cfg_nf['omega_step']),
            psofly.slew_speed,      cfg_nf['slew_speed'],
        )
        # taxi
        yield from bps.mv(psofly.taxi, "Taxi")
        yield from bps.mv(
            det.cam1.num_images, cfg_nf['n_projections'],
            det.cam1.trigger_mode, "Overlapped",
        )
        # start the fly scan
        yield from bps.trigger(det, group='fly')
        yield from bps.abs_set(psofly.fly, "Fly", group='fly')
        yield from bps.wait(group='fly')

    def nf_scan(self, cfg):
        """
        NearField scan plan based on given configuration
        """
        # unpack devices
        det                 = self.nf_det
        stage               = self.nf_stage
        shutter             = self.shutter
        shutter_suspender   = self.suspend_shutter
        beam                = self.nf_beam
        
        # load experiment configurations
        cfg = load_config(cfg) if type(cfg) != dict else cfg
        
        # TODO:
        # the following needs to be updated for 6-ID-D

        # update the cached motor position in the dict in case exp goes wrong
        _cached_position = self.nf_stage.cache_position()
    
        #########################
        ## step 0: preparation ##
        #########################
        acquire_time   = cfg['nf']['acquire_time']
        angs = np.arange(
            cfg['nf']['omega_start'], 
            cfg['nf']['omega_end']+cfg['nf']['omega_step']/2,
            cfg['nf']['omega_step'],
        )
        n_projections = len(angs)
        cfg['nf']['n_projections'] = n_projections
        cfg['nf']['total_images']  = n_projections
        fp = cfg['output']['filepath']
        fn = cfg['output']['fileprefix']

        # consider adding an extra step to:
        #   Perform energy calibration, set intended attenuation
        #   set the lenses, change the intended slit size
        #   prime the control of FS
        #############################################
        ## step 0.1: check and set beam parameters ##
        #############################################
        # set slit sizes
        # These are the 1-ID-E controls
        #   epics_put("1ide1:Kohzu_E_upHsize.VAL", ($1), 10) ##
        #   epics_put("1ide1:Kohzu_E_dnHsize.VAL", (($1)+0.1), 10) ##
        #   epics_put("1ide1:Kohzu_E_upVsize.VAL", ($2), 10) ## VERT SIZE
        #   epics_put("1ide1:Kohzu_E_dnVsize.VAL", ($2)+0.1, 10) ##
        # _beam_h_size    =   cfg['nf']['beamsize_h']
        # _beam_v_size    =   cfg['nf']['beamsize_v']
        # yield from bps.mv(beam.s1.h_size, _beam_h_size          )
        # yield from bps.mv(beam.s1.v_size, _beam_v_size          )
        # yield from bps.mv(beam.s2.h_size, _beam_h_size + 0.1    )       # add 0.1 following 1ID convention
        # yield from bps.mv(beam.s2.v_size, _beam_v_size + 0.1    )       # to safe guard the beam?

        # set attenuation
        # _attenuation = cfg['nf']['attenuation']
        # yield from bps.mv(beam.att.att_level, _attenuation)

        # check energy
        # need to be clear what we want to do here
        # _energy_foil = cfg['nf']['energyfoil']
        # yield from bps.mv(beam.foil, _energy_foil)      # need to complete this part in beamline.py

        # TODO:
        #   Instead of setting the beam optics, just check the current setup
        #   and print it out for user infomation.
        # current beam size
        cfg['nf']['beamsize_h']     = beam.s1.h_size
        cfg['nf']['beamsize_v']     = beam.s1.v_size
        # current lenses (proposed...)
        cfg['nf']['focus_beam']     = beam.l1.l1y == 10  # to see if focusing is used
        # current attenuation
        # TODO: commented for Sim testing
        # cfg['nf']['attenuation']    = beam.att.att_level
        # check energy? may not be necessary.

        # TODO:
        #   set up FS controls
        #   decide what to do with the focus lenses

        #######################################
        ## calculate slew speed for fly scan ##
        #######################################
        # https://github.com/decarlof/tomo2bm/blob/master/flir/libs/aps2bm_lib.py
        # TODO: considering blue pixels, use 2BM code as ref
        scan_time = (acquire_time+cfg['nf']['readout_time'])*n_projections
        slew_speed = (angs.max() - angs.min())/scan_time
        cfg['nf']['slew_speed'] = slew_speed
        
        # need to make sure that the sample out position is the same for both front and back
        x0, z0 = stage.kx.position, stage.kz.position
        dfx, dfz = cfg['nf']['sample_out_position']['kx'], cfg['nf']['sample_out_position']['kz']
        rotang = np.radians(cfg['nf']['omega_end']-cfg['nf']['omega_start'])
        rotm = np.array([[ np.cos(rotang), np.sin(rotang)],
                            [-np.sin(rotang), np.cos(rotang)]])
        dbxz = np.dot(rotm, np.array([dfx, dfz]))
        dbx = dbxz[0] if abs(dbxz[0]) > 1e-8 else 0.0
        dbz = dbxz[1] if abs(dbxz[1]) > 1e-8 else 0.0
        # now put the value to dict
        cfg['nf']['initial_kx']       = x0
        cfg['nf']['initial_kz']       = z0
        cfg['nf']['fronte_white_kx']  = x0 + dfx
        cfg['nf']['fronte_white_kz']  = z0 + dfz
        cfg['nf']['back_white_kx']    = x0 + dbx
        cfg['nf']['back_white_kz']    = z0 + dbz
        
        ## Ideally, we set up the FS control once, then the FS will be controlled with
        ## intended signals
    
        #########################################
        ##  Function for NF Single Layer Scan  ##
        #########################################

        @bpp.stage_decorator([det])         
        @bpp.run_decorator()
        def scan_singlelayer(self, cfg_nf, _layer_number):
            # TODO:
            #   Somewhere we need to check the light status, or, add a suspender?
            # config output
            # currently set up to output 1 HDF5 file for each NF layer, including 2 det positions
            for me in [det.tiff1, det.hdf1]:
                yield from bps.mv(me.file_path, fp)
                yield from bps.mv(me.file_name, '{}_layer{:06d}'.format(fn, _layer_number))
                yield from bps.mv(me.file_write_mode, 2)
                yield from bps.mv(me.num_capture, cfg['nf']['total_images']*2)       # *2 for two det positions
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

            #  TODO:
            #   Add FS control here to toggle the FS or Main Shutter?

            # collect projections in the current layer in the FIRST det z position
            yield from bps.mv(det.cam1.frame_type, 1)  # for HDF5 dxchange data structure
            yield from bps.mv(det.cam1.position, cfg_nf['detector_z_position']['nf_z1']) # need actual motor
            yield from self.fly_scan(cfg['nf'])

            # collect projections in the current layer in the SECOND det z position
            yield from bps.mv(det.cam1.position, cfg_nf['detector_z_position']['nf_z2']) # need actual motor
            yield from self.fly_scan(cfg['nf'])
            
            #  TODO:
            #   Add FS control here to close the FS or Main Shutter?

        ############################
        ## Near Field Volume Scan ##
        ############################
        n_layers   = cfg['nf']['volume']['n_layers']
        ky_start   = cfg['nf']['volume']['ky_start']
        ky_step    = cfg['nf']['volume']['ky_step']
        if ky_step == 0:
            # To repeat the current layer for n_layer times
            # !!! The layer/file number will still increase for this same layer
            _scan_positions = np.arange(1, n_layers+1, 1)
            for _layer_number_count in _scan_positions:
                yield from bps.mv(stage.ky, ky_start)
                yield from scan_singlelayer(self, cfg['ff'], _layer_number_count)     ### NOT sure if this works!!!
        # For regular scans
        elif ky_step != 0:
            _layer_number_count  = 1
            _scan_positions = np.arange(ky_start, ky_start+(n_layers-0.5)*ky_step, ky_step)
            for _current_scan_ky in _scan_positions:
                yield from bps.mv(stage.ky, _current_scan_ky)
                yield from scan_singlelayer(self, cfg['ff'], _layer_number_count)     ### NOT sure if this works!!!
                _layer_number_count += 1

    #   summarize_plan with config yml file
    def dryrun(self, scan_config):
        """use summarize_plan for quick analysis"""
        return summarize_plan(self.nf_scan(scan_config))


class FarField(Experiment):
    """FF-HEDM control for 6-ID-D"""
    
    def __init__(self, mode='debug'):
        Experiment.__init__(self, mode)
        self._mode = mode
        # instantiate device
        self.ff_stage       = FarField.get_ffstage(self._mode)
        self.fly_control    = FarField.get_flycontrol(self._mode)
        self.ff_det         = FarField.get_detector(self._mode)
        self.ff_beam        = FarField.get_ffbeam(self._mode)
        # TODO:
        # we need to do some initialization with Beam based on 
        # a cached/lookup table
        # 
    
    def check(self, cfg):
        """Return user input before run"""
        print(f"FarField configuration:\n{dict_to_msg(cfg['ff'])}")
        print(f"Output:\n{dict_to_msg(cfg['output'])}")

    def __repr__(self):
        """Return summary of the current experiment status"""
        """
        beam  = self.ff_beam
        stage = self.ff_stage
        # get the current beamline optics
        # TODO: need to figure out how to get the beam energy
        _beamline_status = (
                           f"Beam Size is:   {beam.s1.h_size}x{beam.s1.v_size} (HxV) \n"
                           f"Attenuation is: {beam.att_level}                        \n"
                           f"Beam Energy is: {beam.energy}                           \n"   
                           f"Focus Lenses Positions: l1y @ {beam.l1.l1y}             \n"    
                           f"                        l2y @ {beam.l2.l2y}             \n"    
                           f"                        l3y @ {beam.l3.l3y}             \n"    
                           f"                        l4y @ {beam.l4.l4y}             \n"         
                           )

        _status_msg = (
                        (f"Here is the current beamline status:\n")            +
                        _beamline_status                                       +
                        (f"\nHere are the current motor positions:\n")         +
                        dict_to_msg(stage.position_cached)                     +
                        (f"\nHere is the current experiment configuration:\n") 
                        # dict_to_msg(cfg['ff'])                                 +
                        # (f"\nHere are the file output info:\n")                +
                        # dict_to_msg(cfg['output'])
                      )
        return _status_msg
        # TODO:
        #   verbose string representation of the experiment and beamline
        #   status as a dictionary -> yaml 
        """

    @staticmethod
    def get_ffbeam(mode):
        """return FFbeam based on given mode"""
        if mode.lower() in ['dryrun', 'production']:
            beam = Beam()
        elif mode.lower() == 'debug':
             # NOTE:
            #   This is a place holder for maybe additional control of the beam
            #   simulated tomobeam from the virtual beamline
            #   dumped all the simulated beam control to m16
            beam = SimBeam()
        else:
            raise ValueError(f"Invalide mode -> {mode}")
        return beam

    @staticmethod
    def get_ffstage(mode):
        """return nfstage based on given mode"""
        if mode.lower() in ['dryrun', 'production']:
            ffstage = StageAero(name='ffstage')
        elif mode.lower() == 'debug':
            ffstage = SimStageAero(name='ffstage')
        else:
            raise ValueError(f"Invalide mode -> {mode}")
        return ffstage

    @staticmethod
    def get_flycontrol(mode):
        if mode.lower() == 'debug':
            # TODO: need better simulated motors
            from ophyd import sim
            psofly = sim.flyer1
        elif mode.lower() in ['dryrun', 'production']:
            psofly = EnsemblePSOFlyDevice("PV_FLY", name="psofly")
        else:
            raise ValueError(f"Invalide mode, {mode}")
        return psofly

    @staticmethod
    def get_detector(mode):
        # TODO: implement real PVs
        if mode.lower() == 'debug':
            det = SimDetector("6iddSIMDET1:", name='det')

            epics.caput("6iddSIMDET1:cam1:FrameType.ZRST", "/exchange/data_white_pre")
            epics.caput("6iddSIMDET1:cam1:FrameType.ONST", "/exchange/data")
            epics.caput("6iddSIMDET1:cam1:FrameType.TWST", "/exchange/data_white_post")
            epics.caput("6iddSIMDET1:cam1:FrameType.THST", "/exchange/data_dark")
            # ophyd need this configuration
            epics.caput("6iddSIMDET1:cam1:FrameType_RBV.ZRST", "/exchange/data_white_pre")
            epics.caput("6iddSIMDET1:cam1:FrameType_RBV.ONST", "/exchange/data")
            epics.caput("6iddSIMDET1:cam1:FrameType_RBV.TWST", "/exchange/data_white_post")
            epics.caput("6iddSIMDET1:cam1:FrameType_RBV.THST", "/exchange/data_dark")
            # set the layout file for cam
            # TODO:  need to udpate with acutal config files for 6-ID-D
            _current_fp = str(pathlib.Path(__file__).parent.absolute())
            _attrib_fp = os.path.join(_current_fp, 'config/PG2_attributes.xml')
            _layout_fp = os.path.join(_current_fp, 'config/tomo6bma_layout.xml')
            det.cam1.nd_attributes_file.put(_attrib_fp)
            det.hdf1.xml_file_name.put(_layout_fp)
            # turn off the problematic auto setting in cam1
            det.cam1.auto_exposure_auto_mode.put(0)  
            det.cam1.sharpness_auto_mode.put(0)
            det.cam1.gain_auto_mode.put(0)
            det.cam1.frame_rate_auto_mode.put(0)
        elif mode.lower() in ['dryrun', 'production']:
            ### TODO:
            ###     Need to get have the Dexela configured in Devices.py
            det = DexelaDetector("PV_DET", name='det')
            """
            # check the following page for important information
            # https://github.com/BCDA-APS/use_bluesky/blob/master/notebooks/sandbox/images_darks_flats.ipynb
            #
            epics.caput("PV_DET:cam1:FrameType.ZRST", "/exchange/data_white_pre")
            epics.caput("PV_DET:cam1:FrameType.ONST", "/exchange/data")
            epics.caput("PV_DET:cam1:FrameType.TWST", "/exchange/data_white_post")
            epics.caput("PV_DET:cam1:FrameType.THST", "/exchange/data_dark")
            # ophyd need this configuration
            epics.caput("PV_DET:cam1:FrameType_RBV.ZRST", "/exchange/data_white_pre")
            epics.caput("PV_DET:cam1:FrameType_RBV.ONST", "/exchange/data")
            epics.caput("PV_DET:cam1:FrameType_RBV.TWST", "/exchange/data_white_post")
            epics.caput("PV_DET:cam1:FrameType_RBV.THST", "/exchange/data_dark")
            # set the layout file for cam
            # TODO:  need to udpate with acutal config files for 6-ID-D
            _current_fp = str(pathlib.Path(__file__).parent.absolute())
            _attrib_fp = os.path.join(_current_fp, 'config/PG2_attributes.xml')
            _layout_fp = os.path.join(_current_fp, 'config/tomo6bma_layout.xml')
            det.cam1.nd_attributes_file.put(_attrib_fp)
            det.hdf1.xml_file_name.put(_layout_fp)
            # turn off the problematic auto setting in cam1
            det.cam1.auto_exposure_auto_mode.put(0)  
            det.cam1.sharpness_auto_mode.put(0)
            det.cam1.gain_auto_mode.put(0)
            det.cam1.frame_rate_auto_mode.put(0)
            """
        else:
            raise ValueError(f"Invalide mode, {mode}")
        return det

    ###########################
    ## Far Field Calibration ##
    ###########################
    #   NOT to be used in scan plans
    def calibration(self):
        """Far field calibration for detectors"""
        det     = self.ff_det
        # TODO:
        #   add the z motor?
        #   not sure what we need here
        
        pass

    # ----- pre-defined scan plans starts from here
    @bpp.run_decorator()
    def collect_dark_field(self, cfg_ff):
        """
        Collect dark field images by close the shutter
        """
        # TODO:
        #   Need to toggle Fast shutter, or main??
        det = self.ff_det
    
        yield from bps.mv(det.hdf1.nd_array_port, 'PROC1')
        yield from bps.mv(det.tiff1.nd_array_port, 'PROC1') 
        yield from bps.mv(det.proc1.enable, 1)
        yield from bps.mv(det.proc1.reset_filter, 1)
        yield from bps.mv(det.proc1.num_filter, cfg_ff['n_frames'])
        yield from bps.mv(det.cam1.trigger_mode, "Internal")
        yield from bps.mv(det.cam1.image_mode, "Multiple")
        yield from bps.mv(det.cam1.num_images, cfg_ff['n_frames']*cfg_ff['n_dark'])
        yield from bps.trigger_and_read([det])

    @bpp.run_decorator()
    def step_scan(self, cfg_ff):
        """
        Collect projections with step motion
        """
        # unpack devices
        det = self.ff_det
        ffstage = self.ff_stage
        
        # TODO:
        # the fields need to be updated for 6-ID-D
        yield from bps.mv(det.hdf1.nd_array_port, 'PROC1')
        yield from bps.mv(det.tiff1.nd_array_port, 'PROC1') 
        yield from bps.mv(det.proc1.enable, 1)
        yield from bps.mv(det.proc1.reset_filter, 1)
        yield from bps.mv(det.proc1.num_filter, cfg_ff['n_frames'])
   
        angs = np.arange(
            cfg_ff['omega_start'], 
            cfg_ff['omega_end']+cfg_ff['omega_step']/2,
            cfg_ff['omega_step'],
        )
        for ang in angs:
            yield from bps.checkpoint()
            yield from bps.mv(ffstage.rot, ang)
            yield from bps.trigger_and_read([det])   ### Why is this [det] instead of det?  /JasonZ

    @bpp.run_decorator()
    def fly_scan(self, cfg_ff):
        """
        Collect projections with fly motion
        """
        det     = self.ff_det
        psofly  = self.fly_control
        
        # TODO:
        #   Need to set up FS control for the scan
        #   During fly scan, the FS is always open
        #   For step scan, FS is triggered along with the detector (not always)

        # TODO:
        #   The fields need to be updated for 6-ID-D FF-HEDM
        yield from bps.mv(det.hdf1.nd_array_port, 'PG1')
        yield from bps.mv(det.tiff1.nd_array_port, 'PG1')
    
        # we are assuming that the global psofly is available
        yield from bps.mv(
            psofly.start,           cfg_ff['omega_start'],
            psofly.end,             cfg_ff['omega_end'],
            psofly.scan_delta,      abs(cfg_ff['omega_step']),
            psofly.slew_speed,      cfg_ff['slew_speed'],
        )
        # taxi
        yield from bps.mv(psofly.taxi, "Taxi")
        yield from bps.mv(
            det.cam1.num_images, cfg_ff['n_projections'],
            det.cam1.trigger_mode, "Overlapped",
        )
        # start the fly scan
        yield from bps.trigger(det, group='fly')
        yield from bps.abs_set(psofly.fly, "Fly", group='fly')
        yield from bps.wait(group='fly')

    def ff_scan(self, cfg):
        """
        FarField scan plan based on given configuration
        """
        # unpack devices
        det                 = self.ff_det
        stage               = self.ff_stage
        shutter             = self.shutter
        shutter_suspender   = self.suspend_shutter
        beam                = self.ff_beam
        
        # load experiment configurations
        cfg = load_config(cfg) if type(cfg) != dict else cfg
        
        # TODO:
        # the following needs to be updated for 6-ID-D

        # update the cached motor position in the dict in case exp goes wrong
        _cached_position = self.ff_stage.cache_position()
    
        #########################
        ## step 0: preparation ##
        #########################
        acquire_time   = cfg['ff']['acquire_time']
        n_dark         = cfg['ff']['n_dark']
        angs = np.arange(
            cfg['ff']['omega_start'], 
            cfg['ff']['omega_end']+cfg['nf']['omega_step']/2,
            cfg['ff']['omega_step'],
        )
        n_projections = len(angs)
        cfg['ff']['n_projections'] = n_projections
        cfg['ff']['total_images']  = n_dark + n_projections + n_dark
        fp = cfg['output']['filepath']
        fn = cfg['output']['fileprefix']

        # consider adding an extra step to:
        #   Perform energy calibration, set intended attenuation
        #   set the lenses, change the intended slit size
        #   prime the control of FS
        #############################################
        ## step 0.1: check and set beam parameters ##
        #############################################
        # set slit sizes
        # These are the 1-ID-E controls
        #   epics_put("1ide1:Kohzu_E_upHsize.VAL", ($1), 10) ##
        #   epics_put("1ide1:Kohzu_E_dnHsize.VAL", (($1)+0.1), 10) ##
        #   epics_put("1ide1:Kohzu_E_upVsize.VAL", ($2), 10) ## VERT SIZE
        # #   epics_put("1ide1:Kohzu_E_dnVsize.VAL", ($2)+0.1, 10) ##
        # _beam_h_size    =   cfg['ff']['beamsize_h']
        # _beam_v_size    =   cfg['ff']['beamsize_v']
        # yield from bps.mv(beam.s1.h_size, _beam_h_size          )
        # yield from bps.mv(beam.s1.v_size, _beam_v_size          )
        # yield from bps.mv(beam.s2.h_size, _beam_h_size + 0.1    )       # add 0.1 following 1ID convention
        # yield from bps.mv(beam.s2.v_size, _beam_v_size + 0.1    )       # to safe guard the beam?

        # # set attenuation
        # _attenuation = cfg['ff']['attenuation']
        # yield from bps.mv(beam.att.att_level, _attenuation)

        # # check energy
        # # need to be clear what we want to do here
        # _energy_foil = cfg['nf']['energyfoil']
        # yield from bps.mv(beam.foil, _energy_foil)      # need to complete this part in beamline.py

        # TODO:
        #   Instead of setting the beam optics, just check the current setup
        #   and print it out for user infomation.
        # current beam size
        cfg['ff']['beamsize_h']     = beam.s1.h_size
        cfg['ff']['beamsize_v']     = beam.s1.v_size
        # current lenses (proposed...)
        cfg['ff']['focus_beam']     = beam.l1.l1y == 10  # to see if focusing is used
        # current attenuation
        # TODO: att_level commented out for Sim test
        # cfg['ff']['attenuation']    = beam.att.att_level
        # check energy? may not be necessary.

        
        # TODO:
        #   set up FS controls
        #   decide what to do with the focus lenses

        #######################################
        ## calculate slew speed for fly scan ##
        #######################################

        # https://github.com/decarlof/tomo2bm/blob/master/flir/libs/aps2bm_lib.py
        # TODO: considering blue pixels, use 2BM code as ref
        if cfg['ff']['type'].lower() == 'fly':
            scan_time = (acquire_time+cfg['ff']['readout_time'])*n_projections
            slew_speed = (angs.max() - angs.min())/scan_time
            cfg['ff']['slew_speed'] = slew_speed
        

        # TODO:
        #   If this is not used during scans, consider moving this to corresponding part
        
        # need to make sure that the sample out position is the same for both front and back
        x0, z0 = stage.kx.position, stage.kz.position
        dfx, dfz = cfg['ff']['sample_out_position']['kx'], cfg['nf']['sample_out_position']['kz']
        rotang = np.radians(cfg['ff']['omega_end']-cfg['nf']['omega_start'])
        rotm = np.array([[ np.cos(rotang), np.sin(rotang)],
                            [-np.sin(rotang), np.cos(rotang)]])
        dbxz = np.dot(rotm, np.array([dfx, dfz]))
        dbx = dbxz[0] if abs(dbxz[0]) > 1e-8 else 0.0
        dbz = dbxz[1] if abs(dbxz[1]) > 1e-8 else 0.0
        # now put the value to dict
        cfg['ff']['initial_kx']       = x0
        cfg['ff']['initial_kz']       = z0
        cfg['ff']['fronte_white_kx']  = x0 + dfx
        cfg['ff']['fronte_white_kz']  = z0 + dfz
        cfg['ff']['back_white_kx']    = x0 + dbx
        cfg['ff']['back_white_kz']    = z0 + dbz
        
        ## Ideally, we set up the FS control once, then the FS will be controlled with
        ## intended signals

        #########################################
        ##  Function for FF Single Layer Scan  ##
        #########################################

        @bpp.stage_decorator([det])         
        @bpp.run_decorator()
        def scan_singlelayer(self, cfg_ff, _layer_number):
            # TODO:
            #   Somewhere we need to check the light status, or, add a suspender?
            # config output
            for me in [det.tiff1, det.hdf1]:
                yield from bps.mv(me.file_path, fp)
                yield from bps.mv(me.file_name, '{}_layer{:06d}'.format(fn, _layer_number))
                yield from bps.mv(me.file_write_mode, 2)
                yield from bps.mv(me.num_capture, cfg['ff']['total_images'])     
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

            #  TODO:
            #   Add FS control here to toggle the FS or Main Shutter?

            # collect front dark field
            yield from bps.mv(det.cam1.frame_type, 3)  # for HDF5 dxchange data structure
            yield from bps.remove_suspender(shutter_suspender)
            yield from bps.mv(shutter, "close")         # let's discuss which shutter to use here
            yield from self.collect_dark_field(cfg['ff'])

            ### NOTE: the main shutter may be closed after dark field!!!

            # collect projections in the current layer in the det z position
            # Let's discussed if we want det z control during scans
            yield from bps.mv(det.cam1.frame_type, 1)  # for HDF5 dxchange data structure
            if cfg['ff']['type'].lower() == 'step':
                yield from self.step_scan(cfg['ff'])
            elif cfg['ff']['type'].lower() == 'fly':
                # yield from bps.mv(det.cam1.position, cfg_ff['detector_z_position']['ff_z1']) # need actual motor
                yield from self.fly_scan(cfg['nf'])
            else:
                raise ValueError(f"Unsupported scan type: {cfg['ff']['type']}")

            # collect back dark field
            yield from bps.mv(det.cam1.frame_type, 3)  # for HDF5 dxchange data structure
            yield from bps.remove_suspender(shutter_suspender)
            yield from bps.mv(shutter, "close")         # let's discuss which shutter to use here
            yield from self.collect_dark_field(cfg['ff'])
            
            #  TODO:
            #   Add FS control here to close the FS or Main Shutter?

        ###########################
        ## Far Field Volume Scan ##
        ###########################

        n_layers   = cfg['ff']['volume']['n_layers']
        ky_start   = cfg['ff']['volume']['ky_start']
        ky_step    = cfg['ff']['volume']['ky_step']
        if ky_step == 0:
            # To repeat the current layer for n_layer times
            # !!! The layer/file number will still increase for this same layer
            _scan_positions = np.arange(1, n_layers+1, 1)
            for _layer_number_count in _scan_positions:
                yield from bps.mv(stage.ky, ky_start)
                yield from scan_singlelayer(self, cfg['ff'], _layer_number_count)     ### NOT sure if this works!!!
        # For regular scans
        elif ky_step != 0:
            _layer_number_count  = 1
            _scan_positions = np.arange(ky_start, ky_start+(n_layers-0.5)*ky_step, ky_step)
            for _current_scan_ky in _scan_positions:
                yield from bps.mv(stage.ky, _current_scan_ky)
                yield from scan_singlelayer(self, cfg['ff'], _layer_number_count)     ### NOT sure if this works!!!
                _layer_number_count += 1

        # TODO:
        #   Add a final step to spit out the cfg dictionary just used
        #   This should be in a standard clean up procedure that can be added to the RE.suspender
    
    #   summarize_plan with config yml file
    def dryrun(self, scan_config):
        """use summarize_plan for quick analysis"""
        return summarize_plan(self.ff_scan(scan_config))


if __name__ == "__main__":
    pass