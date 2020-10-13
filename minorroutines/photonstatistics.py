# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
#photon statistics analysis module 
#all readout_time in unit of s
#all readout_power in unit of uW
import scipy.stats
import scipy.special
import math  
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

#%% define the four parameters that are used in the photon statistics
def get_g0(readout_power):
    P = readout_power*10**-3
    g0 = 39*P**2 /(1+P/134)
    return g0 

def get_g1(readout_power):
    P = readout_power*10**-3 
    g1 = 310*P**2 / (1 + P/53.2)
    return g1 

def get_y0(readout_power):
    P = readout_power*10**-3
    y0 = 1.63*10**3 * P/(1+P/134) + 0.268*10**3
    return y0 

def get_y1(readout_power):
    P = readout_power*10**-3
    y1 = 46.2*10**3 * P/(1+ P/53)+ 0.268*10**3
    return y1 

#%% Photon statistical model and fidelity
# Photon statistics of initializing in NV- and reading out for tR at power P
# return the probabilty of getting n photons
def PhotonNVm(n,readout_time,readout_power):
    P = readout_power
    g0 = get_g0(P)
    g1 = get_g1(P)
    y1 = get_y1(P)
    y0 = get_y0(P)
    tR =readout_time 
    poisspdf2 = scipy.stats.poisson(y1*tR)
    def Integ(t):
        poisspdf1 = scipy.stats.poisson(y1*t+y0*(tR-t))
        integ = g1*math.e**((g0-g1)*t-g0*tR)*scipy.special.jv(0, 2*math.sqrt(g1*g0*t*(tR-t)))*poisspdf1.pmf(n)
        + math.sqrt((g1*g0*t/(tR-t)))*math.e**((g0-g1)*t-g0*tR)*scipy.special.jv(1, 2*math.sqrt(g1*g0*t*(tR-t)))* poisspdf1.pmf(n)
        return integ
    val, err = scipy.integrate.quad(Integ,0,tR)
    result = val + math.e**(-g1*tR)*poisspdf2.pmf(n)
    return result
# Photon statistics of initializing in NV0 and reading out for tR at power P\
# return probability of getting n photons
def PhotonNV0(n,readout_time,readout_power):
    P = readout_power
    g0 = get_g0(P)
    g1 = get_g1(P)
    y1 = get_y1(P)
    y0 = get_y0(P)
    tR =readout_time 
    poisspdf2 = scipy.stats.poisson(y0*tR)
    def Integ(t):
        poisspdf1 = scipy.stats.poisson(y0*t+y1*(tR-t))
        integ = g0*math.e**((g0-g1)*t-g0*tR)*scipy.special.jv(0, 2*math.sqrt(g1*g0*t*(tR-t)))*poisspdf1.pmf(n)
        + math.sqrt((g1*g0*t/(tR-t)))*math.e**((g1-g0)*t-g1*tR)*scipy.special.jv(1, 2*math.sqrt(g1*g0*t*(tR-t)))* poisspdf1.pmf(n)
        return integ
    val, err = scipy.integrate.quad(Integ,0,tR)
    result = val + math.e**(-g0*tR)*poisspdf2.pmf(n)
    return result
# draw a graph of photon distribution
def plotPhotonDistribution(readout_time,readout_power, NV_state,max_range):
    tR = readout_time
    P = readout_power
    #Plot photon distribution when initializing in NV-
    if NV_state == 1:
        NVm_probability_list = []
        for i in range(0,max_range):
            NVm_probability_list.append([PhotonNVm(i,tR,P)])
        photon_number = list(range(0,max_range))
        plt.plot(photon_number,NVm_probability_list,'b')
        plt.xlabel('number of photons')
        plt.ylabel('P(n)')
        return NVm_probability_list
    #Plot photon distribution when initializing in NV0
    if NV_state == 0:
        NV0_probability_list = []
        for i in range(0,max_range):
            NV0_probability_list.append([PhotonNV0(i,tR,P)])
        photon_number = list(range(0,max_range))
        plt.plot(photon_number,NV0_probability_list,'r')
        plt.xlabel('number of photons')
        plt.ylabel('P(n)')
        return NV0_probability_list
    else:
        print('NV_state is not specified')
#plot two distributions together 
#plotPhotonDistribution(820*10**-3,240*10**-6,1,20)
#plotPhotonDistribution(820*10**-3,240*10**-6,0,20)
#plt.show()    

#get measurement fidelity 
def get_readout_fidelity(readout_time, readout_power, NV_state,n_threshold):
    tR = readout_time
    P = readout_power 
    n = 0 
    Probability_NVm_les_nth = 0 
    Probability_NV0_les_nth = 0 
    for n in range(0,n_threshold):
        Probability_NVm_les_nth += PhotonNVm(n,tR,P)
        Probability_NV0_les_nth += PhotonNV0(n,tR,P)
    # fidelity of correctly determining NV0 state
    if NV_state == 0:
        fidelity = Probability_NV0_les_nth /(Probability_NV0_les_nth + Probability_NVm_les_nth)
        return fidelity
    # fidelity of correctly determining NV- state
    if NV_state == 1:
        fidelity = (1 - Probability_NVm_les_nth) /((1-Probability_NV0_les_nth) + (1 - Probability_NVm_les_nth))
        return fidelity
#%% curve fit to the photon distribution
def get_photon_distribution_curve(photon_number_range,readout_time, g0,g1,y1,y0):    
    tR = readout_time 
    poisspdf2 = scipy.stats.poisson(y1*tR)
    poisspdf3 = scipy.stats.poisson(y0*tR)
    photon_number = list(range(photon_number_range))
    i = 0
    curve = []
    for i in range(len(photon_number)): 
        n = i
        def IntegNVm(t):
            poisspdf1 = scipy.stats.poisson(y1*t+y0*(tR-t))
            integ = g1*math.e**((g0-g1)*t-g0*tR)*poisspdf1.pmf(n)
            + math.sqrt((g1*g0*t/(tR-t)))*math.e**((g0-g1)*t-g0*tR)*scipy.special.jv(1, 2*math.sqrt(g1*g0*t*(tR-t)))* poisspdf1.pmf(n)
            return integ
        def IntegNV0(t):
            poisspdf4 = scipy.stats.poisson(y0*t+y1*(tR-t))
            integ = g0*math.e**((g0-g1)*t-g0*tR)*poisspdf4.pmf(n)
            + math.sqrt((g1*g0*t/(tR-t)))*math.e**((g1-g0)*t-g1*tR)*scipy.special.jv(1, 2*math.sqrt(g1*g0*t*(tR-t)))* poisspdf4.pmf(n)
            return integ
        valNVm, err = scipy.integrate.quad(IntegNVm,0,tR)
        valNV0, err = scipy.integrate.quad(IntegNV0,0,tR)
        result = 0.5*(valNVm + valNV0 + math.e**(-g1*tR)*poisspdf2.pmf(n) + math.e**(-g0*tR)*poisspdf3.pmf(n))
        curve.append(result)
        i += 1
    return curve 

# fit the model to the actual data and return the 4 rates: g0, g1, y1, y0
def get_curve_fit(readout_time,readout_power,data):
    tR = readout_time
    P = readout_power
    initial_guess = [10,100,10000,1000]
    def get_photon_distribution_curve(photon_number,g0,g1,y1,y0):    
        poisspdf2 = scipy.stats.poisson(y1*tR)
        poisspdf3 = scipy.stats.poisson(y0*tR)
        photon_number = list(photon_number)
        i = 0
        curve = []
        for i in range(len(photon_number)): 
            n = i
            def IntegNVm(t):
                poisspdf1 = scipy.stats.poisson(y1*t+y0*(tR-t))
                integ = g1*math.e**((g0-g1)*t-g0*tR)*poisspdf1.pmf(n) + math.sqrt((g1*g0*t/(tR-t)))*math.e**((g0-g1)*t-g0*tR)*scipy.special.jv(1, 2*math.sqrt(g1*g0*t*(tR-t)))* poisspdf1.pmf(n)
                return integ
            def IntegNV0(t):
                poisspdf4 = scipy.stats.poisson(y0*t+y1*(tR-t))
                integ = g0*math.e**((g0-g1)*t-g0*tR)*poisspdf4.pmf(n) + math.sqrt(g1*g0*t/(tR-t))*math.e**((g1-g0)*t-g1*tR)*scipy.special.jv(1, 2*math.sqrt(g1*g0*t*(tR-t)))* poisspdf4.pmf(n)
                return integ
            valNVm, err = scipy.integrate.quad(IntegNVm,0,tR)
            valNV0, err = scipy.integrate.quad(IntegNV0,0,tR)
            result = 0.5*valNVm + 0.5*valNV0 + 0.5*math.e**(-g1*tR)*poisspdf2.pmf(n) + 0.5*math.e**(-g0*tR)*poisspdf3.pmf(n)
            curve.append(result)
            i += 1
        return curve 
    max_range = len(data)
    photon_number = list(range(0,max_range))
    popt, pcov = curve_fit(get_photon_distribution_curve, photon_number, data, p0 = initial_guess)
    return popt  

#def get_curve_fit_NVm(readout_time,readout_power,data):
#    tR = readout_time
#    P = readout_power
#    initial_guess = [10,100,10000,1000]
#    def get_photon_distribution_curve(photon_number,g0,g1,y1,y0):    
#        poisspdf2 = scipy.stats.poisson(y1*tR)
#        photon_number = list(photon_number)
#        i = 0
#        curve = []
#        for i in range(len(photon_number)): 
#            n = i
#            def IntegNVm(t):
#                poisspdf1 = scipy.stats.poisson(y1*t+y0*(tR-t))
#                integ = g1*math.e**((g0-g1)*t-g0*tR)*poisspdf1.pmf(n) + math.sqrt((g1*g0*t/(tR-t)))*math.e**((g0-g1)*t-g0*tR)*scipy.special.jv(1, 2*math.sqrt(g1*g0*t*(tR-t)))* poisspdf1.pmf(n)
#                return integ
#
#            valNVm, err = scipy.integrate.quad(IntegNVm,0,tR)
#            result = valNVm + math.e**(-g1*tR)*poisspdf2.pmf(n)
#            curve.append(result)
#            i += 1
#        return curve 
#    max_range = len(data)
#    photon_number = list(range(0,max_range))
#    popt, pcov = curve_fit(get_photon_distribution_curve, photon_number, data, p0 = initial_guess)
#    return popt  


#%% test module that simulates data to test the curve fit
#given readout time and power, return a list of probability of observing each number of photon
def get_PhotonNV_list(photon_number,readout_time,readout_power):
    P = readout_power
    tR =readout_time 
    i =0 
    Probability_list = []
    for i in range(len(photon_number)):
        n = i 
        result = 0.5*(PhotonNVm(n,tR,P) + PhotonNV0(n,tR,P))
        Probability_list.append(result)
    return Probability_list

# give a set of test data based on the model given by Shields' paper 
def get_fake_data(data,variation):
    i = 0 
    fake_data = []
    for i in range(len(data)):
        fake_data.append(abs(data[i] + np.random.randint(-1,2)* variation * np.random.random_sample()))
    return fake_data

# fit the model to the fake data generated
def run_test(photon_number_range, variation,readout_time,readout_power):
    tR = readout_time
    P = readout_power
    photon_number = list(range(photon_number_range))
    data = get_PhotonNV_list(photon_number, tR, P)
    fake_data = get_fake_data(data, variation)
    g0, g1, y1, y0= get_curve_fit(tR, P, fake_data)
    print( "At power = "+ str(P*10**3) + " nW" + " : "+ "Expected value: " + "g0 = " + str(get_g0(P)) +' , ' + "g1 = "+ str(get_g1(P))+ ',' + 
    "y1 = " + str(get_y1(P)) + ' ; ' + 'y0 =' + str(get_y0(P)))
    print("Actual value: " + "g0 = " + str(g0) +' , ' + "g1 = "+ str(g1)+ ',' + 
    "y1 = " + str(y1) + ' ; ' + 'y0 =' + str(y0))
    plt.plot(photon_number, fake_data,'b')
    plt.plot(photon_number, get_photon_distribution_curve(photon_number_range,tR, g0,g1,y1,y0),'r')
    plt.xlabel('number of photons')
    plt.ylabel('P(n)')
    plt.show()
    
#%% Power/n_threshold optimization 

def get_optimized_power(readout_time, power_range, n_threshold):
    tR = readout_time
    power_list = list(np.linspace(power_range[0],power_range[1],num = 1000))
    fidelity_list = []
    i = 0 
    for i in range(len(power_list)):
        fidelity_list.append(get_readout_fidelity(tR, power_list[i], 0, n_threshold))
        i+=1
    highest_fidelity_index = fidelity_list.index(max(fidelity_list))
    highest_fidelity = max(fidelity_list)
    optimized_power = power_list[highest_fidelity_index]
    return highest_fidelity, optimized_power
    
def get_fidelity_difference(readout_time, readout_power, n_threshold):
    return abs(get_readout_fidelity(readout_time, readout_power, 0, n_threshold) - get_readout_fidelity(readout_time, readout_power, 1, n_threshold))

def get_fidelity_list_power(readout_time, power_range, n_threshold):
    tR = readout_time
    power_list = list(np.linspace(power_range[0],power_range[1],num = 1000))
    i =0 
    fidelity_difference_list = []
    for i in range(len(power_list)):
        fidelity_difference_list.append(get_fidelity_difference(tR, power_list[i],n_threshold))
    return fidelity_difference_list
                        
def get_optimized_n_threshold(readout_time, power_range, n_threshold_list):
    tR = readout_time
    fidelity_difference_list = []
    i = 0
    for i in range(len(n_threshold_list)):
        n_th = n_threshold_list[i]
        fidelity_difference_list.append(min(get_fidelity_list_power(tR, power_range, n_th)))
    lower_fidelity_difference_index = fidelity_difference_list.index(min(fidelity_difference_list))
    optimized_n = n_threshold_list[lower_fidelity_difference_index]
    return optimized_n

#given a power_range, a two-element list, return the optimized n_threshold, power, highest fidelity
def get_optimized_fidelity(readout_time, power_range, n_threshold_list):
    tR = readout_time
    P = power_range
    optimized_n_threshold = get_optimized_n_threshold(tR, P, n_threshold_list)
    highest_fidelity, optimized_power = get_optimized_power(tR, P, optimized_n_threshold)
    return optimized_n_threshold, optimized_power, highest_fidelity
    
#%% curve fit and figure drawing for each charge state
#given actural data: 
#unique_value: number of photons that are collected; 
#relative_frequency: the probabiltiy of appearance for each number of photons
def get_curve_fit_NVm(readout_time,readout_power,unique_value, relative_frequency):
    tR = readout_time
    P = readout_power
    initial_guess = [10,100,10000,1000]
    def get_photon_distribution_curve(unique_value,g0,g1,y1,y0):    
        poisspdf2 = scipy.stats.poisson(y1*tR)
        photon_number = unique_value
        i = 0
        curve = []
        for i in range(len(photon_number)): 
            n = photon_number[i]
            def IntegNVm(t):
                poisspdf1 = scipy.stats.poisson(y1*t+y0*(tR-t))
                integ = g1*math.e**((g0-g1)*t-g0*tR)*poisspdf1.pmf(n) + math.sqrt(abs(g1*g0*t/(tR-t)))*math.e**((g0-g1)*t-g0*tR)*scipy.special.jv(1, 2*math.sqrt(abs(g1*g0*t*(tR-t))))* poisspdf1.pmf(n)
                return integ

            valNVm, err = scipy.integrate.quad(IntegNVm,0,tR)
            result = valNVm + math.e**(-g1*tR)*poisspdf2.pmf(n)
            curve.append(result)
            i += 1
        return curve 
    photon_number =unique_value
    popt, pcov = curve_fit(get_photon_distribution_curve, photon_number,  relative_frequency, p0 = initial_guess)
    return popt, np.diag(pcov)

def get_photon_distribution_curveNVm(photon_number,readout_time, g0,g1,y1,y0):  
    if g0 < 0:
            g0 = 0
    if g1 < 0:
        g1 = 0
    tR = readout_time 
    poisspdf2 = scipy.stats.poisson(y1*tR)
    i = 0
    curve = []
    photon_number_list = list(range(photon_number))
    for i in range(len(photon_number_list)): 
        n = i
        def IntegNVm(t):
            poisspdf1 = scipy.stats.poisson(y1*t+y0*(tR-t))
            integ = g1*math.e**((g0-g1)*t-g0*tR)*poisspdf1.pmf(n)
            + math.sqrt(abs(g1*g0*t/(tR-t)))*math.e**((g0-g1)*t-g0*tR)*scipy.special.jv(1, 2*math.sqrt(abs(g1*g0*t*(tR-t))))* poisspdf1.pmf(n)
            return integ
        valNVm, err = scipy.integrate.quad(IntegNVm,0,tR)
        result = valNVm + math.e**(-g1*tR)*poisspdf2.pmf(n) 
        curve.append(result)
        i += 1
    return curve 

def get_curve_fit_NV0(readout_time,readout_power,unique_value, relative_frequency):
    tR = readout_time
    P = readout_power
    initial_guess = [10,100,10000,1000]
    def get_photon_distribution_curve(unique_value,g0,g1,y1,y0):
        poisspdf3 = scipy.stats.poisson(y0*tR)
        photon_number = unique_value
        i = 0
        curve = []
        for i in range(len(photon_number)): 
            n = photon_number[i]
            def IntegNV0(t):
                poisspdf4 = scipy.stats.poisson(y0*t+y1*(tR-t))
                integ = g0*math.e**((g0-g1)*t-g0*tR)*poisspdf4.pmf(n) + math.sqrt(abs(g1*g0*t/(tR-t)))*math.e**((g1-g0)*t-g1*tR)*scipy.special.jv(1, 2*math.sqrt(abs(g1*g0*t*(tR-t))))* poisspdf4.pmf(n)
                return integ

            valNV0, err = scipy.integrate.quad(IntegNV0,0,tR)
            result = valNV0 + math.e**(-g0*tR)*poisspdf3.pmf(n)
            curve.append(result)
            i += 1
        return curve 
    photon_number =unique_value
    popt, pcov = curve_fit(get_photon_distribution_curve, photon_number,  relative_frequency, p0 = initial_guess)
    print(np.diag(pcov))
    return popt, np.diag(pcov)

def get_photon_distribution_curveNV0(photon_number,readout_time, g0,g1,y1,y0):    
    if g0 < 0:
        g0 = 0
    if g1 < 0:
        g1 = 0
    tR = readout_time 
    poisspdf3 = scipy.stats.poisson(y0*tR)
    i = 0
    curve = []
    photon_number_list = list(range(photon_number))
    for i in range(len(photon_number_list)): 
        n = i
        def IntegNV0(t):
            poisspdf4 = scipy.stats.poisson(y0*t+y1*(tR-t))
            integ = g0*math.e**((g0-g1)*t-g0*tR)*poisspdf4.pmf(n) + math.sqrt(g1*g0*t/(tR-t))*math.e**((g1-g0)*t-g1*tR)*scipy.special.jv(1, 2*math.sqrt(g1*g0*t*(tR-t)))* poisspdf4.pmf(n)
            return integ

        valNV0, err = scipy.integrate.quad(IntegNV0,0,tR)
        result = valNV0 + math.e**(-g0*tR)*poisspdf3.pmf(n)
        curve.append(result)
        i += 1
    return curve    
#%% quick single poisson curve fit 
def get_sigle_poisson_distribution_fit(readout_time,readout_power,unique_value, relative_frequency):
    tR = readout_time
    number_of_photons = unique_value
    def PoissonDistribution(number_of_photons, F):
        poissonian =[]
        for i in range(len(number_of_photons)):
            n = number_of_photons[i]
            poissonian.append(((F*tR)**n) * (math.e ** (-F*tR)) /math.factorial(n))
        return poissonian
    popt, pcov = curve_fit(PoissonDistribution, number_of_photons,  relative_frequency)
    return popt, np.diag(pcov)

def get_single_poisson_distribution_curve(number_of_photons,readout_time, F):
    poissonian_curve =[]
    tR = readout_time
    for i in range(len(number_of_photons)):
        n = number_of_photons[i]
        poissonian_curve.append(((F*tR)**n) * (math.e ** (-F*tR)) /math.factorial(n))
    return poissonian_curve   

#%% quick double poisson curve fit 
def get_poisson_distribution_fit(readout_time,unique_value, relative_frequency):
    tR = readout_time
    number_of_photons = unique_value
    def PoissonDistribution(number_of_photons, a, b, numbla1, numbla2):
        #numbla1 and numbla2 represent the fluorescence rate 
        poissonian =[]
        for i in range(len(number_of_photons)):
            n = number_of_photons[i]
            poissonian.append((a*(numbla1*tR)**n) * (math.e ** (-numbla1*tR)) /math.factorial(n) + b*((numbla2*tR)**n) * (math.e ** (-numbla2*tR)) /math.factorial(n))
        return poissonian
    popt, pcov = curve_fit(PoissonDistribution, number_of_photons,  relative_frequency)
    return popt

def get_poisson_distribution_curve(number_of_photons,readout_time, a, b, numbla1, numbla2):
    poissonian_curve =[]
    tR = readout_time
    for i in range(len(number_of_photons)):
        n = number_of_photons[i]
        poissonian_curve.append((a*(numbla1*tR)**n) * (math.e ** (-numbla1*tR)) /math.factorial(n) + b*((numbla2*tR)**n) * (math.e ** (-numbla2*tR)) /math.factorial(n))
    return poissonian_curve 
#%% gaussian fit
def get_gaussian_distribution_fit(readout_time,readout_power,unique_value, relative_frequency):
    tR = readout_time
    number_of_photons = unique_value
    average_photon_number = 0
    for i in range(len(unique_value)):
        average_photon_number += relative_frequency[i] * unique_value[i]
    variance = 0 
    for i in range(len(unique_value)):
        variance += relative_frequency[i] * (unique_value[i])**2
    variance = variance - average_photon_number**2
    sigma_guess = math.sqrt(variance)
    def GaussianDistribution(number_of_photons,u,sigma, offset, coeff):
        gaussian = []
        for i in range(len(number_of_photons)):
            n = number_of_photons[i]
            gaussian.append(offset + coeff * math.e ** (-0.5*((n - u)/sigma)**2))
        return gaussian
    popt, pcov = curve_fit(GaussianDistribution,number_of_photons,relative_frequency,p0= [average_photon_number,sigma_guess,0,0.1])
    return popt

def get_gaussian_distribution_curve(number_of_photons,readout_time,u, sigma, offset, coeff):
    gaussian =[]
    for i in range(len(number_of_photons)):
        n = number_of_photons[i]
        gaussian.append(offset + coeff * math.e**(-0.5*((n - u)/sigma)**2))
    return gaussian

#%% photon counts monitoring module 
    
def get_time_axe(sequence_time, readout_time, photon_number_list):
    time_data = []
    for i in range(1,len(photon_number_list)+1):
        time_data.append(sequence_time*i)
    return time_data

def get_photon_counts(readout_time, photon_number_list):
    photon_counts = np.array(photon_number_list)/np.array(readout_time)
    return photon_counts.tolist()
        
        
        
                