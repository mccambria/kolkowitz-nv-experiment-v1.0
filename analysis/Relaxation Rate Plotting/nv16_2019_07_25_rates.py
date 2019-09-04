# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 14:36:23 2019

This file plots the relaxation rate data collected for the nv16_2019_07_25.

The data is input manually, and plotted on a loglog plot with error bars along
the y-axis. A 1/f**2 line is also fit to the gamma rates to show the behavior.

@author: Aedan
"""

'''
nv16_2019_07_25


'''
# %%
def fit_eq_alpha(f, amp, alpha, offset):
    return amp*f**(-alpha) + offset

# %%

import matplotlib.pyplot as plt
from scipy import asarray as ar, exp
from scipy.optimize import curve_fit
import numpy

# The data
nv16_splitting_list = [28.6, 53.0, 81.2, 128.0, 283.7]
nv16_omega_avg_list = [0.58, 0.79, 1.75, 0.69, 0.64]
nv16_omega_error_list = [0.10, 0.11, 0.19, 0.10, 0.18]
nv16_gamma_avg_list = [110, 32, 18.2, 12.1, 6.8]
nv16_gamma_error_list = [20, 5, 1.0, 0.8, 0.4]

# Try to fit the gamma to a 1/f^alpha

fit_alpha_params, cov_arr = curve_fit(fit_eq_alpha, nv16_splitting_list, nv16_gamma_avg_list, 
                                p0 = [1000, 1, 3], sigma = nv16_gamma_error_list,
                                absolute_sigma = True)

splitting_linspace = numpy.linspace(10, 2000,
                                    1000)
omega_constant_array = numpy.empty([1000]) 
omega_constant_array[:] = numpy.average(nv16_omega_avg_list)

fig, ax = plt.subplots(1, 1, figsize=(10, 8))


axis_font = {'size':'14'}

orange = '#f7941d'
purple = '#87479b'

ax.set_xscale("log", nonposx='clip')
ax.set_yscale("log", nonposy='clip')
ax.errorbar(nv16_splitting_list, nv16_gamma_avg_list, yerr = nv16_gamma_error_list, 
            label = r'$\gamma$', fmt='o', markersize = 10, color=purple)
ax.errorbar(nv16_splitting_list, nv16_omega_avg_list, yerr = nv16_omega_error_list, 
            label = r'$\Omega$', fmt='^', markersize = 10, color=orange)
ax.plot(splitting_linspace, omega_constant_array, color= orange,
            label = r'$\Omega$')


#ax.plot(splitting_linspace, fit_eq_2(splitting_linspace, *fit_2_params), 
#            label = r'$f^{-2}$', color ='teal')
#ax.plot(splitting_linspace, fit_eq_1(splitting_linspace, *fit_1_params), 
#            label = r'$f^{-1}$', color = 'orange')

# %%

ax.plot(splitting_linspace, fit_eq_alpha(splitting_linspace, *fit_alpha_params), 
            color = purple, label = 'fit')

text = '\n'.join((r'$1/f^\alpha$ fit:',
                  r'$\alpha = $' + '%.2f'%(fit_alpha_params[1])
#                  r'$A_0 = $' + '%.0f'%(fit_alpha_params[0]),
#                  r'$\gamma_0 = $' + '%.2f'%(fit_params[2])
                  ))
props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
#ax.text(0.85, 0.7, text, transform=ax.transAxes, fontsize=12,
#        verticalalignment='top', bbox=props)

# %%

ax.tick_params(which = 'both', length=6, width=2, colors='k',
                grid_alpha=0.7, labelsize = 18)

ax.tick_params(which = 'major', length=12, width=2)

ax.grid()

ax.set_xlim([10,1200])
ax.set_ylim([0.1,300])

plt.xlabel('Splitting (MHz)', fontsize=18)
plt.ylabel('Relaxation Rate (kHz)', fontsize=18)
#plt.title('NV16', fontsize=18)
#ax.legend(fontsize=18)
fig.savefig("C:/Users/Aedan/Creative Cloud Files/Paper Illustrations/Magnetically Forbidden Rate/fig_3b.pdf", bbox_inches='tight')
