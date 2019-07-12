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

# def list_predefined_vars():
#     print(f"🙊: These are the predefined vars:")
#     for key, val in keywords_vars.items():
#         print(f"\t{key}:\t{val}")
#     print()

# def list_predefined_func():
#     print(f"🙊: These are the predefined functions:")
#     for key, val in keywords_func.items():
#         print(f"\t{key}:\t{val}")
#     print()


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
keywords_func['getRunEngine'] = 'Get a bluesky RunEngine'
def getRunEngine(db=None):
    """
    Return an instance of RunEngine.  It is recommended to have only
    one RunEngine per session.
    """
    RE = RunEngine({})
    db = metadata_db if db is None else db
    RE.subscribe(db.insert)
    RE.subscribe(BestEffortCallback())
    return RE

RE = getRunEngine()
keywords_vars['RE'] = 'Default RunEngine instance'


# --- import utility functions
from utility import load_config
keywords_func['load_config'] = load_config.__doc__









