# -*- coding: utf-8 -*-
"""Template for major routines. Major routines are routines for which we will
probably want to save the data.

Created on Sun Jun 16 11:38:17 2019

@author: mccambria
"""


# %% Imports


import utils.tool_belt as tool_belt


# %% Constants


# %% Functions


def clean_up(cxn):

    pass


def save_data(name, raw_data, figs):
    """Save the raw data to a txt file as a json object. Save the figures as
    svgs.
    """

    time_stamp = tool_belt.get_time_stamp()

    file_path = tool_belt.get_file_path(__file__, time_stamp, name)

    tool_belt.save_raw_data(rawData, file_path)

    for fig in figs:
        tool_belt.save_figure(fig, file_path)


# %% Figure functions


# For a major routine we'll typically have a count rate as a function of
# some variable (maybe relaxation time or microwave frequency). We'll also
# typically record two count rates for each data point: a signal (when the
# microwaves are on, for example) and a reference (when the microwaves are off,
# following the same example). To present this data, we should be consistent
# and use the below pattern. For an example, see the figures generated by
# rabi.py. Of course, some major routines won't follow this pattern and that's
# fine. We should still stick to the general idea of plotting functions
# that can be used to recreate plots from existing data sets.

# Figure 1: Raw data line plots

#     Axis 1: The average signal and reference count rates on the same axis

#     Axis 2: The normalized (average signal / average reference) signal

# Figure 2 (1 axis): Fit with the normalized signal as a scatter plot and the
# fit as a smooth line through the data - text box displaying the fit function
# and optimized fit parameters


def create_raw_figure():
    """Create figure 1. If you're implementing incremental plotting, this
    should create a shell figure that can be filled in with update_raw_figure.
    It should still support complete plotting, though, since this is
    necessary for simple plotting of existing data sets.
    """

    pass


def update_raw_figure():
    """If you want your routine to support incremental plotting, add that
    functionality here. Incremental plotting is nice, but not always
    super important.
    """

    pass


def create_fit_figure():
    """Create figure 2."""

    pass


# %% Main


def main(cxn):
    """When you run the file, we'll call into main, which should contain the
    body of the routine.
    """

    # %% Initial set up here

    # %% Collect the data

    # %% Wrap up

    clean_up(cxn)

    # Set up the raw data dictionary
    raw_data = {}

    # Save the data and the figures from this run
    save_data(name, raw_data, figs)


# %% Run the file


# The __name__ variable will only be '__main__' if you run this file directly.
# This allows a file's functions, classes, etc to be imported without running
# the script that you set up here.
if __name__ == '__main__':

    # You should at least be able to recreate a data set's figures when you
    # run a file so we'll do that as an example here

    # Get the data
    file_name = ''  # eg '2019-06-07_14-20-27_ayrton12.txt'
    data = tool_belt.get_raw_data(__file__, file_name)

    # Replot
    create_raw_figure()
    create_fit_figure()