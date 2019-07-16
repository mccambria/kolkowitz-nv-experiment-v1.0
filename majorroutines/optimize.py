# -*- coding: utf-8 -*-
"""
Optimize on an NV

Created on Thu Apr 11 11:19:56 2019

@author: mccambria
"""


# %% Imports


import utils.tool_belt as tool_belt
import numpy
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import time


# %% Define a few parameters

num_steps = 51


# %% Plotting functions


def create_figure():
    fig, axes_pack = plt.subplots(1, 3, figsize=(17, 8.5))
    axis_titles = ['X Axis', 'Y Axis', 'Z Axis']
    for ind in range(3):
        ax = axes_pack[ind]
        ax.set_title(axis_titles[ind])
        ax.set_xlabel('Volts (V)')
        ax.set_ylabel('Count rate (kcps)')
    fig.set_tight_layout(True)
    fig.canvas.draw()
    fig.canvas.flush_events()
    return fig
    
    
def update_figure(fig, axis_ind, voltages, count_rates, text=None):
    axes = fig.get_axes()
    ax = axes[axis_ind]
    ax.plot(voltages, count_rates)

    if text is not None:
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.05, 0.95, text, transform=ax.transAxes, fontsize=12,
                verticalalignment='top', bbox=props)

    fig.canvas.draw()
    fig.canvas.flush_events()


# %% Other functions


def read_timed_counts(cxn, num_steps, period, apd_indices):

    cxn.apd_tagger.start_tag_stream(apd_indices)
    num_read_so_far = 0
    counts = []

    timeout_duration = ((period*(10**-9)) * num_steps) + 10
    timeout_inst = time.time() + timeout_duration

    cxn.pulse_streamer.stream_start(num_steps)
    
    while num_read_so_far < num_steps:
        
        if time.time() > timeout_inst:
            break
        
        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break

        # Read the samples and update the image
        new_samples = cxn.apd_tagger.read_counter_simple()
        num_new_samples = len(new_samples)
        if num_new_samples > 0:
            counts.extend(new_samples)
            num_read_so_far += num_new_samples

    cxn.apd_tagger.stop_tag_stream()
    
    return numpy.array(counts, dtype=int)

    
def stationary_count_lite(cxn, coords, shared_params, apd_indices):
    
    readout = shared_params['continuous_readout_ns']
    
    #  Some initial calculations
    total_num_samples = 2
    x_center, y_center, z_center = coords
    readout = readout // total_num_samples

    # Load the PulseStreamer - 2000 ns delay accounts for whatever the AOM
    # delay is - the actual value doesn't matter since we're just measuring
    # the steady state
    cxn.pulse_streamer.stream_load('simple_readout.py',
                                   [2000, readout, apd_indices[0]])

    tool_belt.set_xyz(cxn, [x_center, y_center, z_center])

    # Collect the data
    cxn.apd_tagger.start_tag_stream(apd_indices)
    cxn.pulse_streamer.stream_start(total_num_samples)
    new_samples = cxn.apd_tagger.read_counter_simple(total_num_samples)
    print(new_samples)
    new_samples_avg = numpy.average(new_samples)
    cxn.apd_tagger.stop_tag_stream()
    counts_kcps = (new_samples_avg / 1000) / (readout / 10**9)
    
    return counts_kcps
    
    
def optimize_on_axis(cxn, nv_sig, axis_ind, shared_params,
                     apd_indices, fig=None):
    
    seq_file_name = 'simple_readout.py'
    
    axis_center = nv_sig[axis_ind]
    x_center, y_center, z_center = nv_sig[0: 3]
    
    scan_range_nm = 3 * shared_params['airy_radius_nm']
    readout = shared_params['continuous_readout_ns']
    
    tool_belt.init_safe_stop()
    
    # x/y
    if axis_ind in [0, 1]:
        
        scan_range = scan_range_nm / shared_params['galvo_nm_per_volt']
        
        seq_params = [shared_params['galvo_delay_ns'],
                      readout,
                      apd_indices[0]]
        ret_vals = cxn.pulse_streamer.stream_load(seq_file_name, seq_params)
        period = ret_vals[0]
        
        # Fix the piezo
        cxn.objective_piezo.write_voltage(z_center)
        
        # Get the proper scan function
        if axis_ind == 0:
            scan_func = cxn.galvo.load_x_scan
        elif axis_ind == 1:
            scan_func = cxn.galvo.load_y_scan
            
        voltages = scan_func(x_center, y_center, scan_range, num_steps, period)
        counts = read_timed_counts(cxn, num_steps, period, apd_indices)
        
    # z
    elif axis_ind == 2:
        
        scan_range = scan_range_nm / shared_params['piezo_nm_per_volt']
        half_scan_range = scan_range / 2
        low_voltage = axis_center - half_scan_range
        high_voltage = axis_center + half_scan_range
        voltages = numpy.linspace(low_voltage, high_voltage, num_steps)
    
        # Fix the galvo
        cxn.galvo.write(x_center, y_center)
    
        # Set up the stream
        seq_params = [shared_params['piezo_delay_ns'],
                      readout,
                      apd_indices[0]]
        ret_vals = cxn.pulse_streamer.stream_load(seq_file_name, seq_params)
        period = ret_vals[0]
    
        # Set up the APD
        cxn.apd_tagger.start_tag_stream(apd_indices)
    
        counts = numpy.zeros(num_steps, dtype=int)
    
        for ind in range(num_steps):
            
            if tool_belt.safe_stop():
                break
    
            cxn.objective_piezo.write_voltage(voltages[ind])
    
            # Start the timing stream
            cxn.pulse_streamer.stream_start()
    
            counts[ind] = int(cxn.apd_tagger.read_counter_simple(1)[0])
    
        cxn.apd_tagger.stop_tag_stream()
        
    count_rates = (counts / 1000) / (readout / 10**9)
    
    if fig is not None:
        update_figure(fig, axis_ind, voltages, count_rates)
        
    opti_coord = fit_gaussian(nv_sig, voltages, count_rates, axis_ind, fig)
        
    return opti_coord, voltages, counts, 
    
    
def fit_gaussian(nv_sig, voltages, count_rates, axis_ind, fig=None):
        
    fit_func = tool_belt.gaussian
    
    # The order of parameters is 
    # 0: coefficient that defines the peak height
    # 1: mean, defines the center of the Gaussian
    # 2: standard deviation, defines the width of the Gaussian
    # 3: constant y value to account for background
    expected_count_rate = nv_sig[3]
    if expected_count_rate is None:
        expected_count_rate = 50  # Guess 50
    expected_count_rate = float(expected_count_rate)
    background_count_rate = nv_sig[4]
    if background_count_rate is None:
        background_count_rate = 0  # Guess 0
    background_count_rate = float(background_count_rate)
    low_voltage = voltages[0]
    high_voltage = voltages[-1]
    scan_range = high_voltage - low_voltage
    init_fit = (expected_count_rate - background_count_rate,
                nv_sig[axis_ind],
                scan_range / 3,
                background_count_rate)
    opti_params = None
    try:
        inf = numpy.inf
        low_bounds = [0, low_voltage, 0, 0]
        high_bounds = [inf, high_voltage, inf, inf]
        opti_params, cov_arr = curve_fit(fit_func, voltages,
                                         count_rates, p0=init_fit,
                                         bounds=(low_bounds, high_bounds))
        # Consider it a failure if we railed or somehow got out of bounds
        for ind in range(len(opti_params)):
            param = opti_params[ind]
            if not (low_bounds[ind] < param < high_bounds[ind]):
                opti_params = None
    except Exception:
        pass
        
    if opti_params is None:
        print('Optimization failed for axis {}'.format(axis_ind))
        
    # Plot
    if (fig is not None) and (opti_params is not None):
        # Plot the fit
        linspace_voltages = numpy.linspace(low_voltage, high_voltage,
                                           num=1000)
        fit_count_rates = fit_func(linspace_voltages, *opti_params)
        # Add info to the axes
        # a: coefficient that defines the peak height
        # mu: mean, defines the center of the Gaussian
        # sigma: standard deviation, defines the width of the Gaussian
        # offset: constant y value to account for background
        text = 'a={:.3f}\n $\mu$={:.3f}\n ' \
            '$\sigma$={:.3f}\n offset={:.3f}'.format(*opti_params)
        update_figure(fig, axis_ind, linspace_voltages,
                      fit_count_rates, text)
    
    center = None
    if opti_params is not None:
        center = opti_params[1]
        
    return center


# %% User functions
    

def optimize_list(cxn, nv_sig_list, nd_filter, apd_indices):
    
    tool_belt.init_safe_stop()
    
    opti_nv_sig_list = []
    for ind in range(len(nv_sig_list)):
        
        print('Optimizing on NV {}...'.format(ind))
        
        if tool_belt.safe_stop():
            break
        
        nv_sig = nv_sig_list[ind]
        opti_coords = main(cxn, nv_sig, nd_filter, apd_indices,
                           set_to_opti_coords=False)
        if opti_coords is not None:
            opti_nv_sig_list.append('[{:.3f}, {:.3f}, {:.1f}, {}, {}],'.format(*opti_coords, *nv_sig[3: ]))
        else:
            opti_nv_sig_list.append('Optimization failed for NV {}.'.format(ind))
    
    for nv_sig in opti_nv_sig_list:
        print(nv_sig)
    

# %% Main


def main(cxn, nv_sig, nd_filter, apd_indices, name='untitled', 
         set_to_opti_coords=True, save_data=False, plot_data=False):
    
    tool_belt.reset_cfm(cxn)
    
    # Adjust the sig we use for drift
    drift = tool_belt.get_drift()
    passed_coords = nv_sig[0: 3]
    adjusted_coords = (numpy.array(passed_coords) + numpy.array(drift)).tolist()
    adjusted_nv_sig = [*adjusted_coords, *nv_sig[3:]]
    
    # Get the shared parameters from the registry
    shared_params = tool_belt.get_shared_parameters_dict(cxn)
    
    expected_count_rate = nv_sig[3]
    
    opti_succeeded = False
    
    # %% Try to optimize
    
    num_attempts = 2
    
    for ind in range(num_attempts):
        
        if ind > 0:
            print('Trying again...')
        
        # Create 3 plots in the figure, one for each axis
        fig = None
        if plot_data:
            fig = create_figure()
        
        # Optimize on each axis
        opti_coords = []
        voltages_by_axis = []
        counts_by_axis = []
        for axis_ind in range(3):
            ret_vals = optimize_on_axis(cxn, adjusted_nv_sig, axis_ind,
                                        shared_params, apd_indices, fig)
            opti_coords.append(ret_vals[0])
            voltages_by_axis.append(ret_vals[1])
            counts_by_axis.append(ret_vals[2])
            
        # We failed to get optimized coordinates, try again
        if None in opti_coords:
            continue
            
        # Check the count rate
        opti_count_rate = stationary_count_lite(cxn, opti_coords,
                                                shared_params, apd_indices)
        
        # Verify that our optimization found a reasonable spot by checking
        # the count rate at the center against the expected count rate
        if expected_count_rate is not None:
            
            lower_threshold = expected_count_rate * 3/4
            upper_threshold = expected_count_rate * 5/4
            
            if ind == 0:
                print('Expected count rate: {}'.format(expected_count_rate))
                
            print('Count rate at optimized coordinates: {:.1f}'.format(opti_count_rate))
            
            # If the count rate close to what we expect, we succeeded!
            if lower_threshold <= opti_count_rate <= upper_threshold:
                print('Optimization succeeded!')
                opti_succeeded = True
            else:
                print('Count rate at optimized coordinates out of bounds.')
                # If we failed by expected counts, try again with the
                # coordinates we found. If x/y are off initially, then
                # z will give a false optimized coordinate. x/y will give
                # true optimized coordinates regardless of the other initial
                # coordinates, however. So we might succeed by trying z again 
                # at the optimized x/y. 
                adjusted_nv_sig = [*opti_coords, *nv_sig[3:]]
                
        # If the threshold is not set, we succeed based only on optimize       
        else:
            print('Count rate at optimized coordinates: {:.0f}'.format(opti_count_rate))
            print('Optimization succeeded! (No expected count rate passed.)')
            opti_succeeded = True
        # Break out of the loop if optimization succeeded
        if opti_succeeded:
            break
        
    if not opti_succeeded:
        opti_coords = None
        
    # %% Calculate the drift relative to the passed coordinates
    
    if opti_succeeded:
        drift = (numpy.array(opti_coords) - numpy.array(passed_coords)).tolist()
        tool_belt.set_drift(drift)
    
    # %% Set to the optimized coordinates, or just tell the user what they are
            
    if set_to_opti_coords:
        if opti_succeeded:
            tool_belt.set_xyz(cxn, opti_coords)
        else:
            # Let the user know something went wrong
            print('Optimization failed. Resetting to coordinates ' \
                  'about which we attempted to optimize.')
            tool_belt.set_xyz(cxn, adjusted_coords)
    else:
        if opti_succeeded:
            print('Optimized coordinates: ')
            print('{:.3f}, {:.3f}, {:.1f}'.format(*opti_coords))
            print('Drift: ')
            print('{:.3f}, {:.3f}, {:.1f}'.format(*drift))
        else:
            print('Optimization failed.')
            
    print('\n')
                               
    # %% Clean up and save the data
    
    tool_belt.reset_cfm(cxn)

    # Don't bother saving the data if we're just using this to find the
    # optimized coordinates
    if save_data:

        timestamp = tool_belt.get_time_stamp()

        rawData = {'timestamp': timestamp,
                   'name': name,
                   'nv_sig': nv_sig,
                   'nv_sig-units': tool_belt.get_nv_sig_units(),
                   'nv_sig-format': tool_belt.get_nv_sig_format(),
                   'nd_filter': nd_filter,
                   'num_steps': num_steps,
                   'readout': shared_params['continuous_readout_ns'],
                   'readout-units': 'ns',
                   'opti_coords': opti_coords,
                   'opti_coords-units': 'V',
                   'x_voltages': voltages_by_axis[0].tolist(),
                   'x_voltages-units': 'V',
                   'y_voltages': voltages_by_axis[1].tolist(),
                   'y_voltages-units': 'V',
                   'z_voltages': voltages_by_axis[2].tolist(),
                   'z_voltages-units': 'V',
                   'x_counts': counts_by_axis[0].tolist(),
                   'x_counts-units': 'number',
                   'y_counts': counts_by_axis[1].tolist(),
                   'y_counts-units': 'number',
                   'z_counts': counts_by_axis[2].tolist(),
                   'z_counts-units': 'number'}

        filePath = tool_belt.get_file_path(__file__, timestamp, name)
        tool_belt.save_raw_data(rawData, filePath)
        
        if fig is not None:
            tool_belt.save_figure(fig, filePath)
            
    # %% Return the optimized coordinates we found
    
    return opti_coords
