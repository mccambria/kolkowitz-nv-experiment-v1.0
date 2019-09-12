# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 14:36:23 2019

This file plots the relaxation rate data collected for the nv0_2019_06_27.

@author: Aedan
"""

'''
nv0_2019_06_27


'''
# %%
def fit_eq_alpha(f, amp, alpha):
    return amp*f**(-alpha)

# %%

import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy

# The data
splitting_list = [48.1, 92.3]
omega_avg_list = [0.45, 0.25]
omega_error_list = [0.14, 0.05]
gamma_avg_list = [17.5, 6.4]
gamma_error_list = [0.7, 0.3]

# Try to fit the gamma to a 1/f^2

fit_alpha_params, cov_arr = curve_fit(fit_eq_alpha, splitting_list, gamma_avg_list, 
                                p0 = (100, 1), sigma = gamma_error_list,
                                absolute_sigma = True)

splitting_linspace = numpy.linspace(10, 2000,
                                    1000)

omega_constant_array = numpy.empty([1000]) 
omega_constant_array[:] = numpy.average(omega_avg_list)


fig, ax = plt.subplots(1, 1, figsize=(10, 8))


axis_font = {'size':'14'}

orange = '#f7941d'
purple = '#87479b'

ax.set_xscale("log", nonposx='clip')
ax.set_yscale("log", nonposy='clip')
ax.errorbar(splitting_list, gamma_avg_list, yerr = gamma_error_list, 
            label = r'$\gamma$',  fmt='o',markersize = 10, color = purple)
ax.errorbar(splitting_list, omega_avg_list, yerr = omega_error_list, 
            label = r'$\Omega$', fmt='^', markersize = 10, color=orange)


# %%

ax.plot(splitting_linspace, fit_eq_alpha(splitting_linspace, *fit_alpha_params), 
             label = r'fit',color =purple)
ax.plot(splitting_linspace, omega_constant_array, color = orange,
            label = r'$\Omega$')

text = '\n'.join((r'$1/f^{\alpha}$ fit:',
                  r'$\alpha = $' + '%.2f'%(fit_alpha_params[1]),
#                  r'$\gamma_\infty = $' + '%.2f'%(fit_alpha_params[2])
                  r'$A_0 = $' + '%.0f'%(fit_alpha_params[0])
                  ))
props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
ax.text(0.85, 0.7, text, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', bbox=props)

# %%

ax.tick_params(which = 'both', length=6, width=2, colors='k',
                grid_alpha=0.7, labelsize = 18)

ax.tick_params(which = 'major', length=12, width=2)

ax.grid()

ax.set_xlim([10,1200])
ax.set_ylim([0.1,300])

plt.xlabel('Splitting (MHz)', fontsize=18)
plt.ylabel('Relaxation Rate (kHz)', fontsize=18)
plt.title('NV 0', fontsize=18)
#ax.legend(fontsize=18)
fig.canvas.draw()
fig.canvas.flush_events()

#fig.savefig("C:/Users/Aedan/Creative Cloud Files/Paper Illustrations/Magnetically Forbidden Rate/fig_3c.pdf", bbox_inches='tight')