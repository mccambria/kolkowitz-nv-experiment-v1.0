# -*- coding: utf-8 -*-
"""
T1 measurement routine.

This version of t1 allows the the readout and measurement of all nine possible
combinations of the preparation and readout of the states in relaxation 
measurements.

With the current HP signal generator we have, we write the +1 frequency to the
Tektronix signal generator, and must set the HP signal generator to the -1 freq

To specify the preparation and readout states, pass into the function a list in 
the form [preparation state, readout state]. That is passed in as 
init_read_state.

Created on Wed Apr 24 15:01:04 2019

@author: agardill
"""

# %% Imports


import utils.tool_belt as tool_belt
import majorroutines.optimize as optimize
import numpy
import os
import time
from random import shuffle
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

import json
from scipy import asarray as ar,exp

# %% Main

def main(cxn, coords, offsetxy, nd_filter, apd_indices, expected_counts,
         uwave_freq_plus, uwave_freq_minus, uwave_power, 
         uwave_pi_pulse_plus, uwave_pi_pulse_minus, relaxation_time_range,
         num_steps, num_reps, num_runs, 
         init_read_list, name='untitled'):
    
    
    # %% Defiene the times to be used in the sequence

    # Define some times (in ns)
    # time to intially polarize the nv
    polarization_time = 3 * 10**3
    # time of illumination during which signal readout occurs
    signal_time = 3 * 10**3
    # time of illumination during which reference readout occurs
    reference_time = 3 * 10**3
    # time between polarization and experiment without illumination
    pre_uwave_exp_wait_time = 1 * 10**3
    # time between the end of the experiment and signal without illumination
    post_uwave_exp_wait_time = 1 * 10**3
    # time between signal and reference without illumination
    sig_to_ref_wait_time = pre_uwave_exp_wait_time + post_uwave_exp_wait_time
    # the amount of time the AOM delays behind the gate and rf
    aom_delay_time = 750
    # the amount of time the rf delays behind the AOM and rf
    rf_delay_time = 40
    # the length of time the gate will be open to count photons
    gate_time = 450
    
    # %% Unpack the initial and read state
    
    init_state = init_read_list[0]
    read_state = init_read_list[1]  
    
    # %% Setting initialize and readout states
    
    if init_state == 0:
        uwave_pi_pulse_init = 0
    elif init_state == 1:
        uwave_pi_pulse_init = round(uwave_pi_pulse_plus)
    elif init_state == -1:
        uwave_pi_pulse_init = round(uwave_pi_pulse_minus)

    if read_state == 0:
        uwave_pi_pulse_read = 0
    elif read_state == 1:
        uwave_pi_pulse_read =round(uwave_pi_pulse_plus)
    elif read_state == -1:
        uwave_pi_pulse_read = round(uwave_pi_pulse_minus)
        
    if init_state == 0:
        uwave_freq_init = 2.87 
    if init_state == 1:
        uwave_freq_init = uwave_freq_plus
    if init_state == -1:
        uwave_freq_init = uwave_freq_minus

        
    if read_state == 0:
        uwave_freq_read = 2.87    
    if read_state == 1:
        uwave_freq_read = uwave_freq_plus
    if read_state == -1:
        uwave_freq_read = uwave_freq_minus        


    print('Initial pi pulse: {} ns'.format(uwave_pi_pulse_init))
    print('Initial frequency: {} GHz'.format(uwave_freq_init))
    print('Readout pi pulse: {} ns'.format(uwave_pi_pulse_read))
    print('Readout frequency: {} GHz'.format(uwave_freq_read))

    # %% Create the array of relaxation times
    
    # Array of times to sweep through
    # Must be ints since the pulse streamer only works with int64s
    
    min_relaxation_time = int( relaxation_time_range[0] )
    max_relaxation_time = int( relaxation_time_range[1] )
    
    taus = numpy.linspace(min_relaxation_time, max_relaxation_time,
                          num=num_steps, dtype=numpy.int32)
     
    # %% Fix the length of the sequence to account for odd amount of elements
     
    # Our sequence pairs the longest time with the shortest time, and steps 
    # toward the middle. This means we only step through half of the length
    # of the time array. 
    
    # That is a problem if the number of elements is odd. To fix this, we add 
    # one to the length of the array. When this number is halfed and turned 
    # into an integer, it will step through the middle element.
    
    if len(taus) % 2 == 0:
        half_length_taus = int( len(taus) / 2 )
    elif len(taus) % 2 == 1:
        half_length_taus = int( (len(taus) + 1) / 2 )
        
    # Then we must use this half length to calculate the list of integers to be
    # shuffled for each run
    
    tau_ind_list = list(range(0, half_length_taus))
        
    # %% Create data structure to save the counts
    
    # We create an array of NaNs that we'll fill
    # incrementally for the signal and reference counts. 
    # NaNs are ignored by matplotlib, which is why they're useful for us here.
    # We define 2D arrays, with the horizontal dimension for the frequency and
    # the veritical dimension for the index of the run.
    
    sig_counts = numpy.empty([num_runs, num_steps], dtype=numpy.uint32)
    sig_counts[:] = numpy.nan
    ref_counts = numpy.copy(sig_counts)
    
    # %% Make some lists and variables to save at the end
    
    passed_coords = coords
    
    opti_coords_list = []
    optimization_success_list = []
    
    # %% Analyze the sequence
    
    # pulls the file of the sequence from serves/timing/sequencelibrary
    file_name = os.path.basename(__file__)
    
    sequence_args = [min_relaxation_time, polarization_time, signal_time, reference_time, 
                    sig_to_ref_wait_time, pre_uwave_exp_wait_time, 
                    post_uwave_exp_wait_time, aom_delay_time, rf_delay_time, 
                    gate_time, uwave_pi_pulse_plus, uwave_pi_pulse_minus, max_relaxation_time,
                    apd_indices[0], init_state, read_state]
    ret_vals = cxn.pulse_streamer.stream_load(file_name, sequence_args, 1)
    seq_time = ret_vals[0]
    
    # %% Ask user if they wish to run experiment based on run time
    
    seq_time_s = seq_time / (10**9)  # s
    expected_run_time = num_steps * num_reps * num_runs * seq_time_s / 2  # s
    expected_run_time_m = expected_run_time / 60 # m

    
#    msg = 'Expected run time: {:.1f} minutes. ' \
#        'Enter \'y\' to continue: '.format(expected_run_time_m)
#    if input(msg) != 'y':
#        return
    
    
    print(' \nExpected run time: {:.1f} minutes. '.format(expected_run_time_m))
    
    # %% Get the starting time of the function, to be used to calculate run time

    startFunctionTime = time.time()
    
     # %% Set up the microwaves
     # hardwire the tektronix sig gen to use the ms = +1 frequency
    cxn.microwave_signal_generator.set_freq(uwave_freq_plus)
    # hardwire in this special case
#    if init_state == -1 and read_state == -1:
#        cxn.microwave_signal_generator.set_freq(uwave_freq_minus)
#        uwave_pi_pulse_init = round(82.65)
    cxn.microwave_signal_generator.set_amp(uwave_power)
    cxn.microwave_signal_generator.uwave_on()
    
    # %% Collect the data
    
    # Start 'Press enter to stop...'
    tool_belt.init_safe_stop()
    
    for run_ind in range(num_runs):

        print('Run index: {}'.format(run_ind))
        
        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break
        
        # Optimize
        ret_val = optimize.main(cxn, coords, nd_filter, apd_indices, 
                               expected_counts = expected_counts)
        
        coords = ret_val[0]
        optimization_success = ret_val[1]
        
        # Save the coords found and if it failed
        optimization_success_list.append(optimization_success)
        opti_coords_list.append(coords)
        
        print('coords: {}'. format(coords))
        
        print('offset: {}'. format(offsetxy))
        
        x_center= coords[0]+offsetxy[0]
        y_center=coords[1]+offsetxy[1]
        
        print('set coords: {}'. format([x_center,y_center]))
        
        cxn.galvo.write(x_center, y_center)
            
        # Load the APD
        cxn.apd_tagger.start_tag_stream(apd_indices)  
        
        # Shuffle the list of tau indices so that it steps thru them randomly
        shuffle(tau_ind_list)
        
        for tau_ind in tau_ind_list:
            
            # 'Flip a coin' to determine which tau (long/shrt) is used first
            rand_boolean = numpy.random.randint(0, high=2)
            
            if rand_boolean == 1:
                tau_ind_first = tau_ind
                tau_ind_second = -tau_ind - 1
            elif rand_boolean == 0:
                tau_ind_first = -tau_ind - 1
                tau_ind_second = tau_ind
                
            
            # Break out of the while if the user says stop
            if tool_belt.safe_stop():
                break  
            
            # Stream the sequence
            args = [taus[tau_ind_first], polarization_time, signal_time, reference_time, 
                    sig_to_ref_wait_time, pre_uwave_exp_wait_time, 
                    post_uwave_exp_wait_time, aom_delay_time, rf_delay_time, 
                    gate_time, uwave_pi_pulse_plus, uwave_pi_pulse_minus, taus[tau_ind_second],
                    apd_indices[0], init_state, read_state]

            print(' \nFirst relaxation time: {}'.format(taus[tau_ind_first]))
            print('Second relaxation time: {}'.format(taus[tau_ind_second]))  
            
            cxn.pulse_streamer.stream_immediate(file_name, num_reps, args, 1)        
            
            # Each sample is of the form [*(<sig_shrt>, <ref_shrt>, <sig_long>, <ref_long>)]
            # So we can sum on the values for similar index modulus 4 to
            # parse the returned list into what we want.
            new_counts = cxn.apd_tagger.read_counter_separate_gates(1)
            sample_counts = new_counts[0]
            
            sig_gate_counts = sample_counts[::4]
            sig_counts[run_ind, tau_ind] = sum(sig_gate_counts)
            
            count = sum(sample_counts[0::4])
            sig_counts[run_ind, tau_ind_first] = count
            print('First signal = ' + str(count))
            
            count = sum(sample_counts[1::4])
            ref_counts[run_ind, tau_ind_first] = count  
            print('First Reference = ' + str(count))
            
            count = sum(sample_counts[2::4])
            sig_counts[run_ind, tau_ind_second] = count
            print('Second Signal = ' + str(count))

            count = sum(sample_counts[3::4])
            ref_counts[run_ind, tau_ind_second] = count
            print('Second Reference = ' + str(count))
            
        cxn.apd_tagger.stop_tag_stream()

    # %% Hardware clean up

    cxn.apd_tagger.stop_tag_stream()
    cxn.microwave_signal_generator.uwave_off()
    
    # %% Average the counts over the iterations

    avg_sig_counts = numpy.average(sig_counts, axis=0)
    avg_ref_counts = numpy.average(ref_counts, axis=0)
    
    # %% Calculate the t1 data, signal / reference over different relaxation times

    norm_avg_sig = avg_sig_counts / avg_ref_counts
    
    # %% Plot the t1 signal

    raw_fig, axes_pack = plt.subplots(1, 2, figsize=(17, 8.5))

    ax = axes_pack[0]
    ax.plot(taus / 10**6, avg_sig_counts, 'r-', label = 'signal')
    ax.plot(taus / 10**6, avg_ref_counts, 'g-', label = 'reference')
    ax.set_xlabel('Relaxation time (ms)')
    ax.set_ylabel('Counts')
    ax.legend()

    ax = axes_pack[1]
    ax.plot(taus / 10**6, norm_avg_sig, 'b-')
    ax.set_title('T1 Measurement. Initial state: {}, readout state: {}'.format(init_state, read_state))
    ax.set_xlabel('Relaxation time (ms)')
    ax.set_ylabel('Contrast (arb. units)')

    raw_fig.canvas.draw()
    # fig.set_tight_layout(True)
    raw_fig.canvas.flush_events()
    
    # %% Save the data

    endFunctionTime = time.time()

    timeElapsed = endFunctionTime - startFunctionTime

    timestamp = tool_belt.get_time_stamp()
    
    raw_data = {'timestamp': timestamp,
            'timeElapsed': timeElapsed,
            'name': name,
            'init_state': int(init_state),
            'read_state': int(read_state),
            'passed_coords': passed_coords,
            'opti_coords_list': opti_coords_list,
            'offsets': offsetxy,
            'coords-units': 'V',
            'optimization_success_list': optimization_success_list,
            'expected_counts': expected_counts,
            'expected_counts-units': 'kcps',
            'nd_filter': nd_filter,
            'gate_time': gate_time,
            'gate_time-units': 'ns',
            'uwave_freq_init': uwave_freq_init,
            'uwave_freq_init-units': 'GHz',
            'uwave_freq_read': uwave_freq_read,
            'uwave_freq_read-units': 'GHz',
            'uwave_power': uwave_power,
            'uwave_power-units': 'dBm',
            'uwave_pi_pulse_init': uwave_pi_pulse_init,
            'uwave_pi_pulse_init-units': 'ns',
            'uwave_pi_pulse_read': uwave_pi_pulse_read,
            'uwave_pi_pulse_read-units': 'ns',
            'relaxation_time_range': relaxation_time_range,
            'relaxation_time_range-units': 'ns',
            'num_steps': num_steps,
            'num_reps': num_reps,
            'num_runs': num_runs,
            'sig_counts': sig_counts.astype(int).tolist(),
            'sig_counts-units': 'counts',
            'ref_counts': ref_counts.astype(int).tolist(),
            'ref_counts-units': 'counts',
            'norm_avg_sig': norm_avg_sig.astype(float).tolist(),
            'norm_avg_sig-units': 'arb'}
    
    file_path = tool_belt.get_file_path(__file__, timestamp, name)
    tool_belt.save_figure(raw_fig, file_path)
    tool_belt.save_raw_data(raw_data, file_path)
    
    return coords
    
# %%    
    
def decayExp(t, offset, amplitude, decay):
    return offset + amplitude * exp(-decay * t)    
    
# %% Fitting the data
    
def t1_exponential_decay(open_file_name, save_file_type):
    
    directory = 'E:/Team Drives/Kolkowitz Lab Group/nvdata/t1_measurement/'
   
    # Open the specified file
    with open(directory + open_file_name + '.txt') as json_file:
        
        # Load the data from the file
        data = json.load(json_file)
        countsT1 = data["norm_avg_sig"]
        relaxation_time_range = data["relaxation_time_range"]
        num_steps = data["num_steps"]
        spin = data["spin_measured?"]
        
    min_relaxation_time = relaxation_time_range[0] 
    max_relaxation_time = relaxation_time_range[1]
        
    timeArray = numpy.linspace(min_relaxation_time, max_relaxation_time,
                              num=num_steps, dtype=numpy.int32)
    
    offset = 0.8
    amplitude = 0.1
    decay = 1/10000 # inverse ns

    popt,pcov = curve_fit(decayExp, timeArray, countsT1, 
                              p0=[offset, amplitude, decay])
    
    decay_time = 1 / popt[2]
            
    first = timeArray[0]
    last = timeArray[len(timeArray)-1]
    linspaceTime = numpy.linspace(first, last, num=1000)
    
    
    fig, ax= plt.subplots(1, 1, figsize=(10, 8))
    ax.plot(timeArray / 10**6, countsT1,'bo',label='data')
    ax.plot(linspaceTime / 10**6, decayExp(linspaceTime,*popt),'r-',label='fit')
    ax.set_xlabel('Dark Time (ms)')
    ax.set_ylabel('Contrast (arb. units)')
    ax.set_title('T1 of ' + str(spin))
    ax.legend()
    
    text = "\n".join((r'$C + A_0 e^{-t / d}$',
                      r'$C = $' + '%.1f'%(popt[0]),
                      r'$A_0 = $' + '%.1f'%(popt[1]),
                      r'$d = $' + "%.3f"%(decay_time / 10**6) + " ms"))
    
    
    props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
    ax.text(0.70, 0.95, text, transform=ax.transAxes, fontsize=12,
                            verticalalignment="top", bbox=props)
    
    fig.canvas.draw()
    fig.canvas.flush_events()
    
    fig.savefig(open_file_name + 'replot.' + save_file_type)

    