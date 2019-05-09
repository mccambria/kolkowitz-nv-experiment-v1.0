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
import numpy
import utils.tool_belt as tool_belt
import majorroutines.image_sample as image_sample
import majorroutines.optimize as optimize
import majorroutines.stationary_count as stationary_count
import majorroutines.resonance as resonance
import majorroutines.rabi as rabi
import majorroutines.g2_measurement as g2_measurement
import majorroutines.t1_measurement as t1_measurement
import majorroutines.t1_measurement_single as t1_measurement_single


# %% Minor Routines


def set_xyz(coords):
    with labrad.connect() as cxn:
        tool_belt.set_xyz(cxn, coords)


def set_xyz_zero():
    with labrad.connect() as cxn:
        tool_belt.set_xyz_zero(cxn)


# %% Major Routines


def do_image_sample(name, coords, nd_filter, scan_range, num_steps, apd_index):

    readout = 10 * 10**6  # In nanoseconds

    with labrad.connect() as cxn:
        # For now we only support square scans so pass scan_range twice
        image_sample.main(cxn, coords, nd_filter, scan_range, scan_range,
                          num_steps, readout, apd_index, name=name)


def do_optimize(name, coords, nd_filter, apd_index):

    with labrad.connect() as cxn:
        optimize.main(cxn, coords, nd_filter, apd_index, name,
                      expected_counts=None, set_to_opti_centers=False,
                      save_data=True, plot_data=True, )


def do_stationary_count(name, coords, nd_filter, apd_index):

    # In nanoseconds
    run_time = 2 * 10**9
    readout = 100 * 10**6

    with labrad.connect() as cxn:
        stationary_count.main(cxn, coords, nd_filter, run_time, readout, apd_index,
                              name=name)


def do_g2_measurement(name, coords, nd_filter, apd_a_index, apd_b_index):

    run_time = 60 * 10
#    run_time = 30
    diff_window = 150 * 10**3  # 100 ns in ps
    
    with labrad.connect() as cxn:
        g2_measurement.main(cxn, coords, nd_filter, run_time, diff_window,
                            apd_a_index, apd_b_index, name=name)


def do_resonance(name, coords, nd_filter, apd_index, expected_counts):

    freq_center = 2.87
    freq_range = 0.2
#    freq_range = 0.05
    num_steps = 101
    num_runs = 6
    uwave_power = -13.0  # -13.0 with a 1.5 ND is a good starting point

    with labrad.connect() as cxn:
        resonance.main(cxn, coords, nd_filter, apd_index, expected_counts, freq_center, freq_range,
                       num_steps, num_runs, uwave_power, name=name)


def do_rabi(name, coords, nd_filter, sig_apd_index, ref_apd_index, expected_counts):

    uwave_freq = 2.881
    uwave_power = 9.0  # 9.0 is the highest reasonable value, accounting for saturation 
    # ND 1.5 is a good starting point
    uwave_time_range = [0, 200]
    num_steps = 51
    
    num_reps = 10**5
#    num_reps = 100
    num_runs = 4
#    num_runs = 8

    with labrad.connect() as cxn:
        rabi.main(cxn, coords, nd_filter, sig_apd_index, ref_apd_index, 
                  expected_counts, uwave_freq, uwave_power, uwave_time_range,
                  num_steps, num_reps, num_runs, name=name)


def do_t1_measurement(name, coords, nd_filter,
                      sig_shrt_apd_index, ref_shrt_apd_index,
                      sig_long_apd_index, ref_long_apd_index, expected_counts,
                      uwave_freq, uwave_pi_pulse, relaxation_time_range, 
                      measure_spin_0):
    
#    uwave_freq = 2.851
    uwave_power = 9
#    uwave_pi_pulse = round(110.3 / 2)
#    relaxation_time_range = [0, 100 * 10**3]
#    relaxation_time_range = [0, 1000 * 10**3]
#    relaxation_time_range = [0, 500 * 10**3]
#    relaxation_time_range = [0, 100 * 10**4]
    num_steps = 26
    num_reps = 10**4
    num_runs = 2
#    measure_spin_0 = False
    
    with labrad.connect() as cxn:
         new_coords = t1_measurement.main(cxn, coords, nd_filter,
                     sig_shrt_apd_index, ref_shrt_apd_index,
                     sig_long_apd_index, ref_long_apd_index,
                     expected_counts,
                     uwave_freq, uwave_power, uwave_pi_pulse,
                     relaxation_time_range, num_steps, num_reps, num_runs, 
                     name, measure_spin_0)
         
    return new_coords
         
def do_t1_measurement_single(name, coords, nd_filter,
                             sig_apd_index, ref_apd_index, expected_counts):
    
    uwave_freq = 2.888
    uwave_power = 9
    uwave_pi_pulse = round( 0 / 2)
    relaxation_time_range = [0, 1.5 * 10**6]
    num_steps = 101
    num_reps = 3 * 10**3
    num_runs = 10  
    measure_spin_0 = True
    
    
    with labrad.connect() as cxn:
        t1_measurement_single.main(cxn, coords, nd_filter, sig_apd_index, ref_apd_index, expected_counts,
                        uwave_freq, uwave_power, uwave_pi_pulse, relaxation_time_range,
                        num_steps, num_reps, num_runs, 
                        name, measure_spin_0)
    


# %% Script Code


# Functions only run when called. Since this part of the script is not in a
# function, it will run when the script is run.
# __name__ will only be __main__ if we're running the file as a program.
# The below pattern enables us to import this file as a module without
# running it as a program.
if __name__ == '__main__':

    # %% Frequently modified/shared parameters

    name = 'ayrton12'
    
    #  Coords from 4/30
#    nv2 = [-0.044, 0.043, 49.1] ## coordinates 5/7 18:00
#    nv2 = [-0.072, 0.039, 47.7] ## coordinates 5/8 9:00
    
    nv2 = [-0.079, 0.0331, 48.484] # 2019-04-30-NV2
#    nv_list = [nv2]
    
    # Coords from 5/6
    nv0 = [0.005, 0.017, 49.6]
    nv1 = [0.000, 0.100, 49.8]
    nv2 = [-0.021, 0.019, 49.7]
    nv3 = [-0.027, -0.041, 49.8]
    nv4 = [-0.070, -0.035, 49.9]
    nv5 = [-0.101, -0.032, 49.7]
    nv6 = [-0.074, 0.078, 49.4] ##
    nv7 = [-0.067, 0.062, 49.7]
    nv8 = [-0.062, 0.128, 49.6]
    nv9 = [-0.162, 0.082, 49.7]
    nv10 = [-0.053, 0.111, 49.7]
    nv11 = [-0.044, 0.102, 49.7]
    nv12 = [-0.183, 0.131, 49.7]
    nv13 = [-0.166, 0.135, 49.7]
    nv14 = [0.075, 0.188, 49.5]
    nv15 = [0.092, 0.190, 49.4]
#    nv_list = [nv0, nv1, nv2, nv3, nv4, nv5, nv6, nv7, nv8,
#               nv9, nv10, nv11, nv12, nv13, nv14, nv15]
#    nv_list = [nv2, nv3, nv4, nv6, nv8]
    nv_list = [nv6]

#    other_coords = [-0.05, 0.05, 49.6]
#    nv_list = [other_coords]
    
#    global_drift = numpy.array([0, 0, 0])
    
    nd_filter = 1.5

    apd_a_index = 0
    apd_b_index = 1
    apd_c_index = 2
    apd_d_index = 3

    scan_range = 0.15
    num_scan_steps = 60
     
    # Based on the current nv, what kcounts/s do we expect?
    # If not know, set to None
    expected_counts = 50
    
    # arrays for the t1 measuremnt info
    
    # 2019-04-30-NV2
    m_plus_one = [[0, 2 * 10**3], 2.852, 99.55, False]
    m_minus_one = [[0, 2 * 10**3], 2.880, 126.85, False]
    m_zero = [[0, 1.2 * 10**6], 2.87, 0, True]
    
    # 2019-05-07-NV6
    m_plus_one = [[0, 100 * 10**3], 2.850, 56.25, False]
    m_minus_one = [[0, 100 * 10**3], 2.881, 42.9, False]
    m_zero = [[0, 1.5 * 10**6], 2.87, 0, True]

    t1_array = numpy.array([m_plus_one, m_minus_one, m_zero])

    # %% Functions to run
    try:
#        for nv in nv_list:
#            coords = numpy.array(nv) + global_drift
#            coords = nv
#            set_xyz_zero()
#            do_image_sample(name, coords, nd_filter, scan_range, num_scan_steps, apd_a_index)
#            do_optimize(name, coords, nd_filter, apd_a_index)
#            do_stationary_count(name, coords, nd_filter, apd_a_index)
#            do_g2_measurement(name, coords, nd_filter, apd_a_index, apd_b_index)
#            do_resonance(name, coords, nd_filter, apd_a_index, expected_counts)
#            do_rabi(name, coords, nd_filter, apd_a_index, apd_b_index, expected_counts)
#            do_t1_measurement(name, coords, nd_filter, apd_a_index, 
#                              apd_b_index, apd_c_index, apd_d_index, expected_counts,
#                              uwave_freq, uwave_pi_pulse, relaxation_time_range, measure_spin_0)
#            do_t1_measurement_single(name, coords, nd_filter, apd_a_index, apd_b_index, expected_counts)
            
            
        
        for nv in nv_list: 
            coords = nv
            
            for t1_ind in [1]:
                
                relaxation_time_range = t1_array[t1_ind,0]
                uwave_freq = t1_array[t1_ind, 1]
                uwave_pi_pulse = t1_array[t1_ind, 2]
                measure_spin_0 = t1_array[t1_ind, 3]
            
                ret_val = do_t1_measurement(name, coords, nd_filter, apd_a_index, 
                                  apd_b_index, apd_c_index, apd_d_index, expected_counts,
                                  uwave_freq, uwave_pi_pulse, relaxation_time_range, measure_spin_0)
                
                print("new coordinates:" + str(ret_val)) 
                coords = ret_val
    finally:
        # Kill safe stop
        if tool_belt.check_safe_stop_alive():
            print("\n\nRoutine complete. Press enter to exit.")
            tool_belt.poll_safe_stop()
