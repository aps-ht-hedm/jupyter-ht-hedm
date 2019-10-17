# jupyter-ht-hedm
Driving HT-HEDM experiment with Bluesky+Ophyd as backend and Jupyter as the front-end.

# Interface with virtual beamline
The folder `vbdata` is used to _interface_ with the virutal beamline:

* vbdata/data: mapped as `/data` for relavent epics devices.
* vbdata/data/db: mapped as `/data/db` for storing data base (Mongo DB).

# On VirtualBeamline testing
* 10-17-2019: 
   * Tomography passed initial tests with step scan, both tiff and hdf outputs are supported.
   * !!! File path will lead to a time out in RE with bps.mv(det.tiff1.file_path, 'XXXXX'). Bluesky may be waiting for read back from (det.tiff1.file_path_exists).
   * Test record can be found in "private"

