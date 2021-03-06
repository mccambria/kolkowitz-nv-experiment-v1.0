# -*- coding: utf-8 -*-
"""
Created on Sun Sep 15 13:12:42 2019

This file calculates the T2,max of the various NV rates we've collected.

From putting the NV into a coherent superposition between 0 and +/-1, the
maximum coherence time is set by the relaxation rates:
    
T2,max = 2 / (3*omega + gamma)

The error on this associated maximum T2 is then:
    
delta(T2,max) = (3*omega + gamma)**-2 * Sqrt( (6*del(omega))**2 + (2*del(gamma))**2 )

@author: Aedan
"""
import numpy
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# %%

font_size = 75
marker_size = 38 #40

xlim = [-100,1200]
ylim = [0.005,2.5]
#xticks = [0,400, 800]
xticks = [0,500, 1000]
yticks=[0.01,0.1,1]


# %%

nv1_splitting_list = [ 19.5, 19.8, 27.7, 28.9, 32.7, 51.8, 97.8, 116, 268, 350, 561.7, 1016.8]
nv1_omega_avg_list = numpy.array([ 0.83, 1.23, 1.30,  1.000,  1.42, 1.85, 1.41, 1.18, 1.04, 0.72, 1.19, 0.58])
nv1_omega_error_list = numpy.array([ 0.04, 0.04, 0.06, 0.016,  0.05, 0.08, 0.05, 0.06, 0.04, 0.04, 0.06, 0.03])*2
nv1_gamma_avg_list = numpy.array([58.3, 117, 64.5, 56.4,  42.6, 13.1, 3.91, 4.67, 1.98, 1.57, 0.70, 0.41])
nv1_gamma_error_list = numpy.array([1.4, 4, 1.4, 1.3,  0.9, 0.2, 0.1, 0.11, 0.1, 0.12, 0.05, 0.05])*2

# The data
nv2_splitting_list = [15.3,29.2, 45.5, 85.2, 280.4,697.4, 29.1, 44.8, 56.2, 56.9,  101.6]
nv2_omega_avg_list = numpy.array([0.24, 0.328, 0.266, 0.285, 0.276, 0.29,0.412, 0.356, 0.326, 0.42,  0.312])
nv2_omega_error_list = numpy.array([0.01, 0.013, 0.01, 0.011, 0.011, 0.02, 0.011, 0.012, 0.008, 0.05,  0.009])*2
nv2_gamma_avg_list = numpy.array([124, 31.1, 8.47, 2.62, 0.443, 0.81,20.9, 6.43, 3.64, 3.77,  1.33])
nv2_gamma_error_list = numpy.array([3, 0.4, 0.11, 0.05, 0.014, 0.06,0.3, 0.12, 0.08, 0.09,  0.05])*2

nv16_splitting_list = [17.1, 28.6, 53.0, 81.2, 128.0, 283.7, 495.8, 746]
nv16_omega_avg_list = numpy.array([0.708, 0.53, 0.87, 1.7, 0.60, 0.70, 1.4, 1.03])
nv16_omega_error_list = numpy.array([0.165, 0.05, 0.09, 0.2, 0.05, 0.07, 0.4, 0.17])*2
nv16_gamma_avg_list = numpy.array([108, 90, 26.2, 17.5, 11.3, 5.6, 3.7, 2.8])
nv16_gamma_error_list = numpy.array([10, 5, 0.9, 0.6, 0.4, 0.3, 0.4, 0.3])*2

#NV0
splitting_list = [23.4, 26.3, 36.2, 48.1, 60.5, 92.3, 150.8, 329.6, 884.9] #, 1080.5, 1148.4
omega_avg_list = numpy.array([0.283, 0.33,0.32,  0.314, 0.24, 0.253, 0.29, 0.33, 0.29])#, 0.28, 0.38
omega_error_list = numpy.array([0.017, 0.03,0.03,  0.01, 0.02, 0.012, 0.02, 0.02, 0.02])*2 #, 0.05, 0.04
gamma_avg_list = numpy.array([	34.5, 29.0, 20.4,  15.8, 9.1, 6.4, 4.08, 1.23, 0.45]) #, 0.69, 0.35
gamma_error_list = numpy.array([1.3, 1.1, 0.5, 0.3, 0.3, 0.1, 0.15, 0.07, 0.03])*2#, 0.12, 0.03


nv13_splitting_list = [10.9,  23.1,  29.8, 51.9, 72.4, 112.9, 164.1, 256.2]
nv13_omega_avg_list = numpy.array([0.45,  1.01, 1.01, 0.39, 0.76, 0.92, 0.66, 0.23])
nv13_omega_error_list = numpy.array([0.06,  0.16,   0.09, 0.04, 0.1, 0.14, 0.11, 0.04])*2
nv13_gamma_avg_list = numpy.array([240,  62, 19.3, 17.7, 16.2, 12.1, 5.6, 2.1])
nv13_gamma_error_list = numpy.array([25,  8,   1.1, 1.4, 1.1, 0.9, 0.5, 0.3])*2

# %% NV1

nv1_color = '#87479b'

T2_max_1 = 2 / (3 * nv1_omega_avg_list + nv1_gamma_avg_list) 
T2_max_error_1 = (3*nv1_omega_avg_list + nv1_gamma_avg_list)**-2 * numpy.sqrt( (6*nv1_omega_error_list)**2 + (2*nv1_gamma_error_list)**2 )

T2_max_traditional_1 = 2 / (3 * nv1_omega_avg_list)
T2_max_traditional_error_1 = T2_max_traditional_1 * nv1_omega_error_list / nv1_omega_avg_list

average_traditional_t2_max_1= numpy.empty([1000]) 
average_traditional_t2_max_1[:] = numpy.average(T2_max_traditional_1)

average_traditional_t2_error_1= numpy.empty([1000]) 
average_traditional_t2_error_1[:]= numpy.sqrt(sum(T2_max_traditional_error_1**2)) / len(T2_max_traditional_error_1)

#print(average_traditional_t2_max_1)
#print(average_traditional_t2_error_1)

# %% NV2

nv2_color = '#87479b'

T2_max_2 = 2 / (3 * nv2_omega_avg_list + nv2_gamma_avg_list) 
T2_max_error_2 = (3*nv2_omega_avg_list + nv2_gamma_avg_list)**-2 * numpy.sqrt( (6*nv2_omega_error_list)**2 + (2*nv2_gamma_error_list)**2 )

T2_max_traditional_2 = 2 / (3 * nv2_omega_avg_list)
T2_max_traditional_error_2 = T2_max_traditional_2 * nv2_omega_error_list / nv2_omega_avg_list

average_traditional_t2_max_2= numpy.empty([1000]) 
average_traditional_t2_max_2[:] = numpy.average(T2_max_traditional_2)

average_traditional_t2_error_2= numpy.empty([1000]) 
average_traditional_t2_error_2[:]= numpy.sqrt(sum(T2_max_traditional_error_2**2)) / len(T2_max_traditional_error_2)

# %% NV16

nv16_color = '#87479b'

T2_max_16 = 2 / (3 * nv16_omega_avg_list + nv16_gamma_avg_list) 
T2_max_error_16 = (3*nv16_omega_avg_list + nv16_gamma_avg_list)**-2 * numpy.sqrt( (6*nv16_omega_error_list)**2 + (2*nv16_gamma_error_list)**2 )

T2_max_traditional_16 = 2 / (3 * nv16_omega_avg_list)
T2_max_traditional_error_16 = T2_max_traditional_16 * nv16_omega_error_list / nv16_omega_avg_list

average_traditional_t2_max_16= numpy.empty([1000]) 
average_traditional_t2_max_16[:] = numpy.average(T2_max_traditional_16)

average_traditional_t2_error_16= numpy.empty([1000]) 
average_traditional_t2_error_16[:]= numpy.sqrt(sum(T2_max_traditional_error_16**2)) / len(T2_max_traditional_error_16)

# %% NV0

nv0_color = '#87479b'

T2_max_0 = 2 / (3 * omega_avg_list + gamma_avg_list) 
T2_max_error_0 = (3*omega_avg_list + gamma_avg_list)**-2 * numpy.sqrt( (6*omega_error_list)**2 + (2*gamma_error_list)**2 )

T2_max_traditional_0 = 2 / (3 * omega_avg_list)
T2_max_traditional_error_0 = T2_max_traditional_0 * omega_error_list / omega_avg_list

average_traditional_t2_max_0= numpy.empty([1000]) 
average_traditional_t2_max_0[:] = numpy.average(T2_max_traditional_0)

average_traditional_t2_error_0= numpy.empty([1000]) 
average_traditional_t2_error_0[:]= numpy.sqrt(sum(T2_max_traditional_error_0**2)) / len(T2_max_traditional_error_0)


print(T2_max_1[1]*1000, T2_max_error_1[1]*1000, 
      T2_max_2[0]*1000, T2_max_error_2[0]*1000,
      T2_max_16[0]*1000, T2_max_error_16[0]*1000,
      T2_max_0[0]*1000, T2_max_error_0[0]*1000)

# %% NV13

T2_max_13 = 2 / (3 * nv13_omega_avg_list + nv13_gamma_avg_list) 
T2_max_error_13 = (3*nv13_omega_avg_list + nv13_gamma_avg_list)**-2 * numpy.sqrt( (6*nv13_omega_error_list)**2 + (2*nv13_gamma_error_list)**2 )

print(T2_max_13[0]*1000, T2_max_error_13[0]*1000)
# %%

linspace = numpy.linspace(0, 2000, 1000)


fig1, ax = plt.subplots(1, 1, figsize=(8, 8))

ax.errorbar(nv1_splitting_list, T2_max_1, yerr = T2_max_error_1, 
            label = 'NV1',  color= nv1_color, fmt='D',markersize = marker_size, elinewidth=4)

print(numpy.average(T2_max_traditional_1))
ax.set_yscale("log", nonposy='clip')
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y,pos: ('{{:.{:1d}f}}'.format(int(numpy.maximum(-numpy.log10(y),0)))).format(y)))



ax.tick_params(which = 'both', length=16, width=3, colors='k',
                 direction = 'in', grid_alpha=0.7, labelsize = font_size)

ax.tick_params(which = 'major', length=30, width=5)
ax.set_xticks(xticks)
ax.set_yticks(yticks)

locmin = ticker.LogLocator(base=10.0,subs=(0.1, 0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9),numticks=16)
ax.yaxis.set_minor_locator(locmin)
ax.yaxis.set_minor_formatter(ticker.NullFormatter())

ax.set_xlim(xlim)
ax.set_ylim(ylim)

ax.grid(axis='y',lw=3)

#plt.xlabel(r'$\Delta_{\pm}$ (MHz)', fontsize=font_size)
#plt.ylabel(r'$T_{2,max}$ (ms)', fontsize=font_size)

fig1.savefig("C:/Users/Aedan/Creative Cloud Files/Paper Illustrations/Magnetically Forbidden Rate/fig_3a_inset.pdf", bbox_inches='tight')


# %%

fig2, ax = plt.subplots(1, 1, figsize=(8, 8))

ax.errorbar(nv2_splitting_list, T2_max_2, yerr = T2_max_error_2, 
            label = 'NV2',  color= nv2_color, fmt='D',markersize = marker_size, elinewidth=4)
#ax.plot(linspace, average_traditional_t2_max_2,  
#            label = 'NV2', linestyle='-.', color = nv2_color, linewidth=3)

print(numpy.average(T2_max_traditional_2))

ax.tick_params(which = 'both', length=16, width=3, colors='k',
                 direction = 'in', grid_alpha=0.7, labelsize = font_size)

ax.tick_params(which = 'major', length=30, width=5)

ax.set_yscale("log", nonposy='clip')
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y,pos: ('{{:.{:1d}f}}'.format(int(numpy.maximum(-numpy.log10(y),0)))).format(y)))
ax.set_xticks(xticks)
ax.set_yticks(yticks)

locmin = ticker.LogLocator(base=10.0,subs=(0.1, 0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9),numticks=16)
ax.yaxis.set_minor_locator(locmin)
ax.yaxis.set_minor_formatter(ticker.NullFormatter())

ax.set_xlim(xlim)
ax.set_ylim(ylim)

ax.grid(axis='y',lw=3)
#plt.xlabel(r'$\Delta_{\pm}$ (MHz)', fontsize=font_size)
#plt.ylabel(r'$T_{2,max}$ (ms)', fontsize=font_size)

fig2.savefig("C:/Users/Aedan/Creative Cloud Files/Paper Illustrations/Magnetically Forbidden Rate/fig_3b_inset.pdf", bbox_inches='tight')


# %%
fig3, ax = plt.subplots(1, 1, figsize=(8, 8))
ax.errorbar(nv16_splitting_list, T2_max_16, yerr = T2_max_error_16, 
            label = 'NV16',  color= nv16_color, fmt='D',markersize = marker_size, elinewidth=4)
#ax.plot(linspace, average_traditional_t2_max_16,  
#            label = 'NV16', linestyle='--', color = nv16_color, linewidth=3)

print(numpy.average(T2_max_traditional_16))

ax.tick_params(which = 'both', length=16, width=3, colors='k',
                 direction = 'in', grid_alpha=0.7, labelsize = font_size)

ax.tick_params(which = 'major', length=20, width=5)

ax.set_yscale("log", nonposy='clip')
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y,pos: ('{{:.{:1d}f}}'.format(int(numpy.maximum(-numpy.log10(y),0)))).format(y)))
ax.set_xticks(xticks)
ax.set_yticks(yticks)

locmin = ticker.LogLocator(base=10.0,subs=(0.1, 0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9),numticks=16)
ax.yaxis.set_minor_locator(locmin)
ax.yaxis.set_minor_formatter(ticker.NullFormatter())

ax.grid(axis='y',lw=3)
#plt.xlabel(r'$\Delta_{\pm}$ (MHz)', fontsize=font_size)
#plt.ylabel(r'$T_{2,max}$ (ms)', fontsize=font_size)

ax.set_xlim(xlim)
ax.set_ylim(ylim)

#ax.set_xscale("log", nonposx='clip')


#ax.legend(fontsize=18)

fig3.savefig("C:/Users/Aedan/Creative Cloud Files/Paper Illustrations/Magnetically Forbidden Rate/fig_3c_inset.pdf", bbox_inches='tight')

# %%
fig4, ax = plt.subplots(1, 1, figsize=(8, 8))
ax.errorbar(splitting_list, T2_max_0, yerr = T2_max_error_0, 
            label = 'NV0',  color= nv0_color, fmt='D',markersize = marker_size, elinewidth=4)

print(numpy.average(T2_max_traditional_0))

ax.tick_params(which = 'both', length=16, width=3, colors='k',
                 direction = 'in', grid_alpha=0.7, labelsize = font_size)

ax.tick_params(which = 'major', length=20, width=5)

ax.set_yscale("log", nonposy='clip')
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y,pos: ('{{:.{:1d}f}}'.format(int(numpy.maximum(-numpy.log10(y),0)))).format(y)))
ax.set_xticks(xticks)
ax.set_yticks(yticks)

locmin = ticker.LogLocator(base=10.0,subs=(0.1, 0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9),numticks=16)
ax.yaxis.set_minor_locator(locmin)
ax.yaxis.set_minor_formatter(ticker.NullFormatter())

ax.grid(axis='y',lw=3)
#plt.xlabel(r'$\Delta_{\pm}$ (MHz)', fontsize=font_size)
#plt.ylabel(r'$T_{2,max}$ (ms)', fontsize=font_size)

ax.set_xlim(xlim)
ax.set_ylim(ylim)

#ax.set_xscale("log", nonposx='clip')


#ax.legend(fontsize=18)

fig4.savefig("C:/Users/Aedan/Creative Cloud Files/Paper Illustrations/Magnetically Forbidden Rate/fig_3d_inset.pdf", bbox_inches='tight')


# %%
fig5, ax = plt.subplots(1, 1, figsize=(8, 8))
ax.errorbar(nv13_splitting_list, T2_max_13, yerr = T2_max_error_13, 
            label = 'NV0',  color= nv0_color, fmt='D',markersize = marker_size, elinewidth=4)

#print(numpy.average(T2_max_traditional_13))

ax.tick_params(which = 'both', length=16, width=3, colors='k',
                 direction = 'in', grid_alpha=0.7, labelsize = font_size)

ax.tick_params(which = 'major', length=20, width=5)

ax.set_yscale("log", nonposy='clip')
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y,pos: ('{{:.{:1d}f}}'.format(int(numpy.maximum(-numpy.log10(y),0)))).format(y)))
ax.set_xticks([0, 150, 300])
ax.set_yticks([0.01, 0.1, 1])

locmin = ticker.LogLocator(base=10.0,subs=(0.1, 0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9),numticks=16)
ax.yaxis.set_minor_locator(locmin)
ax.yaxis.set_minor_formatter(ticker.NullFormatter())

ax.grid(axis='y', lw=3)
plt.xlabel(r'$\Delta_{\pm}$ (MHz)', fontsize=font_size)
plt.ylabel(r'$T_{2,max}$ (ms)', fontsize=font_size)

ax.set_xlim([-15,350])
ax.set_ylim([0.004,1.1])

#ax.set_xscale("log", nonposx='clip')


#ax.legend(fontsize=18)

fig5.savefig("C:/Users/Aedan/Creative Cloud Files/Paper Illustrations/Magnetically Forbidden Rate/NV13_inset.pdf", bbox_inches='tight')


