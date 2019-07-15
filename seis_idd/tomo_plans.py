#!/usr/bin/env python

"""
Predefined bluesky scan plans
"""

import numpy                 as np
import bluesky.plans         as bp
import bluesky.preprocessors as bpp
import bluesky.plan_stubs    as bps

from utility            import load_config

@bpp.run_decorator()
def collect_white_field(det, tomostage, cfg_tomo, atfront=True):
    """
    Collect white/flat field images by moving the sample out of the FOV
    """
    # move sample out of the way
    if atfront:
        yield from bps.mv(tomostage.samX, cfg_tomo['fronte_white_samx'])
        yield from bps.mv(tomostage.samY, cfg_tomo['fronte_white_samy'])
    else:
        yield from bps.mv(tomostage.samX, cfg_tomo['back_white_samx'])
        yield from bps.mv(tomostage.samY, cfg_tomo['back_white_samy'])

    # setup detector
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
    yield from bps.mv(tomostage.samX, cfg_tomo['initial_samx'])
    yield from bps.mv(tomostage.samY, cfg_tomo['initial_samy'])


@bpp.run_decorator()
def collect_dark_field(det, tomostage, cfg_tomo):
    """
    Collect dark field images by close the shutter
    """
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
def step_scan(det, tomostage, cfg_tomo):
    """
    Collect projects with step motion
    """
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
def fly_scan(det, tomostage, cfg_tomo):
    """
    Collect projections with fly motion
    """
    yield from bps.mv(det.hdf1.nd_array_port, 'PG1')
    yield from bps.mv(det.tiff1.nd_array_port, 'PG1')

    # we are assuming that the global psofly is available
    yield from bps.mv(
        psofly.start,           cfg_tomo['omega_start'],
        psofly.end,             cfg_tomo['omega_end'],
        psofly.scan_delta,      cfg_tomo['omega_step'],
        psofly.slew_speed,      cfg_tomo['slew_speed'],
    )
    # taxi
    yield from bps.mv(psofly.taxi, "Taxi")
    # ???
    yield from bps.mv(
        det.cam.num_images, cfg_tomo['n_projections'],
        det.cam.trigger_mode, "Overlapped",
    )
    # start the fly scan
    yield from bps.trigger(det, group='fly')
    yield from bps.abs_set(psofly.fly, "Fly", group='fly')
    yield from bps.wait(group='fly')



def tomo_scan(det, tomostage, shutter, shutter_suspender, cfg):
    """
    Tomography scan plan based on given configuration
    """
    cfg = load_config(cfg) if type(cfg) != dict else cfg

    # set universal camera parameters
    det.cam.acquire_time.put(cfg['tomo']['acquire_time'])
    det.cam.acquire_period.put(cfg['tomo']['acquire_period'])

    # calc total number of projections
    # NOTE:
    #   Since HDF plugin for AD does not support appending data,
    #   we need keep the file handle open during the entire scan.    
    n_white = cfg['tomo']['n_white']
    n_dark = cfg['tomo']['n_dark']
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
    
    # calculate slew speed for fly scan
    # https://github.com/decarlof/tomo2bm/blob/master/flir/libs/aps2bm_lib.py
    # TODO: considering blue pixels, use 2BM code as ref
    if cfg['tomo']['type'].lower() == 'fly':
        scan_time = cfg['tomo']['acquire_time']*(n_projections+cfg['tomo']['readout_time'])
        cfg['tomo']['slew_speed'] = (angs.max() - angs.min())/scan_time
    
    # directly configure output plugins
    # NOTE: support both tiff and hdf plugin
    for me in [det.tiff1, det.hdf1]:
        me.file_path.put(fp)
        me.file_name.put(fn)
        me.file_write_mode.put('Stream')
        me.num_capture.put(total_images)
        me.file_template.put(".".join([r"%s%s_%06d",cfg['output']['type'].lower()]))
        me.capture.put(1)
    if cfg['output']['type'] in ['tif', 'tiff']:
        det.tiff1.enable.put(1)
        det.hdf1.enable.put(0)
    elif cfg['output']['type'] in ['hdf', 'hdf1', 'hdf5']:
        det.tiff1.enable.put(0)
        det.hdf1.enable.put(1)
    else:
        raise ValueError(f"Unsupported output type {cfg['output']['type']}")

    # need to make sure that the sample out position is the same for both front and back
    x0, y0 = tomostage.samX.position, tomostage.samY.position
    dfx, dfy = cfg['tomo']['sample_out_position']['samx'], cfg['tomo']['sample_out_position']['samy']
    rotang = np.radians(cfg['tomo']['omega_end']-cfg['tomo']['omega_start'])
    rotm = np.array([[ np.cos(rotang), np.sin(rotang)],
                     [-np.sin(rotang), np.cos(rotang)]])
    dbxy = np.dot(rotm, np.array([dfx, dfy]))
    dbx = dbxy[0] if abs(dbxy) > 1e-8 else 0.0
    dby = dbxy[1] if abs(dbxy) > 1e-8 else 0.0
    # now put the value to dict
    cfg['tomo']['initial_samx'] = x0
    cfg['tomo']['initial_samy'] = y0
    cfg['tomo']['fronte_white_samx'] = x0 + dfx
    cfg['tomo']['fronte_white_samy'] = y0 + dfy
    cfg['tomo']['back_white_samx'] = x0 + dbx
    cfg['tomo']['back_white_samy'] = y0 + dby

    @bpp.run_decorator()
    def scan_closure():
        # open shutter for beam
        yield from bps.mv(shutter, 'open')
        yield from bps.install_suspender(shutter_suspender)

        # collect front white field
        yield from bps.mv(det.cam.frame_type, 0)  # for HDF5 dxchange data structure
        yield from collect_white_field(det, tomostage, cfg['tomo'], atfront=True)

        # collect projections
        yield from bps.mv(det.cam.frame_type, 1)  # for HDF5 dxchange data structure
        if cfg['tomo']['type'].lower() == 'step':
            yield from step_scan(det, tomostage, cfg['tomo'])
        elif cfg['tomo']['type'].lower() == 'fly':
            yield from fly_scan(det, tomostage, cfg['tomo'])
        else:
            raise ValueError(f"Unsupported scan type: {cfg['tomo']['type']}")

        # collect back white field
        yield from bps.mv(det.cam.frame_type, 2)  # for HDF5 dxchange data structure
        yield from collect_white_field(det, tomostage, cfg['tomo'], atfront=False)

        # collect back dark field
        yield from bps.mv(det.cam.frame_type, 3)  # for HDF5 dxchange data structure
        yield from bps.remove_suspender(shutter_suspender)
        yield from bps.mv(shutter, "close")
        yield from collect_dark_field(det, tomostage, cfg['tomo'])

    return (yield from scan_closure())
