import numpy as np
from math import ceil
import pylab as py
from astropy.table import Table
from astropy.io import fits
from matplotlib.colors import LogNorm
import os
import pdb

def starfield(): # plot the targets in their 15jun07 image
    root = '/Users/nijaid/microlens/data/microlens/15jun07/combo/mag15jun07_'

    targets = ['OB150029','OB150211','OB140613']
    fig = py.figure(figsize=(15,5))
    for i in range(len(targets)):
        img = fits.getdata(root + targets[i] + '_kp.fits')
        coords = Table.read(root + targets[i] + '_kp.coo', format='ascii')
        x = coords['col1']
        y = coords['col2']

        py.subplot(1,3,i+1)
        py.imshow(img, cmap='Greys', norm=LogNorm(vmin=1.0,vmax=10000))
        py.plot([x+100,x], [y-100,y], 'r-')
        py.text(x+100, y-150, targets[i], fontsize=10, color='red')

        py.plot([150,351.1], [100,100], color='magenta', linewidth=2) # plot a scale
        py.text(238.5, 125, '2"', color='magenta', fontsize=10)

        # py.text(1010, 1010, 'N', color='green', fontsize=9)
        # ax.arrow(1010,935, 0,75, head_width=0.05, head_length=0.05, fc='green')
        # py.text(935, 935, 'E', color='green', fontsize=9)

        py.xlim(30,1100)
        py.ylim(40,1060)
        py.gca().axes.axis('off')
        py.subplots_adjust(wspace=0.025)

    # py.show()
    py.savefig('/Users/nijaid/microlens/starfield.png', dpi=300)

def mag_poserror(target):
    '''
    Plot magnitude v position uncertainty in date tiles.

    target - str: Lowercase name of the target.
    '''
    root = '/u/jlu/data/microlens/'
    epochs = analyzed(target)
    magCutOff = 17.0
    radius = 4
    scale = 0.00995

    py.figure(figsize=(15,5))
    py.clf()
        
    Nrows = ceil(float(len(epochs))/3)
    n = 1
    for epoch in epochs:
        starlist = root + '%s/combo/starfinder/mag%s_%s_kp_rms.lis' %(epoch,epoch,target)
        print(starlist)

        lis = Table.read(starlist, format='ascii')
        name = lis[lis.colnames[0]]
        mag = lis[lis.colnames[1]]
        x = lis[lis.colnames[3]]
        y = lis[lis.colnames[4]]
        xerr = lis[lis.colnames[5]]
        yerr = lis[lis.colnames[6]]
        snr = lis[lis.colnames[7]]
        corr = lis[lis.colnames[8]]

        merr = 1.086 / snr

        # Convert into arsec offset from field center
        # We determine the field center by assuming that stars
        # are detected all the way out the edge.
        xhalf = x.max() / 2.0
        yhalf = y.max() / 2.0
        x = (x - xhalf) * scale
        y = (y - yhalf) * scale
        xerr *= scale * 1000.0
        yerr *= scale * 1000.0

        r = np.hypot(x, y)
        err = (xerr + yerr) / 2.0

        magStep = 1.0
        radStep = 1.0
        magBins = np.arange(10.0, 20.0, magStep)
        radBins = np.arange(0.5, 9.5, radStep)

        errMag = np.zeros(len(magBins), float)
        errRad = np.zeros(len(radBins), float)
        merrMag = np.zeros(len(magBins), float)
        merrRad = np.zeros(len(radBins), float)

        # Compute errors in magnitude bins
        for mm in range(len(magBins)):
            mMin = magBins[mm] - (magStep / 2.0)
            mMax = magBins[mm] + (magStep / 2.0)
            idx = (np.where((mag >= mMin) & (mag < mMax) & (r < radius)))[0]

            if (len(idx) > 0):
                errMag[mm] = np.median(err[idx])
                merrMag[mm] = np.median(merr[idx])

        # Compute errors in magnitude bins
        for rr in range(len(radBins)):
            rMin = radBins[rr] - (radStep / 2.0)
            rMax = radBins[rr] + (radStep / 2.0)
            idx = (np.where((r >= rMin) & (r < rMax) & (mag < magCutOff)))[0]

            if (len(idx) > 0):
                errRad[rr] = np.median(err[idx])
                merrRad[rr] = np.median(err[idx])

        idx = (np.where((mag < magCutOff) & (r < radius)))[0]
        errMedian = np.median(err[idx])
        numInMedian = len(idx)

        py.subplot(Nrows, 3, n)
        idx = (np.where(r<radius))[0]
        py.semilogy(mag[idx], err[idx], 'k.')
        py.axis([15, 23, 1e-2, 30.0])
        py.ylabel('Positional Uncertainty (mas)', fontsize=12)
        date = '20' + epoch[0:2] + ' ' + epoch[2].upper() + epoch[3:5] + ' ' + epoch[5:]
        py.text(15, 10, date, fontsize=12)
        if ceil(float(n)/3) == Nrows:
            py.xlabel('K Magnitude', fontsize=12)

        n += 1

    py.show()

def analyzed(target):
    if target == 'ob150211':
        epochs = ['15may05', '15jun07', '15jun28', '15jul23', '16may03', '16jul14', '16aug02']
    if target == 'ob150029':
        epochs = ['15jun07', '15jul23', '16may24', '16jul14']
    if target == 'ob140613':
        epochs = ['15jun07', '15jun28', '16apr17', '16may24', '16aug02']
    return epochs


if __name__ == '__main__':
    from sys import argv
    if len(argv) > 1:
        if argv[1] == 'starfield':
            starfield()