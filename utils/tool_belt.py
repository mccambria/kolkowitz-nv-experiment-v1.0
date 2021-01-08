# -*- coding: utf-8 -*-
"""
This file contains functions, classes, and other objects that are useful
in a variety of contexts. Since they are expected to be used in many
files, I put them all in one place so that they don't have to be redefined
in each file.

Created on Fri Nov 23 14:57:08 2018

@author: mccambria
"""


# %% Imports


import matplotlib.pyplot as plt
import threading
import os
import datetime
import numpy
from numpy import exp
import json
import time
import labrad
from tkinter import Tk
from tkinter import filedialog
from git import Repo
from pathlib import Path
from pathlib import PurePath
from enum import Enum, auto
import socket


# %% Constants


class States(Enum):
    """Do not update this without also updating get_state_signal_generator!"""
    LOW = auto()
    ZERO = auto()
    HIGH = auto()
    
def get_signal_generator_name(state):
    if state.value == States.LOW.value:
        signal_generator_name = 'signal_generator_tsg4104a'
    elif state.value == States.HIGH.value:
        signal_generator_name = 'signal_generator_bnc835'
    return signal_generator_name
    
def get_signal_generator_cxn(cxn, state):
    signal_generator_name = get_signal_generator_name(state)
    signal_generator_cxn = eval('cxn.{}'.format(signal_generator_name))
    return signal_generator_cxn


# %% xyz sets


def set_xyz(cxn, coords):
    cxn.galvo.write(coords[0], coords[1])
    cxn.objective_piezo.write(coords[2])
    # Force some delay before proceeding to account 
    # for the effective write time
    time.sleep(0.002)


def set_xyz_zero(cxn):
    cxn.galvo.write(0.0, 0.0)
    cxn.objective_piezo.write(5.0)
    # Force some delay before proceeding to account 
    # for the effective write time
    time.sleep(0.001)


def set_xyz_on_nv(cxn, nv_sig):
    coords = nv_sig['coords']
    cxn.galvo.write(coords[0], coords[1])
    cxn.objective_piezo.write(coords[2])
    # Force some delay before proceeding to account 
    # for the effective write time
    time.sleep(0.001)
    

# %% Pulse Streamer utils


def encode_seq_args(seq_args):
    return json.dumps(seq_args)

def decode_seq_args(seq_args_string):
    return json.loads(seq_args_string)

def get_pulse_streamer_wiring(cxn):
    cxn.registry.cd(['', 'Config', 'Wiring', 'Pulser'])
    sub_folders, keys = cxn.registry.dir()
    if keys == []:
        return {}
    p = cxn.registry.packet()
    for key in keys:
        p.get(key, key=key)  # Return as a dictionary
    wiring = p.send()
    pulse_streamer_wiring = {}
    for key in keys:
        pulse_streamer_wiring[key] = wiring[key]
    return pulse_streamer_wiring

def get_time_tagger_wiring(cxn):
    cxn.registry.cd(['', 'Config', 'Wiring', 'Tagger'])
    sub_folders, keys = cxn.registry.dir()
    if keys == []:
        return {}
    p = cxn.registry.packet()
    for key in keys:
        p.get(key, key=key)  # Return as a dictionary
    wiring = p.send()
    pulse_streamer_wiring = {}
    for key in keys:
        pulse_streamer_wiring[key] = wiring[key]
    return pulse_streamer_wiring

# %% adp_tagger utils
    
def decode_time_tags(ret_vals_string):
    ret_vals = ret_vals_string.split('.')
    new_tags = []
    new_channels = []
    if ret_vals[0] != '':
        for val in ret_vals:
            split_val = val.split(',')
            new_tags.append(split_val[0])
            new_channels.append(int(split_val[1]))
        new_tags = numpy.array(new_tags, dtype=numpy.int64)    
    return new_tags, new_channels

# %% Matplotlib plotting utils


def create_image_figure(imgArray, imgExtent, clickHandler=None, title = None, color_bar_label = 'Counts', min_value=None):
    """
    Creates a figure containing a single grayscale image and a colorbar.

    Params:
        imgArray: numpy.ndarray
            Rectangular numpy array containing the image data.
            Just zeros if you're going to be writing the image live.
        imgExtent: list(float)
            The extent of the image in the form [left, right, bottom, top]
        clickHandler: function
            Function that fires on clicking in the image

    Returns:
        matplotlib.figure.Figure
    """

    # Tell matplotlib to generate a figure with just one plot in it
    fig, ax = plt.subplots()

    # Tell the axes to show a grayscale image
    img = ax.imshow(imgArray, cmap='inferno',
                    extent=tuple(imgExtent), vmin = min_value)

#    if min_value == None:
#        img.autoscale()

    # Add a colorbar
    clb = plt.colorbar(img)
    clb.set_label(color_bar_label, rotation=270)
#    clb.set_label('kcounts/sec', rotation=270)
    
    # Label axes
    plt.xlabel('V')
    plt.ylabel('V')
    if title:
        plt.title(title)

    # Wire up the click handler to print the coordinates
    if clickHandler is not None:
        fig.canvas.mpl_connect('button_press_event', clickHandler)

    # Draw the canvas and flush the events to the backend
    fig.canvas.draw()
    plt.tight_layout()
    fig.canvas.flush_events()

    return fig


def update_image_figure(fig, imgArray):
    """
    Update the image with the passed image array and redraw the figure.
    Intended to update figures created by create_image_figure.

    The implementation below isn't nearly the fastest way of doing this, but
    it's the easiest and it makes a perfect figure every time (I've found
    that the various update methods accumulate undesirable deviations from
    what is produced by this brute force method).

    Params:
        fig: matplotlib.figure.Figure
            The figure containing the image to update
        imgArray: numpy.ndarray
            The new image data
    """

    # Get the image - Assume it's the first image in the first axes
    axes = fig.get_axes()
    ax = axes[0]
    images = ax.get_images()
    img = images[0]

    # Set the data for the image to display
    img.set_data(imgArray)

    # Check if we should clip or autoscale
    clipAtThousand = False
    if clipAtThousand:
        if numpy.all(numpy.isnan(imgArray)):
            imgMax = 0  # No data yet
        else:
            imgMax = numpy.nanmax(imgArray)
        if imgMax > 1000:
            img.set_clim(None, 1000)
        else:
            img.autoscale()
    else:
        img.autoscale()

    # Redraw the canvas and flush the changes to the backend
    fig.canvas.draw()
    fig.canvas.flush_events()


def create_line_plot_figure(vals, xVals=None):
    """
    Creates a figure containing a single line plot

    Params:
        vals: numpy.ndarray
            1D numpy array containing the values to plot
        xVals: numpy.ndarray
            1D numpy array with the x values to plot against
            Default is just the index of the value in vals

    Returns:
        matplotlib.figure.Figure
    """

    # Tell matplotlib to generate a figure with just one plot in it
    fig, ax = plt.subplots()

    if xVals is not None:
        ax.plot(xVals, vals)
        ax.set_xlim(xVals[0], xVals[len(xVals) - 1])
    else:
        ax.plot(vals)
        ax.set_xlim(0, len(vals)-1)

    # Draw the canvas and flush the events to the backend
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig


def create_line_plots_figure(vals, xVals=None):
    """
    Creates a figure containing a single line plot

    Params:
        vals: tuple(numpy.ndarray)
            1D numpy array containing the values to plot
        xVals: numpy.ndarray
            1D numpy array with the x values to plot against
            Default is just the index of the value in vals

    Returns:
        matplotlib.figure.Figure
    """

    # Tell matplotlib to generate a figure with len(vals) plots
    fig, ax = plt.subplots(len(vals))

    if xVals is not None:
        ax.plot(xVals, vals)
        ax.set_xlim(xVals[0], xVals[len(xVals) - 1])
    else:
        ax.plot(vals)
        ax.set_xlim(0, len(vals) - 1)

    # Draw the canvas and flush the events to the backend
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig


def update_line_plot_figure(fig, vals):
    """
    Updates a figure created by create_line_plot_figure

    Params:
        vals: numpy.ndarray
            1D numpy array containing the values to plot
    """

    # Get the line - Assume it's the first line in the first axes
    axes = fig.get_axes()
    ax = axes[0]
    lines = ax.get_lines()
    line = lines[0]

    # Set the data for the line to display and rescale
    line.set_ydata(vals)
    ax.relim()
    ax.autoscale_view(scalex=False)

    # Redraw the canvas and flush the changes to the backend
    fig.canvas.draw()
    fig.canvas.flush_events()


# %% Math functions

def get_pi_pulse_dur(rabi_period):
    return round(rabi_period / 2)
    

def get_pi_on_2_pulse_dur(rabi_period):
    return round(rabi_period / 4)


def gaussian(x, *params):
    """
    Calculates the value of a gaussian for the given input and parameters

    Params:
        x: float
            Input value
        params: tuple
            The parameters that define the Gaussian
            0: coefficient that defines the peak height
            1: mean, defines the center of the Gaussian
            2: standard deviation, defines the width of the Gaussian
            3: constant y value to account for background
    """

    coeff, mean, stdev, offset = params
    var = stdev**2  # variance
    centDist = x-mean  # distance from the center
    return offset + coeff**2*numpy.exp(-(centDist**2)/(2*var))


def sinexp(t, offset, amp, freq, decay):
    two_pi = 2*numpy.pi
    half_pi = numpy.pi / 2
    return offset + (amp * numpy.sin((two_pi * freq * t) + half_pi)) * exp(-decay**2 * t)

# This cosexp includes a phase that will be 0 in the ideal case.
#def cosexp(t, offset, amp, freq, phase, decay):
#    two_pi = 2*numpy.pi
#    return offset + (numpy.exp(-t / abs(decay)) * abs(amp) * numpy.cos((two_pi * freq * t) + phase))


def cosexp(t, offset, amp, freq, decay):
    two_pi = 2*numpy.pi
    return offset + (numpy.exp(-t / abs(decay)) * abs(amp) * numpy.cos((two_pi * freq * t)))

def cosexp_scc(t, offset, amp, freq, decay):
    two_pi = 2*numpy.pi
    return offset - (numpy.exp(-t / abs(decay)) * abs(amp) * numpy.cos((two_pi * freq * t)))

def cosine_sum(t, offset, decay, amp_1, freq_1, amp_2, freq_2, amp_3, freq_3):
    two_pi = 2*numpy.pi
    
    return offset + numpy.exp(-t / abs(decay)) * (
                amp_1 * numpy.cos(two_pi * freq_1 * t) +
                amp_2 * numpy.cos(two_pi * freq_2 * t) +
                amp_3 * numpy.cos(two_pi * freq_3 * t))
    
def calc_snr(sig_count, ref_count):
    '''
    Take a list of signal and reference counts, and take their average, then 
    calculate a snr.
    inputs:
        sig_count = list
        ref_counts = list
    outputs:
        snr = list
    '''    
    
    sig_count_avg = numpy.average(sig_count)
    ref_count_avg = numpy.average(ref_count)
    dif = sig_count_avg - ref_count_avg
    noise = numpy.sqrt(ref_count_avg)
    snr = dif / noise
    
    return snr


# %% LabRAD utils


def get_shared_parameters_dict(cxn):
    """Get the shared parameters from the registry. These parameters are not
    specific to any experiment, but are instead used across experiments. They
    may depend on the current alignment (eg aom_delay) or they may just be
    parameters that are referenced by many sequences (eg polarization_dur).
    Generally, they should need to be updated infrequently, unlike the
    shared parameters defined in cfm_control_panel, which change more
    frequently (eg apd_indices).
    
    We currently have the parameters listed below. All durations (ending in
    _delay or _dur) have units of ns.
        airy_radius: Standard deviation of the Gaussian approximation to
            the Airy disk in nm
        polarization_dur: Duration to illuminate for polarization
        post_polarization_wait_dur: Duration to wait after polarization to
            allow the NV metastable state to decay
        pre_readout_wait_dur: Duration to wait before readout - functionally
            I think this is just for symmetry with post_polarization_wait_dur
        532_aom_delay: Delay between signal to the 532 nm laser AOM and the
            AOM actually opening
        uwave_delay: Delay between signal to uwave switch and the switch
            actually opening - should probably be different for different
            signal generators...
        pulsed_readout_dur: Readout duration if we're looking to determine
            the state directly dorm fluorescence
        continuous_readout_dur: Readout duration if we're just looking to
            see how bright something is
        galvo_delay: Delay between signal to galvo and the galvo settling to
            its new position
        galvo_nm_per_volt: Conversion factor between galvo voltage and xy
            position
        piezo_delay: Delay between signal to objective piezo and the piezo
            settling to its new position
        piezo_nm_per_volt: Conversion factor between objective piezo voltage
            and z position
    """

    # Get what we need out of the registry
    cxn.registry.cd(['', 'SharedParameters'])
    sub_folders, keys = cxn.registry.dir()
    if keys == []:
        return {}

    p = cxn.registry.packet()
    for key in keys:
        p.get(key)
    vals = p.send()['get']

    reg_dict = {}
    for ind in range(len(keys)):
        key = keys[ind]
        val = vals[ind]
        reg_dict[key] = val

    return reg_dict


# %% Open utils


def ask_open_file(file_path):
    """
    Open a file by selecting it through a file window. File window usually
    opens behind Spyder, may need to minimize Spyder to see file number

    file_path: input the file path to the folder of the data, starting after
    the Kolkowitz Lab Group folder

    Returns:
        string: file name of the file to use in program
    """
    # Prompt the user to select a file
    print('Select file \n...')

    root = Tk()
    root.withdraw()
    root.focus_force()
    directory = str("E:/Shared drives/Kolkowitz Lab Group/" + file_path)
    file_name = filedialog.askopenfilename(initialdir = directory,
                                          title = 'choose file to replot', filetypes = (("svg files","*.svg"),("all files","*.*")) )
    return file_name

def get_file_list(path_from_nvdata, file_ends_with,
                 data_dir='E:/Shared drives/Kolkowitz Lab Group/nvdata'):
    '''
    Creates a list of all the files in the folder for one experiment, based on
    the ending file name
    '''
    
    data_dir = Path(data_dir)
    file_path = data_dir / path_from_nvdata 
    
    file_list = []
    
    for file in os.listdir(file_path):
        if file.endswith(file_ends_with):
            file_list.append(file)

    return file_list


def get_raw_data(path_from_nvdata, file_name,
                 nvdata_dir='E:/Shared drives/Kolkowitz Lab Group/nvdata'):
    """Returns a dictionary containing the json object from the specified
    raw data file.
    """

    data_dir = PurePath(nvdata_dir, path_from_nvdata)
    file_name_ext = '{}.txt'.format(file_name)
    file_path = data_dir / file_name_ext

    with open(file_path) as file:
        return json.load(file)
    

# %%  Save utils


def get_branch_name():
    """Return the name of the active branch of kolkowitz-nv-experiment-v1.0"""
    home_to_repo = Path('Documents/GitHub/kolkowitz-nv-experiment-v1.0')
    repo_path = Path.home() / home_to_repo
    repo = Repo(repo_path)
    return repo.active_branch.name


def get_time_stamp():
    """
    Get a formatted timestamp for file names and metadata.

    Returns:
        string: <year>-<month>-<day>_<hour>-<minute>-<second>
    """

    timestamp = str(datetime.datetime.now())
    timestamp = timestamp.split('.')[0]  # Keep up to seconds
    timestamp = timestamp.replace(':', '_')  # Replace colon with dash
    timestamp = timestamp.replace('-', '_')  # Replace dash with underscore
    timestamp = timestamp.replace(' ', '-')  # Replace space with dash
    return timestamp


def get_folder_dir(source_name, subfolder):

    source_name = os.path.basename(source_name)
    source_name = os.path.splitext(source_name)[0]

    branch_name = get_branch_name()
    pc_name = socket.gethostname()

#    # Check where we should save to
#    if branch_name == 'master':
#        # master should save without a branch sub-folder
#        joined_path = os.path.join('E:/Shared drives/Kolkowitz Lab Group/nvdata',
#                                   source_name)
#    else:
#        # Otherwise we want a branch sub-folder so that we know this data was
#        # produced by code that's under development
#        joined_path = os.path.join('E:/Shared drives/Kolkowitz Lab Group/nvdata',
#                                   source_name,
#                                   'branch_{}'.format(branch_name))
    
    joined_path = os.path.join('E:/Shared drives/Kolkowitz Lab Group/nvdata',
                               'pc_{}'.format(pc_name),
                               'branch_{}'.format(branch_name),
                               source_name)
    
    if subfolder is not None:
        joined_path = os.path.join(joined_path, subfolder)

    folderDir = os.path.abspath(joined_path)

    # Make the required directory if it doesn't exist already
    if not os.path.isdir(folderDir):
        os.makedirs(folderDir)

    return folderDir

def get_data_path():
    return Path('E:/Shared drives/Kolkowitz Lab Group/nvdata')

def get_file_path(source_name, time_stamp='', name='', subfolder=None):
    """
    Get the file path to save to. This will be in a subdirectory of nvdata.

    Params:
        source_name: string
            Source file name - alternatively, __file__ of the caller which will
            be parsed to get the name of the subdirectory we will write to
        time_stamp: string
            Formatted timestamp to include in the file name
        name: string
            The file names consist of <timestamp>_<name>.<ext>
            Ext is supplied by the save functions
        subfolder: string
            Subfolder to save to under file name
    """

    # Set up the file name
    if (time_stamp != '') and (name != ''):
        fileName = '{}-{}'.format(time_stamp, name)
        #locate the subfolder that matches the month and year when the data is taken
        date_folder_name = '_'.join(time_stamp.split('_')[0:2])
    elif (time_stamp == '') and (name != ''):
        fileName = name
    elif (time_stamp != '') and (name == ''):
        fileName = '{}-{}'.format(time_stamp, 'untitled')
        date_folder_name = '_'.join(time_stamp.split('_')[0:2])
    else:
        fileName = '{}-{}'.format(get_time_stamp(), 'untitled')
    
    # Create the subfolder combined name, if needed
    if (subfolder != None) and (date_folder_name != None):
        subfolder_name = str(date_folder_name + '/' + subfolder)
    elif (subfolder == None) and (date_folder_name != None):
        subfolder_name = date_folder_name
    else:
        subfolder_name = None
        
    
    folderDir = get_folder_dir(source_name, subfolder_name)

    fileDir = os.path.abspath(os.path.join(folderDir, fileName))

    return fileDir

#def get_file_path(source_name, time_stamp='', name='', subfolder=None):
#    """
#    Get the file path to save to. This will be in a subdirectory of nvdata.
#
#    Params:
#        source_name: string
#            Source file name - alternatively, __file__ of the caller which will
#            be parsed to get the name of the subdirectory we will write to
#        time_stamp: string
#            Formatted timestamp to include in the file name
#        name: string
#            The file names consist of <timestamp>_<name>.<ext>
#            Ext is supplied by the save functions
#        subfolder: string
#            Subfolder to save to under file name
#    """
#
#    # Set up the file name
#    if (time_stamp != '') and (name != ''):
#        fileName = '{}-{}'.format(time_stamp, name)
#    elif (time_stamp == '') and (name != ''):
#        fileName = name
#    elif (time_stamp != '') and (name == ''):
#        fileName = '{}-{}'.format(time_stamp, 'untitled')
#    else:
#        fileName = '{}-{}'.format(get_time_stamp(), 'untitled')
#
#    folderDir = get_folder_dir(source_name, subfolder)
#
#    fileDir = os.path.abspath(os.path.join(folderDir, fileName))
#
#    return fileDir


def save_figure(fig, file_path):
    """
    Save a matplotlib figure as a png.

    Params:
        fig: matplotlib.figure.Figure
            The figure to save
        file_path: string
            The file path to save to including the file name, excluding the
            extension
    """

    file_path = str(file_path)
    fig.savefig(file_path + '.svg')


def save_raw_data(rawData, filePath):
    """
    Save raw data in the form of a dictionary to a text file. New lines
    will be printed between entries in the dictionary.

    Params:
        rawData: dict
            The raw data as a dictionary - will be saved via JSON
        filePath: string
            The file path to save to including the file name, excluding the
            extension
    """

    with open(filePath + '.txt', 'w') as file:
        json.dump(rawData, file, indent=2)


def get_nv_sig_units():
    return {'coords': 'V', 'expected_count_rate': 'kcps', 
        'pulsed_readout_dur': 'ns', 
        'pulsed_SCC_readout_dur': 'ns', 'am_589_power': '0-1 V', 
        'pulsed_shelf_dur': 'ns', 'am_589_shelf_power': '0-1 V', 
        'pulsed_ionization_dur': 'ns', 'cobalt_638_power': 'mW', 
        'pulsed_reionization_dur': 'ns', 'cobalt_532_power': 'mW', 
        'magnet_angle': 'deg', 'resonance': 'GHz',
        'rabi': 'ns', 'uwave_power': 'dBm'}

# Error messages
    
def color_ind_err(color_ind):
    if color_ind != 532 or color_ind != 589:
        raise RuntimeError('Value of color_ind must be 532 or 589.'+
                           '\nYou entered {}'.format(color_ind))
        
def aom_ao_589_pwr_err(aom_ao_589_pwr):
    if aom_ao_589_pwr < 0 or aom_ao_589_pwr > 1.0:
        raise RuntimeError('Value for 589 aom must be within 0 to +1 V.'+
                           '\nYou entered {} V'.format(aom_ao_589_pwr))
        
def ao_638_pwr_err(ao_638_pwr):
    if ao_638_pwr < 0 or ao_638_pwr > 0.9:
        raise RuntimeError('Value for 638 ao must be within 0 to 0.9 V.'+
                           '\nYou entered {} V'.format(ao_638_pwr))
 
def x_y_image_grid(x_center, y_center, x_range, y_range, num_steps):
    
        if x_range != y_range:
            raise ValueError('x_range must equal y_range for now')

        x_num_steps = num_steps
        y_num_steps = num_steps

        # Force the scan to have square pixels by only applying num_steps
        # to the shorter axis
        half_x_range = x_range / 2
        half_y_range = y_range / 2

        x_low = x_center - half_x_range
        x_high = x_center + half_x_range
        y_low = y_center - half_y_range
        y_high = y_center + half_y_range

        # Apply scale and offset to get the voltages we'll apply to the galvo
        # Note that the polar/azimuthal angles, not the actual x/y positions
        # are linear in these voltages. For a small range, however, we don't
        # really care.
        x_voltages_1d = numpy.linspace(x_low, x_high, num_steps)
        y_voltages_1d = numpy.linspace(y_low, y_high, num_steps)

        ######### Works for any x_range, y_range #########

        # Winding cartesian product
        # The x values are repeated and the y values are mirrored and tiled
        # The comments below shows what happens for [1, 2, 3], [4, 5, 6]

        # [1, 2, 3] => [1, 2, 3, 3, 2, 1]
        x_inter = numpy.concatenate((x_voltages_1d,
                                     numpy.flipud(x_voltages_1d)))
        # [1, 2, 3, 3, 2, 1] => [1, 2, 3, 3, 2, 1, 1, 2, 3]
        if y_num_steps % 2 == 0:  # Even x size
            x_voltages = numpy.tile(x_inter, int(y_num_steps/2))
        else:  # Odd x size
            x_voltages = numpy.tile(x_inter, int(numpy.floor(y_num_steps/2)))
            x_voltages = numpy.concatenate((x_voltages, x_voltages_1d))

        # [4, 5, 6] => [4, 4, 4, 5, 5, 5, 6, 6, 6]
        y_voltages = numpy.repeat(y_voltages_1d, x_num_steps)

        voltages = numpy.vstack((x_voltages, y_voltages))   
        
        return x_voltages, y_voltages
# %% Misc
        
def opt_power_via_photodiode(color_ind, AO_power_settings = None, nd_filter = None):
    cxn = labrad.connect()
    
    if color_ind==532:
        cxn.pulse_streamer.constant([3],0.0, 0.0) # Turn on the green laser  
        time.sleep(0.5)
        optical_power = cxn.photodiode.read_optical_power()
        
    elif color_ind==589:
        cxn.filter_slider_ell9k.set_filter(nd_filter) # Change the nd filter for the yellow laser
        cxn.pulse_streamer.constant([],0.0, AO_power_settings) # Turn on the yellow laser       
        time.sleep(0.5)
        optical_power = cxn.photodiode.read_optical_power()
        
    elif color_ind==638:
        cxn.pulse_streamer.constant([7], 0.0, 0.0) # Turn on the red laser     
        time.sleep(0.5)
        optical_power = cxn.photodiode.read_optical_power()
    
    time.sleep(0.5)
    cxn.pulse_streamer.constant([], 0.0, 0.0)
    return optical_power

def calc_optical_power_mW(color_ind, optical_power_V):
    # Values found from experiments. See Notebook entry 3/19/2020 and 3/20/2020
    if color_ind == 532:
        return 13* optical_power_V + 0.037
    elif color_ind == 589:
        return 7.9* optical_power_V + 0.024
    if color_ind == 638:
        return 5.7* optical_power_V + 0.035

def measure_g_r_y_power(aom_ao_589_pwr, nd_filter):
    green_optical_power_pd = opt_power_via_photodiode(532)

    red_optical_power_pd = opt_power_via_photodiode(638)

    yellow_optical_power_pd = opt_power_via_photodiode(589,
           AO_power_settings = aom_ao_589_pwr, nd_filter = nd_filter)

    # Convert V to mW optical power
    green_optical_power_mW = \
            calc_optical_power_mW(532, green_optical_power_pd)

    red_optical_power_mW = \
            calc_optical_power_mW(638, red_optical_power_pd)

    yellow_optical_power_mW = \
            calc_optical_power_mW(589, yellow_optical_power_pd)
            
    return green_optical_power_pd, green_optical_power_mW, \
            red_optical_power_pd, red_optical_power_mW, \
            yellow_optical_power_pd, yellow_optical_power_mW
    
# %% Safe stop (TM mccambria)


"""
Safe stop allows you to listen for a stop command while other things are
happening. This allows you to, say, stop a loop-based routine halfway
through. To use safe stop, call init_safe_stop() and then poll for the
stop command with safe_stop(). It's up to you to actually stop the
routine once you get the signal. Note that there's no way to programmatically
halt safe stop once it's running; the user must press enter.

Safe stop works by setting up a second thread alongside the main
thread. This thread listens for input, and sets a threading event after
the input. A threading event is just a flag used for communication between
threads. safe_stop() simply returns whether the flag is set.
"""


def safe_stop_input():
    """
    This is what the safe stop thread does.
    """

    global SAFESTOPEVENT
    input('Press enter to stop...')
    SAFESTOPEVENT.set()


def check_safe_stop_alive():
    """
    Checks if the safe stop thread is alive.
    """

    global SAFESTOPTHREAD
    try:
        SAFESTOPTHREAD
        return SAFESTOPTHREAD.isAlive()
    except NameError:
        return False


def init_safe_stop():
    """
    Initialize safe stop. Recycles the current instance of safe stop if
    there's one already running.
    """

    global SAFESTOPEVENT
    global SAFESTOPTHREAD
    needNewSafeStop = False

    # Determine if we need a new instance of safe stop or if there's
    # already one running
    try:
        SAFESTOPEVENT
        SAFESTOPTHREAD
        if not SAFESTOPTHREAD.isAlive():
            # Safe stop has already run to completion so start it back up
            needNewSafeStop = True
    except NameError:
        # Safe stop was never initialized so just get a new instance
        needNewSafeStop = True

    if needNewSafeStop:
        SAFESTOPEVENT = threading.Event()
        SAFESTOPTHREAD = threading.Thread(target=safe_stop_input)
        SAFESTOPTHREAD.start()


def safe_stop():
    """
    Check if the user has told us to stop. Call this whenever there's a safe
    break point after initializing safe stop.
    """

    global SAFESTOPEVENT

    try:
        return SAFESTOPEVENT.is_set()
    except Exception:
        print('Stopping. You have to intialize safe stop before checking it.')
        return True


def poll_safe_stop():
    """
    Polls safe stop continuously until the user says stop. Effectively a
    regular blocking input. The problem with just sticking input() in the main
    thread is that you can't have multiple threads looking for input.
    """

    init_safe_stop()
    while True:
        time.sleep(0.1)
        if safe_stop():
            break


# %% State/globals


# This isn't really that scary - our client is and should be mostly stateless
# but in some cases it's just easier to share some state across the life of an
# experiment/across experiments. To do this safely and easily we store global
# variables on our LabRAD registry. The globals should only be accessed with
# the getters and setters here so that we can be sure they're implemented
# properly.


def get_drift():
    with labrad.connect() as cxn:
        cxn.registry.cd(['', 'State'])
        drift = cxn.registry.get('DRIFT')
    len_drift = len(drift)
    if len_drift != 3:
        print('Got drift of length {}.'.format(len_drift))
        print('Setting to length 3.')
        if len_drift < 3:
            for ind in range(3 - len_drift):
                drift.append(0.0)
        elif len_drift > 3:
            drift = drift[0:3]
    drift_to_return = []
    for el in drift:
        type_el = type(el)
        if type_el not in [float, numpy.float64]:
            print('Got drift element of type {}.'.format(type_el))
            print('Casting to float.')
            el = float(el)
        drift_to_return.append(el)
    return drift_to_return


def set_drift(drift):
    len_drift = len(drift)
    if len_drift != 3:
        print('Attempted to set drift of length {}.'.format(len_drift))
        print('Set drift unsuccessful.')
    for el in drift:
        type_el = type(el)
        if type_el is not float:
            print('Attempted to set drift element of type {}.'.format(type_el))
            print('Set drift unsuccessful.')
    with labrad.connect() as cxn:
        cxn.registry.cd(['', 'State'])
        return cxn.registry.set('DRIFT', drift)


def reset_drift():
    set_drift([0.0, 0.0, 0.0])


# %% Reset hardware
        

def reset_cfm(cxn=None):
    """Reset our cfm so that it's ready to go for a new experiment. Avoids
    unnecessarily resetting components that may suffer hysteresis (ie the 
    components that control xyz since these need to be reset in any
    routine where they matter anyway).
    """
    
    if cxn == None:
        with labrad.connect() as cxn:
            reset_cfm_with_cxn(cxn)
    else:
        reset_cfm_with_cxn(cxn)
        
            
def reset_cfm_with_cxn(cxn):
    cxn.pulse_streamer.reset()
    cxn.apd_tagger.reset()
    cxn.arbitrary_waveform_generator.reset()
    cxn.signal_generator_tsg4104a.reset()
    cxn.signal_generator_bnc835.reset()
