# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 10:45:09 2019

This file is used to determine the cutoff for photon count nuer for individual
measurmenets between the charge states of the NV.

Collect the photon counts under yellow illumination, after reionizing NV into
NV- with green light. A second collection occurs after ionizing NV to NV0 with
red light.

@author: yanfeili
"""
import utils.tool_belt as tool_belt
import majorroutines.optimize as optimize
import numpy
import matplotlib.pyplot as plt
import labrad
import minorroutines.photonstatistics as ps

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
def main(nv_sig, apd_indices, num_reps):

    with labrad.connect() as cxn:
        main_with_cxn(cxn, nv_sig, apd_indices, num_reps)

def main_with_cxn(cxn, nv_sig, apd_indices, num_reps):

    tool_belt.reset_cfm(cxn)

# %% Initial Calculation and setup
#    apd_indices = [0]
    readout_time = nv_sig['pulsed_SCC_readout_dur']
    reionization_time = nv_sig['pulsed_reionization_dur']
    ionization_time = nv_sig['pulsed_ionization_dur']
    aom_ao_589_pwr = nv_sig['am_589_power']
#    nd_filter = nv_sig['nd_filter']

    shared_params = tool_belt.get_shared_parameters_dict(cxn)

    #delay of aoms and laser
    laser_515_delay = shared_params['515_laser_delay']
    aom_589_delay = shared_params['589_aom_delay']
    laser_638_delay = shared_params['638_DM_laser_delay']
    wait_time = shared_params['post_polarization_wait_dur']

#    readout_power = aom_ao_589_pwr

    # Set up our data structure, list
    # we repeatively collect photons for tR

#    counts = []
    ref_counts = []
    sig_counts=[]
    opti_coords_list = []

    # %% Read the optical power for red, yellow, and green light
    green_optical_power_pd, green_optical_power_mW, \
            red_optical_power_pd, red_optical_power_mW, \
            yellow_optical_power_pd, yellow_optical_power_mW = \
            tool_belt.measure_g_r_y_power(
                                  nv_sig['am_589_power'], nv_sig['nd_filter'])

    readout_power = yellow_optical_power_mW

#%% Estimate the lenth of the sequance

    # We're just going to use the sequence for testign the red/green laser pulses.
    # It is exactly what we wnat, as long as we set the test_color_ind to 638
    seq_args = [readout_time, reionization_time,
                ionization_time, wait_time, laser_515_delay, aom_589_delay,
                laser_638_delay,apd_indices[0], aom_ao_589_pwr, 638]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    ret_vals = cxn.pulse_streamer.stream_load('SCC_optimize_638_and_532_power_and_duration.py', seq_args_string)

    seq_time = ret_vals[0]

    seq_time_s = seq_time / (10**9)  # s
    expected_run_time = num_reps  * seq_time_s #s
    expected_run_time_m = expected_run_time / 60 # m

    # Ask to continue and timeout if no response in 2 seconds?

    print(' \nExpected run time: {:.1f} minutes. '.format(expected_run_time_m))

#    return

#%% Collect data
    tool_belt.init_safe_stop()


#    for run_ind in range(num_runs):

    # Optimize
    opti_coords = optimize.main_with_cxn(cxn, nv_sig, apd_indices, 532, disable=True)
    opti_coords_list.append(opti_coords)

#    print('Run index: {}'. format(run_ind))

    # Break out of the while if the user says stop
#    if tool_belt.safe_stop():
#        break

    # Load the APD
    cxn.apd_tagger.start_tag_stream(apd_indices)

    seq_args = [readout_time, reionization_time,
                ionization_time, wait_time, laser_515_delay, aom_589_delay,
                laser_638_delay,apd_indices[0], aom_ao_589_pwr, 638]
    seq_args_string = tool_belt.encode_seq_args(seq_args)
    cxn.pulse_streamer.stream_immediate('SCC_optimize_638_and_532_power_and_duration.py', num_reps, seq_args_string)

    # Get the counts
    new_counts = cxn.apd_tagger.read_counter_separate_gates(1)

    sample_counts = new_counts[0]

    cxn.apd_tagger.stop_tag_stream()

    sig_counts = sample_counts[0::2]
    ref_counts = sample_counts[1::2]

#%% plot the data and the fit

    # signal -> NV0, reference -> NVm
    unique_value1, relative_frequency1 = get_Probability_distribution(list(sig_counts))
    unique_value2, relative_frequency2 = get_Probability_distribution(list(ref_counts))

    fig, ax = plt.subplots(1, 1, figsize=(10, 8.5))

#    #Shield's NVm, NV0 full model fit
#    g00,g01,y01,y00 = ps.get_curve_fit_NV0(readout_time,readout_power,unique_value1, relative_frequency1)
#    gm0,gm1,ym1,ym0 = ps.get_curve_fit_NVm(readout_time,readout_power,unique_value2, relative_frequency2)
#    print('NV0 full model fit: ' + str(g00,g01,y01,y00))
#    print('NVm full model fit:' + str(gm0,gm1,ym1,ym0))
#
#    #Double poisson fit
#    a0, b0, numbla10, numbla20 = ps.get_gaussian_distribution_fit(readout_time,readout_power,unique_value1, relative_frequency1)
#    am, bm, numbla1m, numbla2m = ps.get_gaussian_distribution_fit(readout_time,readout_power,unique_value2, relative_frequency2)
#    print('NV0 double poisson fit: '+str(a0, b0, numbla10, numbla20))
#    print('NVm double poisson fit: '+str(am, bm, numbla1m, numbla2m))
#
#    photon_numbers1 = list(range(max(unique_value1)))
#    photon_numbers2 = list(range(max(unique_value2)))
#    curve1 = ps.get_photon_distribution_curveNV0(photon_numbers1,readout_time, g00,g01,y01,y00)
#    curve2 = ps.get_photon_distribution_curveNVm(photon_numbers2,readout_time, gm0,gm1,ym1,ym0)
#    curve3 = ps.get_poisson_distribution_curve(photon_numbers1,a0, b0, numbla10, numbla20)
#    curve4 = ps.get_poisson_distribution_curve(photon_numbers2,am, bm, numbla1m, numbla2m)


#    ax.plot(photon_numbers1,curve1,'r')
#    ax.plot(photon_numbers2,curve2,'b')
#    ax.plot(photon_numbers1,curve3,'y')
#    ax.plot(photon_numbers2,curve4,'g')
    ax.plot(unique_value1, relative_frequency1, 'ro', label='Ionization pulse')
    ax.plot(unique_value2, relative_frequency2, 'ko', label='Ionization pulse absent')
    ax.set_xlabel('number of photons (n)')
    ax.set_ylabel('P(n)')
    ax.legend()

    text = '\n'.join(('Reionization time (532 nm)' + '%.3f'%(reionization_time/10**3) + 'us',
                      'Illumination time (589 nm)' + '%.3f'%(readout_time/10**3) + 'us',
                      'Ionization time (638 nm)' + '%.3f'%(ionization_time/10**3) + 'us',
                      'Readout time' + '%.3f'%(readout_time/10**3)+ 'us'))

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.55, 0.85, text, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', bbox=props)
#%% monitor photon counts

    fig2, ax2 = plt.subplots(1,1, figsize = (10, 8.5))

#    time_axe_sig = ps.get_time_axe(seq_time_s*2, readout_time*10**-9,sig_counts)
    sig_counts_cps = ps.get_photon_counts(readout_time*10**-9, sig_counts)
    sig_len=len(sig_counts_cps)

#    time_axe_ref = numpy.array(ps.get_time_axe(seq_time_s*2, readout_time*10**-9,ref_counts)) + seq_time_s
    ref_counts_cps = ps.get_photon_counts(readout_time*10**-9, ref_counts)
    ref_len=len(ref_counts_cps)

    ax2.plot(numpy.linspace(0,sig_len-1, sig_len), numpy.array(sig_counts_cps)/10**3, 'r', label='Ionization pulse')
    ax2.plot(numpy.linspace(0,ref_len-1, ref_len), numpy.array(ref_counts_cps)/10**3, 'k', label='Ionization pulse absent')
    ax2.set_xlabel('Rep number')
    ax2.set_ylabel('photon counts (kcps)')
    ax2.legend()

    text = '\n'.join(('Readout time (589 nm)'+'%.3f'%(readout_time/10**3) + 'us',
                     'Readout power (589 nm)'+'%.3f'%(readout_power*10**3) + 'uW'))

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax2.text(0.55, 0.85, text, transform=ax2.transAxes, fontsize=12,
            verticalalignment='top', bbox=props)


#%% Save data
    timestamp = tool_belt.get_time_stamp()

    # turn the list of unique_values into pure integers, for saving
    unique_value1 = [int(el) for el in unique_value1]
    unique_value2 = [int(el) for el in unique_value2]
    relative_frequency1 = [int(el) for el in relative_frequency1]
    relative_frequency2 = [int(el) for el in relative_frequency2]
    sig_counts = [int(el) for el in sig_counts]
    ref_counts = [int(el) for el in ref_counts]

    raw_data = {'timestamp': timestamp,
            'nv_sig': nv_sig,
            'nv_sig-units': tool_belt.get_nv_sig_units(),
            'green_optical_power_pd': green_optical_power_pd,
            'green_optical_power_pd-units': 'V',
            'green_optical_power_mW': green_optical_power_mW,
            'green_optical_power_mW-units': 'mW',
            'red_optical_power_pd': red_optical_power_pd,
            'red_optical_power_pd-units': 'V',
            'red_optical_power_mW': red_optical_power_mW,
            'red_optical_power_mW-units': 'mW',
            'yellow_optical_power_pd': yellow_optical_power_pd,
            'yellow_optical_power_pd-units': 'V',
            'yellow_optical_power_mW': yellow_optical_power_mW,
            'yellow_optical_power_mW-units': 'mW',
            'num_reps':num_reps,
            'sig_counts': sig_counts,
            'sig_counts-units': 'counts',
            'ref_counts': ref_counts,
            'ref_counts-units': 'counts',
            'unique_valuesNV-': unique_value1,
            'unique_values-units': 'num of photons',
            'relative_frequencyNV0': relative_frequency1,
            'relative_frequency-units': 'occurrences',
            'unique_valuesNV-': unique_value2,
            'unique_values-units': 'num of photons',
            'relative_frequencyNV-': relative_frequency2,
            'relative_frequency-units': 'occurrences'
            }

    file_path = tool_belt.get_file_path(__file__, timestamp, nv_sig['name'])
    tool_belt.save_raw_data(raw_data, file_path)

    tool_belt.save_figure(fig, file_path + '-histogram')
    tool_belt.save_figure(fig2, file_path + '-counts')