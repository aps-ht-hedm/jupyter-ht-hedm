# jupyter-ht-hedm
Driving HT-HEDM experiment with Bluesky+Ophyd as backend and Jupyter as the front-end.

# Interface with virtual beamline
The folder `vbdata` is used to _interface_ with the virutal beamline:

* vbdata/data: mapped as `/data` for relavent epics devices.
* vbdata/data/db: mapped as `/data/db` for storing data base (Mongo DB).
