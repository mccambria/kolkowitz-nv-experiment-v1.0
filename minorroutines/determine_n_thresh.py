#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 20:39:55 2019

@author: yanfeili
"""

# %% import
import utils.tool_belt as tool_belt
import majorroutines.optimize as optimize
import numpy
import matplotlib.pyplot as plt
import labrad

def get_Probability_distribution(aList):
        
    def get_unique_value(aList):
        unique_value_list = []
        for i in range(0,len(aList)):
            if aList[i] not in unique_value_list:
                unique_value_list.append(aList[i])
        return unique_value_list
    unique_value = get_unique_value(aList)
    relative_frequency = []
    for i in range(0,len(unique_value)):
        relative_frequency.append(aList.count(unique_value[i])/ (len(aList)))
        
    return unique_value, relative_frequency

#def create_figure():
#    fig, ax = plt.subplots(1, 1, figsize=(10, 8.5))
#    ax.set_xlabel('number of photons (n)')
#    ax.set_ylabel('P(n)')
#    
#    return fig
    
#%% Main
# Connect to labrad in this file, as opposed to control panel
def main(nv_sig, apd_indices, readout_power,readout_time, num_runs, num_reps):
    
    with labrad.connect() as cxn:
        main_with_cxn(cxn, nv_sig, apd_indices, readout_power,readout_time, num_runs, num_reps)

def main_with_cxn(cxn, nv_sig, apd_indices, readout_power,readout_time,num_runs, num_reps):

    tool_belt.reset_cfm(cxn)

# %% Initial Calculation and setup
#    apd_indices = [0]
    
    shared_params = tool_belt.get_shared_parameters_dict(cxn)
    
    #Define some parameters
    
    #delay of aoms and laser
    aom_delay589 = shared_params['532_aom_delay'] 
    #gate_time in this sequence is the readout time ~8 ms 
    gate_time = readout_time
    #get the aom_power corresponding to the laser power we want 
    #readout_power in unit of microwatts
    aom_power = numpy.sqrt((readout_power - 0.432)/1361.811) #uW
    if aom_power > 1:
        aom_power = 1.0
    
    illumination_time = 10**6
    
    # Set up our data structure, an array of NaNs that we'll fill
    # we repeatively collect photons for tR 
    

    sig_counts=[]
    opti_coords_list = []
    
#%% Estimate the lenth of the sequance
    
    seq_args = [gate_time, illumination_time, aom_delay589 ,apd_indices[0], aom_power]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    ret_vals = cxn.pulse_streamer.stream_load('determine_n_thresh.py', seq_args_string)
    
    seq_time = ret_vals[0]
    
    seq_time_s = seq_time / (10**9)  # s
    expected_run_time = num_reps * num_runs * seq_time_s + (0.5 * num_runs)  # s
    expected_run_time_m = expected_run_time / 60 # m

    # Ask to continue and timeout if no response in 2 seconds?

    print(' \nExpected run time: {:.1f} minutes. '.format(expected_run_time_m))
    
#    return
    
#%% Collect data
    tool_belt.init_safe_stop()

    
    for run_ind in range(num_runs):

        # Optimize
        opti_coords = optimize.main_with_cxn(cxn, nv_sig, apd_indices, 532)
        opti_coords_list.append(opti_coords)    
        
        print('Run index: {}'. format(run_ind))

        # Break out of the while if the user says stop
        if tool_belt.safe_stop():
            break
        
        # Load the APD
        cxn.apd_tagger.start_tag_stream(apd_indices)
        
        seq_args = [gate_time, illumination_time, aom_delay589 ,apd_indices[0], aom_power]
        seq_args_string = tool_belt.encode_seq_args(seq_args)
        cxn.pulse_streamer.stream_immediate('determine_n_thresh.py', num_reps, seq_args_string)
    
        # Get the counts
        new_counts = cxn.apd_tagger.read_counter_simple(num_reps)
        
        sig_counts.extend(new_counts)

    cxn.apd_tagger.stop_tag_stream()
    
    
#%% plot the data
    
    unique_value, relative_frequency = get_Probability_distribution(list(sig_counts))    
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 8.5))
    
    ax.plot(unique_value, relative_frequency, 'bo')
    ax.set_xlabel('number of photons (n)')
    ax.set_ylabel('P(n)')

#%% Save data 
    timestamp = tool_belt.get_time_stamp()
    
    # turn the list of unique_values into pure integers, for saving
    unique_value = [int(el) for el in unique_value]
    sig_counts = [int(el) for el in sig_counts]
    
    raw_data = {'timestamp': timestamp,
            'nv_sig': nv_sig,
            'readout_power': readout_power,
            'readout_power_unit':'uW',
            'readout_time':readout_time,
            'readout_time_unit':'ns',
            'illumination_time': illumination_time,
            'illumination_time-units': 'ns',
            'nv_sig-units': tool_belt.get_nv_sig_units(),
            'num_runs': num_runs,
            'num_reps':num_reps,
            'sig_counts': sig_counts,
            'sig_counts-units': 'counts',
            'unique_valuesNV-': unique_value,
            'unique_values-units': 'num of photons',
            'relative_frequencyNV-': relative_frequency,
            'relative_frequency-units': 'occurrences'
            }

    file_path = tool_belt.get_file_path(__file__, timestamp, nv_sig['name'])
    tool_belt.save_raw_data(raw_data, file_path)    
        
    tool_belt.save_figure(fig, file_path)
