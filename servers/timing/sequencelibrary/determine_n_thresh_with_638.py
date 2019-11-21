#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 20 20:40:44 2019

@author: yanfeili
"""

from pulsestreamer import Sequence
from pulsestreamer import OutputState
import numpy

LOW = 0
HIGH = 1

def get_seq(pulser_wiring, args):

    # Unpack the args
    gate_time, illumination_time532, illumination_time589, aom_delay589, apd_indices, aom_power, aom_delay638, ionize_time = args

    readout_time = numpy.int64(gate_time)
    aom_delay589 = numpy.int64(aom_delay589)
    ionize_time = numpy.int64(ionize_time)
    aom_delay638 = numpy.int64(aom_delay638)
    illumination_time532 = numpy.int64(illumination_time532)
    illumination_time589 = numpy.int64(illumination_time589)

    # SCC photon collection test period
    period =  (illumination_time532 + ionize_time + aom_delay638+ illumination_time589 + aom_delay589 + 400)*2
    
    # Get what we need out of the wiring dictionary
    pulser_do_apd_gate = pulser_wiring['do_apd_{}_gate'.format(apd_indices)]
    pulser_do_clock = pulser_wiring['do_sample_clock']
    pulser_do_aom532 = pulser_wiring['do_532_aom']
    pulser_ao_aom589 = pulser_wiring['ao_589_aom']
    pulser_ao_aom638 = pulser_wiring['do_638_aom']


    seq = Sequence()


    #collect photons for certain timewindow tR in APD
    train = [(aom_delay589 + illumination_time532 + ionize_time + aom_delay638 + 100, LOW), (readout_time, HIGH), (illumination_time589 - readout_time + 300, LOW),
             (aom_delay589 + illumination_time532 + ionize_time + aom_delay638 + 100, LOW), (readout_time, HIGH), (illumination_time589 - readout_time + 300, LOW)]
    seq.setDigital(pulser_do_apd_gate, train)
    
    #clock pulse
    train = [(aom_delay589 + illumination_time532 + ionize_time + aom_delay638 + 100 + illumination_time589 + 100, LOW), (100, HIGH), (100, LOW),
             (aom_delay589 + illumination_time532 + ionize_time + aom_delay638 + 100 + illumination_time589 + 100, LOW), (100, HIGH), (100, LOW)]
    seq.setDigital(pulser_do_clock, train)

    #illuminate with 532
    train = [ (illumination_time532, HIGH), (period/2 -illumination_time532 , LOW), 
              (illumination_time532, HIGH), (period/2 -illumination_time532 , LOW)]
    seq.setDigital(pulser_do_aom532, train)
    
    #readout with 589
    train = [(illumination_time532 + ionize_time + aom_delay638 + 100, LOW), (illumination_time589, aom_power), (aom_delay589 + 300, LOW),
             (illumination_time532 + ionize_time + aom_delay638 + 100, LOW), (illumination_time589, aom_power), (aom_delay589 + 300, LOW)]
    seq.setAnalog(pulser_ao_aom589, train) 
    
    #ionize with 639 
    train = [(illumination_time532+ 100, LOW), (ionize_time, HIGH), (aom_delay638 + illumination_time589 + aom_delay589 + 300, LOW), (period/2, LOW)]
    seq.setDigital(pulser_ao_aom638, train)
    
    final_digital = []
    final = OutputState(final_digital, 0.0, 0.0)

    return seq, final, [period]


if __name__ == '__main__':
    wiring = {'do_apd_0_gate': 1,
              'do_532_aom': 2,
              'sig_gen_gate_chan_name': 3,
               'do_sample_clock':4,
               'ao_589_aom': 0,
               'do_638_aom': 6              }
    args = [1000, 500, 1200, 100, 0,1.0, 300, 1000]
    seq, final, _ = get_seq(wiring, args)
    seq.plot()