#!/usr/bin/env python

"""
This module provides utility functions useful for running experiment through
notebook interface.
"""

import yaml

from tabulate             import tabulate
from IPython              import get_ipython
from IPython.core.display import display, HTML

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