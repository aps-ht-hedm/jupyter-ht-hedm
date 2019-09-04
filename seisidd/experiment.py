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

from   bluesky.callbacks.best_effort import BestEffortCallback
from   bluesky.suspenders            import SuspendFloor
from   bluesky.simulators            import summarize_plan

from  .devices.beamline              import Beam
from  .devices.beamline              import FastShutter
from  .devices.motors                import StageAero
from  .devices.motors                import EnsemblePSOFlyDevice
from  .utility                       import load_config

import bluesky.preprocessors as bpp
import bluesky.plan_stubs    as bps


class Experiment:
    """Generic expriment handler"""

    def __init__(self, mode='debug'):
        self.RE = bluesky.RunEngine({})
        self.db = databroker.Broker.named("mongodb_config")
        self.RE.subscribe(self.db.insert)
        self.RE.subscribe(BestEffortCallback())

        self._mode   = mode
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
        # 
    
    def __repr__(self):
        """Return summary of the current experiment status"""
        # TODO:
        #   verbose string representation of the experiment and beamline
        #   status as a dictionary -> yaml
        pass 

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
        """return tomobeam based on given mode"""
        if mode.lower() in ['dryrun', 'production']:
            tomobeam = Beam()
        elif mode.lower() == 'debug':
            # NOTE:
            #   This is a place holder for maybe additional control of the beam
            #   in the debug mode.  Let's discuss what should be exposed here.
            #   Or, we just use some simulated motors for the beam here as below?
            from ophyd import sim
            from ophyd import MotorBundle
            #   simulated tomobeam motor bundle.  This part need FIX!!!
            tomobeam            = MotorBundle(name='tomobeam')
            #   Upstream slit, slit1
            tomobeam.s1         = MotorBundle(name='s1')
            tomobeam.s1.h_ib    = sim.SynAxis(name='h_ib')
            tomobeam.s1.h_ob    = sim.SynAxis(name='h_ob')
            tomobeam.s1.h_size  = sim.SynAxis(name='h_size')        ### need checking!!
            tomobeam.s1.v_tp    = sim.SynAxis(name='v_tp')
            tomobeam.s1.v_bt    = sim.SynAxis(name='v_bt')
            tomobeam.s1.v_size  = sim.SynAxis(name='v_size')        ### need checking!!
            #   Downstream slit, slit2
            tomobeam.s2         = MotorBundle(name='s2')
            tomobeam.s2.h_ib    = sim.SynAxis(name='h_ib')
            tomobeam.s2.h_ob    = sim.SynAxis(name='h_ob')
            tomobeam.s2.h_size  = sim.SynAxis(name='h_size')        ### need checking!!
            tomobeam.s2.v_tp    = sim.SynAxis(name='v_tp')
            tomobeam.s2.v_bt    = sim.SynAxis(name='v_bt')
            tomobeam.s2.v_size  = sim.SynAxis(name='v_size')        ### need checking!!
            #   Focus lens 1
            tomobeam.l1         = MotorBundle(name='l1')
            tomobeam.l1.l1x     = sim.SynAxis(name='l1x')
            tomobeam.l1.l1y     = sim.SynAxis(name='l1y')
            tomobeam.l1.l1z     = sim.SynAxis(name='l1z')
            tomobeam.l1.l1rot   = sim.SynAxis(name='l1rot')
            tomobeam.l1.l1tx    = sim.SynAxis(name='l1tx')
            tomobeam.l1.l1tz    = sim.SynAxis(name='l1tz')
            #   Focus lens 2
            tomobeam.l2         = MotorBundle(name='l2')
            tomobeam.l2.l1x     = sim.SynAxis(name='l2x')
            tomobeam.l2.l1y     = sim.SynAxis(name='l2y')
            tomobeam.l2.l1z     = sim.SynAxis(name='l2z')
            tomobeam.l2.l1rot   = sim.SynAxis(name='l2rot')
            tomobeam.l2.l1tx    = sim.SynAxis(name='l2tx')
            tomobeam.l2.l1tz    = sim.SynAxis(name='l2tz')
            #   Focus lens 3
            tomobeam.l3         = MotorBundle(name='l3')
            tomobeam.l3.l1x     = sim.SynAxis(name='l3x')
            tomobeam.l3.l1y     = sim.SynAxis(name='l3y')
            tomobeam.l3.l1z     = sim.SynAxis(name='l3z')
            tomobeam.l3.l1rot   = sim.SynAxis(name='l3rot')
            tomobeam.l3.l1tx    = sim.SynAxis(name='l3tx')
            tomobeam.l3.l1tz    = sim.SynAxis(name='l3tz')
            #   Focus lens 4
            tomobeam.l4         = MotorBundle(name='l4')
            tomobeam.l4.l1x     = sim.SynAxis(name='l4x')
            tomobeam.l4.l1y     = sim.SynAxis(name='l4y')
            tomobeam.l4.l1z     = sim.SynAxis(name='l4z')
            tomobeam.l4.l1rot   = sim.SynAxis(name='l4rot')
            tomobeam.l4.l1tx    = sim.SynAxis(name='l4tx')
            tomobeam.l4.l1tz    = sim.SynAxis(name='l4tz')

            return tomobeam



    @staticmethod
    def get_tomostage(mode):
        """return tomostage based on given mode"""
        if mode.lower() in ['dryrun', 'production']:
            tomostage = StageAero(name='tomostage')
        elif mode.lower() == 'debug':
            # NOTE:
            #    Moving a synthetic motor will lead to some really strange
            #    issue.  This could be related to the API change in the
            #    synAxis.
            from ophyd import sim
            from ophyd import MotorBundle
            tomostage       = MotorBundle(name="tomostage")
            tomostage.preci = sim.SynAxis(name='preci')
            tomostage.samX  = sim.SynAxis(name='samX')
            tomostage.ksamX = sim.SynAxis(name='ksamX')
            tomostage.ksamZ = sim.SynAxis(name='ksamz')
            tomostage.samY  = sim.SynAxis(name='samY')
        else:
            raise ValueError(f"Invalide mode -> {mode}")
        return tomostage

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
        if mode.lower() == 'debug':
            # TODO: need better simulated detectors
            from ophyd import sim
            det = sim.noisy_det
        elif mode.lower() in ['dryrun', 'production']:
            det = PointGreyDetector6IDD("PV_DET", name='det')
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
            det.cam.nd_attributes_file.put(_attrib_fp)
            det.hdf1.xml_file_name.put(_layout_fp)
            # turn off the problematic auto setting in cam
            det.cam.auto_exposure_auto_mode.put(0)  
            det.cam.sharpness_auto_mode.put(0)
            det.cam.gain_auto_mode.put(0)
            det.cam.frame_rate_auto_mode.put(0)
        else:
            raise ValueError(f"Invalide mode, {mode}")
        return det

    # ----- pre-defined scan plans starts from here
    @bpp.run_decorator()
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
        _x = cfg_tomo['fronte_white_ksamX'] if atfront else cfg_tomo['back_white_ksamX']
        _z = cfg_tomo['fronte_white_ksamZ'] if atfront else cfg_tomo['back_white_ksamZ']
        yield from bps.mv(tomostage.ksamX, _x)  #update with correct motor name
        yield from bps.mv(tomostage.ksamZ, _z)
    
        # setup detector
        # TODO:
        # actual implementation need to be for 6-ID-D
        yield from bps.mv(det.hdf1.nd_array_port, 'PROC1')
        yield from bps.mv(det.tiff1.nd_array_port, 'PROC1') 
        yield from bps.mv(det.proc1.enable, 1)
        yield from bps.mv(det.proc1.reset_filter, 1)
        yield from bps.mv(det.proc1.num_filter, cfg_tomo['n_frames'])
        yield from bps.mv(det.cam.trigger_mode, "Internal")
        yield from bps.mv(det.cam.image_mode, "Multiple")
        yield from bps.mv(det.cam.num_images, cfg_tomo['n_frames']*cfg_tomo['n_white'])
        yield from bps.trigger_and_read([det])
    
        # move sample back to FOV
        # NOTE:
        # not sure is this will work or not...
        # why are we moving samX with ksamX value???  /JasonZ
        # TODO:
        #   need to update all the motor names according to StageAero
        yield from bps.mv(tomostage.samX, cfg_tomo['initial_ksamX'])
        yield from bps.mv(tomostage.samZ, cfg_tomo['initial_ksamZ'])
    
    @bpp.run_decorator()
    def collect_dark_field(self, cfg_tomo):
        """
        Collect dark field images by close the shutter
        """
        det = self.tomo_det
    
        yield from bps.mv(det.hdf1.nd_array_port, 'PROC1')
        yield from bps.mv(det.tiff1.nd_array_port, 'PROC1') 
        yield from bps.mv(det.proc1.enable, 1)
        yield from bps.mv(det.proc1.reset_filter, 1)
        yield from bps.mv(det.proc1.num_filter, cfg_tomo['n_frames'])
        yield from bps.mv(det.cam.trigger_mode, "Internal")
        yield from bps.mv(det.cam.image_mode, "Multiple")
        yield from bps.mv(det.cam.num_images, cfg_tomo['n_frames']*cfg_tomo['n_dark'])
        yield from bps.trigger_and_read([det])

    @bpp.run_decorator()
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
            yield from bps.mv(tomostage.preci, ang)
            yield from bps.trigger_and_read([det])

    @bpp.run_decorator()
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
            det.cam.num_images, cfg_tomo['n_projections'],
            det.cam.trigger_mode, "Overlapped",
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
        shutter             = self.shutter
        shutter_suspender   = self.suspend_shutter
        tomobeam            = self.tomo_beam
        
        # load experiment configurations
        cfg = load_config(cfg) if type(cfg) != dict else cfg
        
        # TODO:
        # the following needs to be updated for 6-ID-D

        # update the cached motor position in the dict in case exp goes wrong
        _cahed_position = self.tomo_stage.cache_position()
    
        # step 0: preparation
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
        total_images  = n_white + n_projections + n_white + n_dark
        fp = cfg['output']['filepath']
        fn = cfg['output']['fileprefix']

        # consider adding an extra step to:
        #   Perform energy calibration, set intended attenuation
        #   set the lenses, change the intended slit size
        #   prime the control of FS

        #############################################
        ## step 0.5: check and set beam parameters ##
        #############################################
        
        # set slit sizes
        # These are the 1-ID-E controls
        #   epics_put("1ide1:Kohzu_E_upHsize.VAL", ($1), 10) ##
        #   epics_put("1ide1:Kohzu_E_dnHsize.VAL", (($1)+0.1), 10) ##
        #   epics_put("1ide1:Kohzu_E_upVsize.VAL", ($2), 10) ## VERT SIZE
        #   epics_put("1ide1:Kohzu_E_dnVsize.VAL", ($2)+0.1, 10) ##
        _beam_h_size    =   cfg['tomo']['beamsize_h']
        _beam_v_size    =   cfg['tomo']['beamsize_v']
        yield from bps.mv(tomobeam.s1.h_size, _beam_h_size          )
        yield from bps.mv(tomobeam.s1.v_size, _beam_v_size          )
        yield from bps.mv(tomobeam.s2.h_size, _beam_h_size + 0.1    )       # add 0.1 following 1ID convention
        yield from bps.mv(tomobeam.s2.v_size, _beam_v_size + 0.1    )       # to safe guard the beam?

        # set attenuation
        _attenuation = cfg['tomo']['attenuation']
        yield from bps.mv(tomobeam.att.att_level, _attenuation)

        # check energy
        # need to be clear what we want to do here
        _energy_foil = cfg['tomo']['energyfoil']
        yield from bps.mv(tomobeam.foil, _energy_foil)      # need to complete this part in beamline.py

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
        x0, z0 = tomostage.ksamX.position, tomostage.ksamZ.position
        dfx, dfz = cfg['tomo']['sample_out_position']['samX'], cfg['tomo']['sample_out_position']['samZ']
        rotang = np.radians(cfg['tomo']['omega_end']-cfg['tomo']['omega_start'])
        rotm = np.array([[ np.cos(rotang), np.sin(rotang)],
                            [-np.sin(rotang), np.cos(rotang)]])
        dbxz = np.dot(rotm, np.array([dfx, dfz]))
        dbx = dbxz[0] if abs(dbxz[0]) > 1e-8 else 0.0
        dbz = dbxz[1] if abs(dbxz[1]) > 1e-8 else 0.0
        # now put the value to dict
        cfg['tomo']['initial_ksamX'] = x0
        cfg['tomo']['initial_ksamZ'] = z0
        cfg['tomo']['fronte_white_ksamX'] = x0 + dfx
        cfg['tomo']['fronte_white_ksamZ'] = z0 + dfz
        cfg['tomo']['back_white_ksamX'] = x0 + dbx
        cfg['tomo']['back_white_ksamZ'] = z0 + dbz
        
        
        @bpp.stage_decorator([det])
        @bpp.run_decorator()
        def scan_closure():
            # open shutter for beam
            yield from bps.mv(shutter, 'open')
            yield from bps.install_suspender(shutter_suspender)
            
            # config output
            for me in [det.tiff1, det.hdf1]:
                yield from bps.mv(me.file_path, fp)
                yield from bps.mv(me.file_name, fn)
                yield from bps.mv(me.file_write_mode, 2)
                yield from bps.mv(me.num_capture, total_images)
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
    
            # collect front white field
            yield from bps.mv(det.cam.frame_type, 0)  # for HDF5 dxchange data structure
            yield from self.collect_white_field(cfg['tomo'], atfront=True)
    
            # collect projections
            yield from bps.mv(det.cam.frame_type, 1)  # for HDF5 dxchange data structure
            if cfg['tomo']['type'].lower() == 'step':
                yield from self.step_scan(cfg['tomo'])
            elif cfg['tomo']['type'].lower() == 'fly':
                yield from self.fly_scan(cfg['tomo'])
            else:
                raise ValueError(f"Unsupported scan type: {cfg['tomo']['type']}")
    
            # collect back white field
            yield from bps.mv(det.cam.frame_type, 2)  # for HDF5 dxchange data structure
            yield from self.collect_white_field(cfg['tomo'], atfront=False)
    
            # collect back dark field
            yield from bps.mv(det.cam.frame_type, 3)  # for HDF5 dxchange data structure
            yield from bps.remove_suspender(shutter_suspender)
            yield from bps.mv(shutter, "close")
            yield from self.collect_dark_field(cfg['tomo'])
    
        return (yield from scan_closure())
    
    #   summarize_plan with config yml file
    def dryrun(self, scan_config):
        """use summarize_plan for quick analysis"""
        return summarize_plan(tomo_scan(self, scan_config))


class NearField(Experiment):
    """nf-HEDM control for 6-ID-D"""
    
    def __init__(self, mode='debug'):
        Experiment.__init__(self, mode)
        self._mode = mode
        # instantiate device
        self.nf_stage       = NearField.get_nfstage(self._mode)
        self.fly_control    = NearField.get_flycontrol(self._mode)
        self.nf_det         = NearField.get_detector(self._mode)
        self.nf_beam        = Beam()
        # TODO:
        # we need to do some initialization with Beam based on 
        # a cached/lookup table
        # 
    
    def __repr__(self):
        """Return summary of the current experiment status"""
        # TODO:
        #   verbose string representation of the experiment and beamline
        #   status as a dictionary -> yaml
        pass 
    
    
    
    
    
    
    
    
    
    pass


class FarField(Experiment):
    """ff-HEDM control for 6-ID-D"""
    pass


if __name__ == "__main__":
    pass