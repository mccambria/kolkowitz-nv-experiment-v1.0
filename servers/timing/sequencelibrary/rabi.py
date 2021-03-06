# -*- coding: utf-8 -*-
"""
Created on Tue Apr 23 17:39:27 2019

@author: mccambria
"""

from pulsestreamer import Sequence
from pulsestreamer import OutputState
import numpy
import utils.tool_belt as tool_belt
from utils.tool_belt import States

LOW = 0
HIGH = 1


def get_seq(pulser_wiring, args):

    # %% Parse wiring and args

    # The first 9 args are ns durations and we need them as int64s
    durations = []
    for ind in range(9):
        durations.append(numpy.int64(args[ind]))

    # Unpack the durations
    tau, polarization_time, reference_time, signal_wait_time, \
        reference_wait_time, background_wait_time, aom_delay_time, \
        gate_time, max_tau = durations

    # Get the APD indices
    apd_index = args[9]

    # Signify which signal generator to use
    state_value = args[10]

    # Get what we need out of the wiring dictionary
    key = 'do_apd_{}_gate'.format(apd_index)
    pulser_do_apd_gate = pulser_wiring[key]
    sig_gen_name = tool_belt.get_signal_generator_name(States(state_value))
    sig_gen_gate_chan_name = 'do_{}_gate'.format(sig_gen_name)
    pulser_do_sig_gen_gate = pulser_wiring[sig_gen_gate_chan_name]
    pulser_do_aom = pulser_wiring['do_532_aom']

    # %% Couple calculated values

    prep_time = polarization_time + signal_wait_time + \
        tau + signal_wait_time
    end_rest_time = max_tau - tau

    # The period is independent of the particular tau, but it must be long
    # enough to accomodate the longest tau
    period = aom_delay_time + polarization_time + reference_wait_time + \
        reference_wait_time + polarization_time + reference_wait_time + \
        reference_time + max_tau

    # %% Define the sequence

    seq = Sequence()

    # APD gating - first high is for signal, second high is for reference
    pre_duration = aom_delay_time + prep_time
    post_duration = reference_time - gate_time + \
        background_wait_time + end_rest_time
#    mid_duration = period - (pre_duration + (2 * gate_time) + post_duration)
    mid_duration = polarization_time + reference_wait_time - gate_time
    train = [(pre_duration, LOW),
             (gate_time, HIGH),
             (mid_duration, LOW),
             (gate_time, HIGH),
             (post_duration, LOW)]
    seq.setDigital(pulser_do_apd_gate, train)

    # # Ungate (high) the APD channel for the background
    # gateBackgroundTrain = [( AOMDelay + preparationTime + polarizationTime + referenceWaitTime + referenceTime + backgroundWaitTime, low),
    #                       (gateTime, high), (endRestTime - gateTime, low)]
    # pulserSequence.setDigital(pulserDODaqGate0, gateBackgroundTrain)

    # Pulse the laser with the AOM for polarization and readout
    train = [(polarization_time, HIGH),
             (signal_wait_time + tau + signal_wait_time, LOW),
             (polarization_time, HIGH),
             (reference_wait_time, LOW),
             (reference_time, HIGH),
             (background_wait_time + end_rest_time + aom_delay_time, LOW)]
    seq.setDigital(pulser_do_aom, train)

    # Pulse the microwave for tau
    pre_duration = aom_delay_time + polarization_time + signal_wait_time
    post_duration = signal_wait_time + polarization_time + \
        reference_wait_time + reference_time + \
        background_wait_time + end_rest_time
    train = [(pre_duration, LOW), (tau, HIGH), (post_duration, LOW)]
    seq.setDigital(pulser_do_sig_gen_gate, train)

    final_digital = [pulser_wiring['do_532_aom'],
                     pulser_wiring['do_sample_clock']]
    final = OutputState(final_digital, 0.0, 0.0)
    return seq, final, [period]


if __name__ == '__main__':
    wiring = {'ao_589_aom': 1, 'ao_638_laser': 0, 'do_532_aom': 3,
              'do_638_laser': 7, 'do_apd_0_gate': 5, 'do_arb_wave_trigger': 6,
              'do_sample_clock': 0, 'do_signal_generator_bnc835_gate': 1,
              'do_signal_generator_tsg4104a_gate': 4}
#    args = [0, 3000, 1000, 1000, 2000, 1000, 1000, 300, 150, 0, 3]
    args = [2000, 3000, 1000, 1000, 2000, 1000, 0, 300, 2000, 0, 3]
    seq = get_seq(wiring, args)[0]
    seq.plot()
