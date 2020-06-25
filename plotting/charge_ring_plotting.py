# -*- coding: utf-8 -*-
"""
Created on Wed Jun 24 09:05:07 2020

@author: agardill
"""

import matplotlib.pyplot as plt 
import numpy
import utils.tool_belt as tool_belt
from scipy.optimize import curve_fit
from scipy.signal import find_peaks

# %%

def gaussian(r, constrast, sigma, center, offset):
    return offset+ constrast * numpy.exp(-((r-center)**2) / (2 * (sigma**2)))

def double_gaussian_dip(freq, low_constrast, low_sigma, low_center, low_offset,
                        high_constrast, high_sigma, high_center, high_offset):
    low_gauss = gaussian(freq, low_constrast, low_sigma, low_center, low_offset)
    high_gauss = gaussian(freq, high_constrast, high_sigma, high_center, high_offset)
    return low_gauss + high_gauss

# %%
    
def r_vs_power_plot(nv_sig, ring_radius_list, ring_err_list, power_list, 
                    power_err_list, sub_folder, 
                    img_range, num_steps, green_pulse_time, readout):
    power_fig, ax = plt.subplots(1,1, figsize = (8, 8))
    ax.errorbar(power_list, ring_radius_list, xerr = power_err_list, yerr = ring_err_list, fmt = 'o', label = '1 s green pulse')
    ax.set_xlabel('Green optical power (mW)')
    ax.set_ylabel('Charge ring radius (um)')
    ax.legend()
            
    timestamp = tool_belt.get_time_stamp()
    
    # save this dile 
    rawData = {'timestamp': timestamp,
               'nv_sig': nv_sig,
               'nv_sig-units': tool_belt.get_nv_sig_units(),
               'image_range': img_range,
               'image_range-units': 'V',
               'num_steps': num_steps,
               'green_pulse_time': green_pulse_time,
               'green_pulse_time-units': 'ns',
               'readout': readout,
               'readout-units': 'ns',
               'power_list': power_list,
               'power_list-units': 'mW',
               'power_err_list': power_err_list.tolist(),
               'power_err_list-units': 'mW',
               'ring_radius_list':ring_radius_list,
               'ring_radius_list-units': 'um',
               'ring_err_list': ring_err_list,
               'ring_err_list-units': 'um'}
    
    filePath = tool_belt.get_file_path("image_sample", timestamp, nv_sig['name'], subfolder = sub_folder)
    tool_belt.save_raw_data(rawData, filePath + '_radius_vs_power')
    
    tool_belt.save_figure(power_fig, filePath + '_radius_vs_power')
# %%

def radial_distrbution_power(folder_name, sub_folder):
    # create a file list of the files to analyze
    file_list  = tool_belt.get_file_list(folder_name, '.txt')
    # create lists to fill with data
    power_list = []
    ring_radius_list = []
    ring_err_list = []
    
    for file in file_list:
        try:
            data = tool_belt.get_raw_data(folder_name, file[:-4])
            # Get info from file
            timestamp = data['timestamp']
            nv_sig = data['nv_sig']
            coords = nv_sig['coords']
            x_voltages = data['x_voltages']
            y_voltages = data['y_voltages']
            num_steps = data['num_steps']
            img_range= data['image_range']
            dif_img_array = numpy.array(data['dif_img_array'])
            green_pulse_time = data['green_pulse_time']
            readout = data['readout']
            opt_volt = data['green_optical_voltage']
            opt_power = data['green_opt_power']
            
            # Initial calculations
            x_coord = coords[0]          
            y_coord = coords[1]
            half_x_range = img_range / 2
            x_high = x_coord + half_x_range

            pixel_size = x_voltages[1] - x_voltages[0]
            half_pixel_size = pixel_size / 2
            
            # List to hold the values of each pixel within the ring
            counts_r = []
            # New 2D array to put the radial values of each pixel
            r_array = numpy.empty((num_steps, num_steps))
            
            # Calculate the radial distance from each point to center
            for i in range(num_steps):
                x_pos = x_voltages[i] - x_coord
                for j in range(num_steps):
                    y_pos = y_voltages[j]  - y_coord
                    r = numpy.sqrt(x_pos**2 + y_pos**2)
                    r_array[i][j] = r
            
            # define bound on each ring radius, which will be one pixel in size
            low_r = 0
            high_r = pixel_size
            
            # step throguh the radial ranges for each ring, add pixel within ring to list
            while high_r <= (x_high + half_pixel_size):
                ring_counts = []
                for i in range(num_steps):
                    for j in range(num_steps): 
                        radius = r_array[i][j]
                        if radius >= low_r and radius < high_r:
                            ring_counts.append(dif_img_array[i][j])
                # average the counts of all counts in a ring
                counts_r.append(numpy.average(ring_counts))
                # advance the radial bounds
                low_r = high_r
                high_r = high_r + pixel_size
            
            # define the radial values as center values of pizels along x, convert to um
            radii = numpy.array(x_voltages[int(num_steps/2):])*35
            # plot
            fig, ax = plt.subplots(1,1, figsize = (8, 8))
            ax.plot(radii, counts_r)
            ax.set_xlabel('Radius (um)')
            ax.set_ylabel('Avg counts around ring (kcps)')
            ax.set_title('{} s, {} mW green pulse'.format(green_pulse_time/10**9, opt_power))
            
            # try to fit the radial distribution to a double gaussian(work in prog)    
            try:
                contrast_low = 500
                sigma_low = 5
                center_low = -5
                offset_low = 100
                contrast_high = 300
                sigma_high = 5
                center_high = 20
                offset_high = 100            
                guess_params = (contrast_low, sigma_low, center_low, offset_low,
                                contrast_high, sigma_high, center_high, offset_high)
                
                popt, pcov = curve_fit(double_gaussian_dip, radii[1:], counts_r[1:], p0=guess_params)
                radii_linspace = numpy.linspace(radii[0], radii[-1], 1000)
                
                ax.plot(radii_linspace, double_gaussian_dip(radii_linspace, *popt))
                print('fit succeeded')
                
                power_list.append(opt_power)
                ring_radius_list.append(popt[6])
                ring_err_list.append(pcov[6][6])
                
            except Exception:
                print('fit failed' )
                
            # save data from this file
            rawData = {'timestamp': timestamp,
                       'nv_sig': nv_sig,
                       'nv_sig-units': tool_belt.get_nv_sig_units(),
                       'image_range': img_range,
                       'image_range-units': 'V',
                       'num_steps': num_steps,
                       'green_pulse_time': green_pulse_time,
                       'green_pulse_time-units': 'ns',
                       'green_optical_voltage': opt_volt,
                       'green_optical_voltage-units': 'V',
                       'green_opt_power': opt_power,
                       'green_opt_power-units': 'mW',
                       'readout': readout,
                       'readout-units': 'ns',
                       'x_voltages': x_voltages,
                       'x_voltages-units': 'V',
                       'y_voltages': y_voltages,
                       'y_voltages-units': 'V',
                       'ring_radius_list': radii.tolist(),
                       'ring_radius_list-units': 'V',
                       'counts_r': counts_r,
                       'counts_r-units': 'kcps'}
            
            filePath = tool_belt.get_file_path("image_sample", timestamp, nv_sig['name'], subfolder = sub_folder)
            tool_belt.save_raw_data(rawData, filePath + '_radius')
            
            tool_belt.save_figure(fig, filePath + '_radius')
        except Exception:
            continue
    
    # Save a list of the estimated error in power measurement (0.02 mW)
    power_err_list = numpy.ones(len(power_list))
    power_err_list = power_err_list[:]*0.02
    
    return ring_radius_list, ring_err_list, power_list, power_err_list, \
                nv_sig, img_range, num_steps, green_pulse_time, readout
    
# %% 
if __name__ == '__main__':
    parent_folder = "image_sample/branch_Spin_to_charge/2020_06/"
    
#    sub_folder = "hopper_50s_power"
#    sub_folder = "hopper_10s_power"
    sub_folder = "hopper_1s_power"
    folder_name = parent_folder + sub_folder
    
    ret_vals = radial_distrbution_power(folder_name, sub_folder)
    ring_radius_list, ring_err_list, power_list, power_err_list, \
        nv_sig, img_range, num_steps, green_pulse_time, readout = ret_vals
    
    r_vs_power_plot(nv_sig, ring_radius_list, ring_err_list, power_list, 
                    power_err_list, sub_folder, 
                    img_range, num_steps, green_pulse_time, readout)
    print(ring_radius_list, ring_err_list)

    # %% Manual data fitting
    # Picked by eye on original scans 
#    powers = [0.04, 0.06, 0.2, 0.28, 0.44, 0.55, 0.63, 0.75, 0.89, 0.98, 1.10, 1.22] # mW
#    power_err = [0.1, 0.01, 0.05, 0.05, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.01, 0.02] # mW
#    
#    radius_1 = numpy.array([0, 0.08, 0.16, 0.21, 0.25, 0.28, 0.32, 0.32, 0.33, 0.35, 0.37, 0.40]) # V 
#    radius_1_err = numpy.array([0, 0.07, 0.08, 0.06, 0.03, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.04]) # V
#    radius_10 = numpy.array([0, 0.09, 0.22, 0.27, 0.31, 0.33, 0.37, 0.36, 0.39, 0.41, 0.42, 0.43]) # V
#    radius_10_err = numpy.array([0, 0.08, 0.05, 0.03, 0.02, 0.03, 0.02, 0.02, 0.01, 0.01, 0.01, 0.01]) # V
#    radius_50 = numpy.array([0.04, 0.08, 0.26, 0.3, 0.35, 0.39, 0.41, 0.45, 0.42, 0.43, 0.46, 0.50]) # V
#    radius_50_err = numpy.array([0.02, 0.04, 0.03, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.01]) # V
    
    # Determined by eye from radial plots    
    powers = [0.02, 0.04, 0.2, 0.25, 0.44, 0.55, 0.63, 0.75, 0.89, 0.98]   # mW
    power_err =   numpy.ones(len(powers))
    power_err = power_err[:]*0.02
    
    radius_1 = [0.1, 1.5, 4, 7, 11, 13.5, 14.5, 14.0, 15.2, 15.0] # um
    radius_1_err = [0.1, 1, 3, 5, 2, 1, 0.5, 0.5, 0.5, 0.5 ]
    radius_10 = [0.5, 2.5, 8, 9.6, 12.8, 14.7, 15.3, 16.7, 17.3, 17.7] # um
    radius_10_err = numpy.ones(len(radius_10))
    radius_10_err = radius_10_err[:]*0.5 # um
    radius_50 = [1.5, 3.5, 10.5, 13.6, 15.4, 16.5, 17.4, 19.3, 18.4, 19.4] # um
    radius_50_err =  radius_1_err

    fig, ax = plt.subplots(1,1, figsize = (8, 8))
    ax.errorbar(powers, radius_1, xerr = power_err, yerr = radius_1_err, fmt = 'o', label = '1 s green pulse')
    ax.errorbar(powers, radius_10, xerr = power_err, yerr = radius_10_err, fmt = 'o',  label = '10 s green pulse')
    ax.errorbar(powers, radius_50, xerr = power_err, yerr = radius_50_err, fmt = 'o',  label = '50 s green pulse')
    ax.set_xlabel('Green optical power (mW)')
    ax.set_ylabel('Charge ring radius (um)')
    ax.legend()

