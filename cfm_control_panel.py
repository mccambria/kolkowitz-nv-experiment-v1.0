# -*- coding: utf-8 -*-
"""
This file contains functions to control the CFM. Just change the function call
in the main section at the bottom of this file and run the file. Shared or
frequently changed parameters are in the __main__ body and relatively static
parameters are in the function definitions.

Created on Sun Nov 25 14:00:28 2018

@author: mccambria
"""


# %% Imports

import labrad
import utils.tool_belt as tool_belt
import majorroutines.image_sample as image_sample
import majorroutines.optimize as optimize
import majorroutines.stationary_count as stationary_count
import majorroutines.resonance as resonance


# %% Minor Routines


def set_xyz(coords):
    with labrad.connect() as cxn:
        tool_belt.set_xyz(cxn, coords)


def set_xyz_zero():
    with labrad.connect() as cxn:
        tool_belt.set_xyz_zero(cxn)


# %% Major Routines


def do_image_sample(name, coords, scan_range, num_steps, apd_index):

    readout = 10 * 10**6  # In nanoseconds

    with labrad.connect() as cxn:
        # For now we only support square scans so pass scan_range twice
        image_sample.main(cxn, name, coords, scan_range, scan_range,
                          num_steps, readout, apd_index)


def do_optimize(name, coords, apd_index):

    with labrad.connect() as cxn:
        optimize.main(cxn, name, coords, apd_index,
                      set_to_opti_centers=False,
                      save_data=True, plot_data=True)


def do_stationary_count(name, coords, apd_index):

    # In nanoseconds
    run_time = 20 * 10**9
    readout = 100 * 10**6

    with labrad.connect() as cxn:
        stationary_count.main(cxn, name, coords, run_time, readout, apd_index)


def do_resonance(name, coords, apd_index):

    freq_center = 2.87
    freq_range = 0.3
    num_steps = 60
    num_runs = 5
    uwave_power = -13.0  # -13.0 with a 1.0 ND is a good starting point

    with labrad.connect() as cxn:
        resonance.main(cxn, name, coords, apd_index, freq_center, freq_range,
                       num_steps, num_runs, uwave_power)


# %% Script Code


# Functions only run when called. Since this part of the script is not in a
# function, it will run when the script is run.
# __name__ will only be __main__ if we're running the file as a program.
# The below pattern enables us to import this file as a module without
# running it as a program.
if __name__ == '__main__':

    # %% Frequenctly modified/shared parameters
    # The file has minimal documentation.
    # For more, view the function definitions in their respective file.

    name = 'ayrton12'

#    coords = [0.0, 0.0, 50.0]
    coords = [0.002, -0.010, 48.502]

    apd_index = 0

    scan_range = 0.05
    num_scan_steps = 60

    # %% Functions to run

    try:
#        do_image_sample(name, coords, scan_range, num_scan_steps, apd_index)
#        do_optimize(name, coords, apd_index)
#        do_stationary_count(name, coords, apd_index)
        do_resonance(name, coords, apd_index)
    finally:
        pass
        # Kill safe stop
#        if tool_belt.check_safe_stop_alive():
#            tool_belt.poll_safe_stop()
