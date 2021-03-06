# -*- coding: utf-8 -*-
import numpy as np
from scipy.optimize import minimize
from scipy import ndimage

from gridrec import Gridrec

# --------------------------------------------------------------------

def optimize_center(data, theta, slice_no, center_init, tol, mask, ratio):
    """ 
    Find the distance between the rotation axis and the middle
    of the detector field-of-view.
    
    The function exploits systematic artifacts in reconstructed images 
    due to shifts in the rotation center [1]. It uses image entropy
    as the error metric and ''Nelder-Mead'' routine (of the scipy 
    optimization module) as the optimizer.

    Parameters
    ----------
    data : ndarray, float32
        3-D tomographic data with dimensions:
        [projections, slices, pixels]

    slice_no : scalar
        The index of the slice to be used for finding optimal center.

    center_init : scalar
        The initial guess for the center.

    tol : scalar
        Desired sub-pixel accuracy.
        
    mask : bool
        If ``True`` applies a circular mask to the image.

    ratio : scalar
        The ratio of the radius of the circular mask to the
        edge of the reconstructed image.

    Returns
    -------
    output : scalar
        This function returns the index of the center position that
        results in the minimum entropy in the reconstructed image.
        
    References
    ----------
    [1] `SPIE Proceedings, Vol 6318, 631818(2006) \
    <dx.doi.org/10.1117/12.679101>`_
        
    Examples
    --------
    - Finding rotation center automatically:
        
        >>> import tomopy
        >>> 
        >>> # Load data
        >>> myfile = 'demo/data.h5'
        >>> data, white, dark, theta = tomopy.xtomo_reader(myfile, slices_start=0, slices_end=1)
        >>> 
        >>> # Construct tomo object
        >>> d = tomopy.xtomo_dataset(log='error')
        >>> d.dataset(data, white, dark, theta)
        >>> d.normalize()
        >>> 
        >>> # Find rotation center.
        >>> d.optimize_center()
        >>> 
        >>> # Perform reconstruction
        >>> d.gridrec()
        >>> 
        >>> # Save reconstructed data
        >>> output_file='tmp/recon_'
        >>> tomopy.xtomo_writer(d.data_recon, output_file)
        >>> print "Images are succesfully saved at " + output_file + '...'
    """

    # Make an initial reconstruction to adjust histogram limits. 
    recon = Gridrec(data, airPixels=20, ringWidth=10)
    recon.reconstruct(data, theta=theta, center=center_init, slice_no=slice_no)

    # Apply circular mask.
    if mask is True:
        rad = data.shape[2]/2
        y, x = np.ogrid[-rad:rad, -rad:rad]
        msk = x*x + y*y > ratio*ratio*rad*rad
        recon.data_recon[0, msk] = 0
    
    # Adjust histogram boundaries according to reconstruction.
    hist_min = np.min(recon.data_recon)
    if hist_min < 0:
        hist_min = 2 * hist_min
    elif hist_min >= 0:
        hist_min = 0.5 * hist_min
        
    hist_max = np.max(recon.data_recon)
    if hist_max < 0:
        hist_max = 0.5 * hist_max
    elif hist_max >= 0:
        hist_max = 2 * hist_max

    # Magic is ready to happen...
    res = minimize(_costFunc, center_init,
                   args=(data, recon, theta, slice_no, 
                         hist_min, hist_max, mask, ratio),
                   method='Nelder-Mead', tol=tol)
    
    # Have a look at what I found:
    print "calculated rotation center: " + str(np.squeeze(res.x))
    return res.x
    
# --------------------------------------------------------------------

def _costFunc(center, data, recon, theta, slice_no, 
              hist_min, hist_max, mask, ratio):
    """ 
    Cost function of the ``optimize_center``.
    """
    print 'trying center: ' + str(np.squeeze(center))
    center = np.array(center, dtype='float32')
    recon.reconstruct(data, theta=theta, center=center, slice_no=slice_no)

    # Apply circular mask.
    if mask is True:
        rad = data.shape[2]/2
        y, x = np.ogrid[-rad:rad, -rad:rad]
        msk = x*x + y*y > ratio*ratio*rad*rad
        recon.data_recon[0, msk] = 0

    histr, e = np.histogram(ndimage.filters.gaussian_filter(recon.data_recon, sigma=2.), 
                            bins=64, range=[hist_min, hist_max])
    histr = histr.astype('float32') / recon.data_recon.size + 1e-12
    return -np.dot(histr, np.log2(histr))