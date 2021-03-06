import numpy as np
import matplotlib.pyplot as py
from astropy.table import Table
from microlens.jlu import model, model_fitter
import os
import pdb


def getdata(target, pdir):
    if target=='ob150211':
        phot = Table.read('/g/lu/microlens/cross_epoch/OB150211/OGLE-2015-BLG-0211.dat', format='ascii')
        data = {'raL': 17.4906056,
                'decL': -30.9817500}
    elif target=='ob140613':
        phot = Table.read('/g/lu/microlens/cross_epoch/OB140613/OGLE-2014-BLG-0613.dat', format='ascii')
        data = {'raL': 17.8993556,
                'decL': -28.5726667}
    elif target=='ob150029':
        phot = Table.read('/g/lu/microlens/cross_epoch/OB150029/OGLE-2015-BLG-0029.dat', format='ascii')
        data = {'raL': 17.9962778,
                'decL': -28.6449444}
    else:
        raise ValueError(target+' does not have a listed RA and dec')
    
    points = Table.read(pdir + target + '.points', format='ascii')

    points['col2'] = (points['col2'] - points['col2'][0]) * 0.00995
    points['col3'] = (points['col3'] - points['col3'][0]) * 0.00995
    points['col4'] *= 0.00995
    points['col5'] *= 0.00995

    data['mag_err'] = phot['col3']
    data['mag'] = phot['col2']
    data['xpos'] = points['col2']
    data['ypos'] = points['col3']
    data['xpos_err'] = points['col4']
    data['ypos_err'] = points['col5']
    data['t_ast'] = points['col1']*365.25 - 678943.0 # convert to MJD 
    data['t_phot'] = phot['col1'] - 2400000.5 # convert to MJD approximately (from OGLE's HJD)

    return data

def modelfit(target, align_dir, phot_only = False, parallax = False, solve = True, points_dir = 'points_d/', runcode = 'aa_'):
    data = getdata(target, align_dir+points_dir)

    if parallax == False:
        if phot_only:
            mdir = 'mnest_pspl_phot/'
            fit = model_fitter.PSPL_phot_Solver(data)
        if not phot_only:
            mdir = 'mnest_pspl/'
            fit = model_fitter.PSPL_Solver(data)
    elif parallax == True:
        if phot_only:
            mdir = 'mnest_pspl_par_phot/'
            fit = model_fitter.PSPL_phot_parallax_Solver(data)
        if not phot_only:
            mdir = 'mnest_pspl_par/'
            fit = model_fitter.PSPL_parallax_Solver(data)

    fit.outputfiles_basename = align_dir+mdir+runcode
    if solve:
        if target == 'ob150211':
            fit.mag_base_gen = model_fitter.make_gen(16.0, 18.0)
            fit.dL_gen = model_fitter.make_gen(500, 8000)
            
        if not os.path.exists(align_dir+mdir):
            os.mkdir(align_dir+mdir)
        
        fit.solve()
        fit.plot_posteriors()

    if not os.path.exists(align_dir+mdir):
        raise ValueError('This model has not been ran yet.')
        
    modeled = fit.get_best_fit_model()

    # Create t_dat vector of times covering data times + interim periods to get a smooth photometric model
    t_dat = np.linspace(np.min(data['t_phot']), np.max(data['t_phot']), num=len(data['t_phot'])*2, endpoint=True)
    mag_dat = modeled.get_photometry(t_dat)
    mag = modeled.get_photometry(data['t_phot'])

    lnL_phot = modeled.likely_photometry(data['t_phot'], data['mag'], data['mag_err'])
    if phot_only:
        lnL = lnL_phot.mean()
    if not phot_only:
        pos = modeled.get_astrometry(data['t_ast'])
        lnL_ast = modeled.likely_astrometry(data['t_ast'], data['xpos'], data['ypos'], data['xpos_err'], data['ypos_err'])
        lnL = lnL_phot.mean() + lnL_ast.mean()

    print('lnL: ', lnL)

    if not os.path.exists(align_dir+mdir+'plots/'):
        os.mkdir(align_dir+mdir+'plots/')

    fig1, (pho, pho_res) = py.subplots(2,1, figsize=(10,10), gridspec_kw = {'height_ratios': [3,1]}, sharex=True)
    fig1.subplots_adjust(hspace=0)
    pho.errorbar(data['t_phot'], data['mag'], yerr=data['mag_err'], fmt='k.', label='OGLE-IV')
    pho.plot(t_dat, mag_dat, 'r-', label='best-fit model')
    pho.set_ylabel('mag')
    pho.invert_yaxis()
    pho.legend()
    pho.set_title(target + ' Photometry')
    pho_res.errorbar(data['t_phot'], data['mag'] - mag, yerr=data['mag_err'], fmt='k.')
    pho_res.plot(data['t_phot'], mag-mag, 'r-', lw=2)
    pho_res.invert_yaxis()
    pho_res.set_ylabel('data - model')
    pho_res.set_xlabel('days (MJD)')
    py.savefig(align_dir+mdir+'plots/photo.png', bbox_inches='tight')

    if not phot_only:
        fig2, (x, x_res) = py.subplots(2,1, gridspec_kw = {'height_ratios': [3,1]}, sharex=True)
        fig2.subplots_adjust(hspace=0)
        x.errorbar(data['t_ast'], data['xpos'], yerr=data['xpos_err'], fmt='k.', label='aligned data')
        x.plot(data['t_ast'], pos[:,0], 'r-', label='model')
        x.set_ylabel('X Pos (")')
        x.legend()
        x_res.errorbar(data['t_ast'], data['xpos'] - pos[:,0], yerr=data['xpos_err'], fmt='k.')
        x_res.plot(data['t_ast'], pos[:,0] - pos[:,0], 'r-')
        x_res.set_xlabel('days (MJD)')
        x_res.set_ylabel('data - model')
        x.set_title('X')
        py.savefig(align_dir+mdir+'plots/x_pos.png', bbox_inches='tight')

        fig3, (y, y_res) = py.subplots(2,1, gridspec_kw = {'height_ratios': [3,1]}, sharex=True)
        fig3.subplots_adjust(hspace=0)
        y.errorbar(data['t_ast'], data['ypos'], yerr=data['ypos_err'], fmt='k.', label='aligned data')
        y.plot(data['t_ast'], pos[:,1], 'r-', label='model')
        y.set_ylabel('Y Pos (")')
        y.legend()
        y_res.errorbar(data['t_ast'], data['ypos'] - pos[:,1], yerr=data['ypos_err'], fmt='k.')
        y_res.plot(data['t_ast'], pos[:,1] - pos[:,1], 'r-')
        y_res.set_xlabel('days (MJD)')
        y_res.set_ylabel('data - model')
        y.set_title('Y')
        py.savefig(align_dir+mdir+'plots/y_pos.png', bbox_inches='tight')

        py.figure(4)
        py.clf()
        py.errorbar(data['xpos'], data['ypos'], xerr=data['xpos_err'], yerr=data['ypos_err'], fmt='k.')
        py.plot(pos[:,0], pos[:,1], 'r-')
        py.gca().invert_xaxis()
        py.xlabel('X Pos (")')
        py.ylabel('Y Pos (")')
        py.legend(['model', 'aligned data'])
        py.title(target + ' X and Y')
        py.savefig(align_dir+mdir+'plots/pos.png', bbox_inches='tight')

    fit.summarize_results()

    best = fit.get_best_fit()
    
    out = open(align_dir+mdir+runcode+'final.txt', 'w')
    pars, q = quantiles(fit)
    out.write('                       best      median\n')
    for n in pars:
        out.write('%15s  %10.3f  %10.3f + %10.3f - %10.3f\n' % \
                      (n, best[n], q[n][0], q[n][1], q[n][2]))
    out.close()
    
    return

def quantiles(fit):
    tab = fit.load_mnest_results()

    pars = tab.colnames
        
    weights = tab['weights']
    sumweights = np.sum(weights)
    weights = weights / sumweights

    sig1 = 0.682689
    sig2 = 0.9545
    sig3 = 0.9973
    sig1_lo = (1.-sig1)/2.
    sig2_lo = (1.-sig2)/2.
    sig3_lo = (1.-sig3)/2.
    sig1_hi = 1.-sig1_lo
    sig2_hi = 1.-sig2_lo
    sig3_hi = 1.-sig3_lo

    # Calculate the median and quantiles.
    med_vals = {}
    for n in pars:
        # Calculate median, 1 sigma lo, and 1 sigma hi credible interval.
        med_vals[n] = model_fitter.weighted_quantile(tab[n], [0.5, sig1_lo, sig1_hi],
                                                         sample_weight=weights)
        # Switch from values to errors.
        med_vals[n][1] = med_vals[n][0] - med_vals[n][1]
        med_vals[n][2] = med_vals[n][2] - med_vals[n][0]
            

    return pars, med_vals
