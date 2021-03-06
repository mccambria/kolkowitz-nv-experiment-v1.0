# -*- coding: utf-8 -*-
"""
Created on Tue Mar  3 10:17:30 2020

Plot spectra data from a json file with the wavelengths and counts

(note, the function to specify range doesn't set the upper bound properly...
Might be with multiple spectra stitched together, the step sizes are slightly 
different)

@author: agardill
"""

import utils.tool_belt as tool_belt
from scipy.optimize import curve_fit
import numpy
import matplotlib.pyplot as plt

# %%

data_path = 'C:/Users/Public/Documents/Jobin Yvon/SpectraData'

folder = '5_nm_Er_graphene/2020_03_02'

#folder = '5_nm_Er_NO_graphene_Y_ig'

# %%

def wavelength_range_calc(wavelength_range, wavelength_list):
    wvlngth_range_strt = wavelength_range[0]
    wvlngth_range_end = wavelength_range[1]
    
    wvlngth_list_strt = wavelength_list[0]
    wvlngth_list_end = wavelength_list[-1]
    step_size = wavelength_list[1] - wavelength_list[0]
    
    # Try to calculate the indices for plotting, if they are given
    try: 
        start_index = int( (wvlngth_range_strt - wvlngth_list_strt) /  step_size )
    except Exception:
        pass
    try: 
        end_index = -(int((wvlngth_list_end - wvlngth_range_end) /  step_size) + 1)
    except Exception:
        pass
            
    
    #If both ends of range are specified
    if wvlngth_range_strt and wvlngth_range_end:
        
        #However, if the range is outside the actual data, just plot all data
        # Or if one of the bounds is outside the range, do not include that range
        if wvlngth_range_strt < wvlngth_list_strt and \
                                    wvlngth_range_end > wvlngth_list_end:
            print('Wavelength range outside of data range. Plotting full range of data')
            plot_strt = 0
            plot_end = -1
        elif wvlngth_range_strt < wvlngth_list_strt and \
            wvlngth_range_end <= wvlngth_list_end:
                
            print('Requested lower bound of wavelength range outside of data range. Starting data at lowest wavelength')
            plot_strt = 0
            plot_end = end_index
            
        elif wvlngth_range_strt >= wvlngth_list_strt and \
            wvlngth_range_end > wvlngth_list_end:
                
            print('Requested upper bound of wavelength range outside of data range. Plotting up to highest wavelength')
            plot_strt = start_index
            plot_end = -1
        else:
            #If they are given, then plot the requested range
            plot_strt = start_index
            plot_end = end_index
            
    # If the lower bound is given, but not the upper bound
    elif wvlngth_range_strt and not wvlngth_range_end:
        plot_end = -1
        
        if wvlngth_range_strt < wvlngth_list_strt:
            print('Requested lower bound of wavelength range outside of data range. Plotting full range of data')
            plot_strt = 0
        else:
            plot_strt = start_index
            
    # If the upper bound is given, but not the lower bound
    elif wvlngth_range_end and not wvlngth_range_strt:
        plot_strt = 0
        
        if wvlngth_range_end > wvlngth_list_end:
            print('Requested upper bound of wavelength range outside of data range. Plotting full range of data')
            plot_end = -1
        else:
            plot_end = end_index
    # Lastly, if no range is given
    elif not wvlngth_range_end and not wvlngth_range_strt:
       plot_strt = 0 
       plot_end = -1
        
    return plot_strt, plot_end

# %%
    
def plot_spectra(file, wavelength_range, vertical_range, plot_title):
    data = tool_belt.get_raw_data(folder, file,
                 nvdata_dir=data_path)
    wavelengths = numpy.array(data['wavelengths'])
    counts = numpy.array(data['counts'])
    
    background= counts[0]
    
    plot_strt_ind, plot_end_ind  = wavelength_range_calc(wavelength_range, wavelengths)
    

    fig, ax= plt.subplots(1, 1, figsize=(10, 8))
    ax.plot(wavelengths[plot_strt_ind : plot_end_ind], counts[plot_strt_ind : plot_end_ind])
    ax.set_xlabel('Wavelength')
    ax.set_ylabel('Counts')
    ax.set_title(plot_title)
    ax.set_ylim(vertical_range)

        
        
        
    
# %%

# MEasurements 3/2
    
file_p03 = 'p0.2V'
file_m10 = 'm1.0V' 
file_m15 = 'm1.5V'
file_m20 = 'm2.0V'
file_m23 = 'm2.3V'

file_shortpass = 'Shortpass_filter'
file_longpass = 'Longpass filter'

file_ionic_gel = 'Ionic_gel'
file_er_surface = 'Erbium'
file_in_oxide = 'In_oxide'

file_no_graphene_no_IG = '550'

if __name__ == '__main__':
    
    
   
#    plot_spectra(file_ionic_gel, [None, None], [0, 9350],'Focused on Ionic Gel')
#    plot_spectra(file_in_oxide, [None, None], [0, 9350],'Focused on below Oxide Surface')
    
 # %%
    data_graphene = tool_belt.get_raw_data('5_nm_Er_graphene/2020_03_02', file_m10,
                 nvdata_dir=data_path)
    wavelengths_graphene = numpy.array(data_graphene['wavelengths'])
    counts_graphene = numpy.array(data_graphene['counts'])
    
    data_no_graphene = tool_belt.get_raw_data('5_nm_Er_NO_graphene_NO_ig', file_no_graphene_no_IG,
                 nvdata_dir=data_path)
    counts_no_graphene = numpy.array(data_no_graphene['counts'])
    wavelengths_no_graphene = numpy.array(data_no_graphene['wavelengths'])
        
    plot_strt_ind_g, plot_end_ind_g  = wavelength_range_calc([545,570], wavelengths_graphene)
    plot_strt_ind_ng, plot_end_ind_ng  = wavelength_range_calc([545,570], wavelengths_no_graphene)
    

    fig, ax= plt.subplots(1, 1, figsize=(10, 8))    
    ax.plot(wavelengths_no_graphene[plot_strt_ind_ng : plot_end_ind_ng], counts_no_graphene[plot_strt_ind_ng : plot_end_ind_ng], label = 'Er without graphene')

    ax.plot(wavelengths_graphene[plot_strt_ind_g : plot_end_ind_g], counts_graphene[plot_strt_ind_g : plot_end_ind_g] - 750, label = 'Er with graphene (gate voltage = -1.0V)')
    ax.set_xlabel('Wavelength (nm)')
    ax.set_ylabel('Counts')
    ax.set_title('Spectra around 550 nm with and without graphene')
    ax.set_ylim([0, 2000])
    ax.legend()

    
    
    