# -*- coding: utf-8 -*-
import numpy as np
import tomopy.tools.multiprocess_shared as mp

# --------------------------------------------------------------------

def normalize(args):
    """
    Normalize raw projection data with
    the white field projection data.

    Parameters
    ----------
    data : ndarray
        3-D tomographic data with dimensions:
        [projections, slices, pixels]

    data_white : ndarray
        2-D white field projection data.
        
    data_dark : ndarray
        2-D dark field projection data.

    cutoff : scalar
        Permitted maximum vaue of the
        normalized data. 

    Returns
    -------
    data : ndarray
        Normalized data.
        
    Examples
    --------
    - Normalize using white and dark fields:
        
        >>> import tomopy
        >>> 
        >>> # Load sinogram
        >>> myfile = 'demo/data.h5'
        >>> data, white, dark, theta = tomopy.xtomo_reader(myfile, slices_start=0, slices_end=1)
        >>> 
        >>> # Save sinogram before normalization
        >>> output_file='tmp/before_normalization_'
        >>> tomopy.xtomo_writer(data, output_file, axis=1)
        >>> print "Images are succesfully saved at " + output_file + '...'
        >>> 
        >>> # Construct tomo object
        >>> d = tomopy.xtomo_dataset(log='error')
        >>> d.dataset(data, white, dark, theta)
        >>> 
        >>> # Perform normalization
        >>> d.normalize()
        >>> 
        >>> # Save sinogram after normalization
        >>> output_file='tmp/after_normalization_'
        >>> tomopy.xtomo_writer(d.data, output_file, axis=1)
        >>> print "Images are succesfully saved at " + output_file + '...'
    """
    # Arguments passed by multi-processing wrapper
    ind, dshape, inputs = args
    
    # Function inputs
    data = mp.tonumpyarray(mp.shared_arr, dshape) # shared-array
    data_white, data_dark, cutoff = inputs
    
    for m in ind:
        data[m, :, :] = np.divide(data[m, :, :]-data_dark, 
                                  data_white-data_dark)

    if cutoff is not None:
        data[data > cutoff] = cutoff
    
    
    
    
    
    
    
    
    