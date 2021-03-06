# -*- coding: utf-8 -*-
"""
Created on Sat May  4 08:34:08 2019

@author: Aedan
"""

from pulsestreamer import Sequence
import numpy

LOW = 0
HIGH = 1


def get_seq(pulser_wiring, args):
    
    # %% Parse wiring and args
    
    # The first 11 args are ns durations and we need them as int64s
    durations = []
    for ind in range(12):
        durations.append(numpy.int64(args[ind]))        
        
    # Unpack the durations
    tau_shrt, polarization_time, signal_time, reference_time,  \
            sig_to_ref_wait_time, pre_uwave_exp_wait_time,  \
            post_uwave_exp_wait_time, aom_delay_time, rf_delay_time,  \
            gate_time, pi_pulse, tau_long = durations
        
    # Get the APD indices
    sig_shrt_apd_index, ref_shrt_apd_index, \
        sig_long_apd_index, ref_long_apd_index = args[12:16]
        
    # Get what we need out of the wiring dictionary
    key = 'do_apd_gate_{}'.format(sig_shrt_apd_index)
    pulser_do_sig_shrt_apd_gate = pulser_wiring[key]
    print(pulser_do_sig_shrt_apd_gate)
    key = 'do_apd_gate_{}'.format(ref_shrt_apd_index)
    pulser_do_ref_shrt_apd_gate = pulser_wiring[key]
    print(pulser_do_ref_shrt_apd_gate)
    
    key = 'do_apd_gate_{}'.format(sig_long_apd_index)
    pulser_do_sig_long_apd_gate = pulser_wiring[key]
    print(pulser_do_sig_long_apd_gate)
    key = 'do_apd_gate_{}'.format(ref_long_apd_index)
    pulser_do_ref_long_apd_gate = pulser_wiring[key]
    print(pulser_do_ref_long_apd_gate)
    
    
    pulser_do_uwave = pulser_wiring['do_uwave_gate']
    pulser_do_aom = pulser_wiring['do_aom']
    
    # %% Write the microwave sequence to be used.
    
    # In t1, the sequence is just a pi pulse, wait for a relaxation time, then
    # then a second pi pulse
    
    # I define both the time of this experiment, which is useful for the AOM 
    # and gate sequences to dictate the time for them to be LOW
    # And I define the actual uwave experiement to be plugged into the rf
    # sequence. I hope that this formatting works.
    
    # With future protocols--ramsey, spin echo, etc--it will be easy to use 
    # this format of sequence building and just change this secion of the file
    
    uwave_experiment_shrt = pi_pulse + tau_shrt + pi_pulse
    
    uwave_experiment_seq_shrt = [(pi_pulse, HIGH), (tau_shrt, LOW), 
                                     (pi_pulse, HIGH)]
    
    uwave_experiment_long = pi_pulse + tau_long + pi_pulse
    
    uwave_experiment_seq_long = [(pi_pulse, HIGH), (tau_long, LOW), 
                                     (pi_pulse, HIGH)]
    
    # %% Couple calculated values

    prep_time = aom_delay_time + rf_delay_time + \
        polarization_time + pre_uwave_exp_wait_time + \
        uwave_experiment_shrt + post_uwave_exp_wait_time
        
    up_to_long_gates = prep_time + signal_time + sig_to_ref_wait_time + \
        reference_time + pre_uwave_exp_wait_time + \
        uwave_experiment_long + post_uwave_exp_wait_time
    
    after_short_gates = pre_uwave_exp_wait_time + \
        uwave_experiment_long + post_uwave_exp_wait_time + \
        signal_time + sig_to_ref_wait_time + reference_time

    # %% Calclate total period. This is fixed for each tau index
        
    # The period is independent of the particular tau, but it must be long
    # enough to accomodate the longest tau
    period = aom_delay_time + rf_delay_time + polarization_time + \
        pre_uwave_exp_wait_time + uwave_experiment_shrt + post_uwave_exp_wait_time + \
        signal_time + sig_to_ref_wait_time + reference_time + pre_uwave_exp_wait_time + \
        uwave_experiment_long + post_uwave_exp_wait_time + \
        signal_time + sig_to_ref_wait_time + reference_time
        
    # %% Define the sequence

    seq = Sequence()

    # right now, we will just use one signal and one reference, the 'shrt' ones
    
    # Short Signal APD gate
    pre_duration = prep_time
    post_duration = signal_time - gate_time + sig_to_ref_wait_time + \
        reference_time + after_short_gates
        
    train = [(pre_duration, LOW), (gate_time, HIGH), (post_duration, LOW)]
    seq.setDigital(pulser_do_sig_shrt_apd_gate, train)
        
    # Short Reference APD gate
    pre_duration = prep_time + signal_time + sig_to_ref_wait_time
    post_duration = reference_time - gate_time + after_short_gates
    
    train = [(pre_duration, LOW), (gate_time, HIGH), (post_duration, LOW)]
    seq.setDigital(pulser_do_ref_shrt_apd_gate, train)  
    
    # Long Signal APD gate
    pre_duration = up_to_long_gates
    post_duration = signal_time - gate_time + sig_to_ref_wait_time + \
        reference_time
        
    train = [(pre_duration, LOW), (gate_time, HIGH), (post_duration, LOW)]
    seq.setDigital(pulser_do_sig_long_apd_gate, train)
        
    # Long Reference APD gate
    pre_duration = up_to_long_gates + signal_time + sig_to_ref_wait_time
    post_duration = reference_time - gate_time
    
    train = [(pre_duration, LOW), (gate_time, HIGH), (post_duration, LOW)]
    seq.setDigital(pulser_do_ref_long_apd_gate, train)  

    # Pulse the laser with the AOM for polarization and readout
    train = [(rf_delay_time + polarization_time, HIGH),
             (pre_uwave_exp_wait_time + uwave_experiment_shrt + post_uwave_exp_wait_time, LOW),
             (signal_time, HIGH),
             (sig_to_ref_wait_time, LOW),
             (reference_time, HIGH),
             (pre_uwave_exp_wait_time + uwave_experiment_long + post_uwave_exp_wait_time, LOW),
             (signal_time, HIGH),
             (sig_to_ref_wait_time, LOW),
             (reference_time + aom_delay_time, HIGH)]
    seq.setDigital(pulser_do_aom, train)   
    
    # Pulse the microwave for tau
    pre_duration = aom_delay_time + polarization_time + pre_uwave_exp_wait_time
    mid_duration = post_uwave_exp_wait_time + signal_time + sig_to_ref_wait_time + \
        reference_time + pre_uwave_exp_wait_time
    post_duration = post_uwave_exp_wait_time + signal_time + \
        sig_to_ref_wait_time + reference_time + rf_delay_time
        
    train = [(pre_duration, LOW)]
    train.extend(uwave_experiment_seq_shrt)
    train.extend([(mid_duration, LOW)])
    train.extend(uwave_experiment_seq_long)
    train.extend([(post_duration, LOW)])
    seq.setDigital(pulser_do_uwave, train)
    
    return seq, [period]
    
if __name__ == '__main__':
    wiring = {'do_apd_gate_0': 0,
              'do_apd_gate_1': 1,
              'do_apd_gate_2': 6,
              'do_apd_gate_3': 7,
              'do_aom': 2,
              'do_uwave_gate': 3}

    args = [2000, 3000, 3000, 3000, 2000, 1000, 1000, 0, 0, 300, 55, 88000, 0, 1, 2, 3]
    seq, ret_vals = get_seq(wiring, args)
    seq.plot()    
        