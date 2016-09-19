# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import numpy as np
import nibabel as nib
import os
import cPickle
from scipy.io import savemat

pjoin = os.path.join
class IOFactory(object):
    """
    Make a factory for congruent read/write data
    Usage:
        >>>factory = iofiles.IOFactory()
        >>>factory.createfactory('.', 'data.csv')
    """
    def createfactory(self, filepath, filename):
        """
        Create your factory
        ----------------------------------------
        Input:
            filepath: filepath as reading/writing
            filename: filenames
        Output: 
            A class
   
        Note:
            What support now is .csv, .pkl, .mat and .nifti
        """
        _comp_file = pjoin(filepath, filename)
        if _comp_file.endswith('csv'):
            return _CSV(_comp_file)
        elif _comp_file.endswith('pkl'):
            return _PKL(_comp_file)
        elif _comp_file.endswith('mat'):
            return _MAT(_comp_file)
        elif _comp_file.endswith('gz') | _comp_file.endswith('nii'):
            return _NIFTI(_comp_file)
        else:
            return None

class _CSV(object):
    def __init__(self, _comp_file):
	self._comp_file = _comp_file
    def save2csv(self, data):
        """
        Save a 1/2D list data into a csv file.
        ------------------------------------
        Parameters:
            data: raw data
        """
        if isinstance(data, list):
            try:
                f = open(self._comp_file, 'w')
            except IOError:
                print('Can not save file' + self._comp_file)
            else:
                for line in data:
                    if isinstance(line, list):
                        line_str = [str(item) for item in line]
                        line_str = ','.join(line_str)
                    else:
                        line_str = str(line)
                    f.write(line_str + '\n')
                f.close()
        else:
            raise ValueError, 'Input must be a list.'        

    def nparray2csv(self, data, labels = None):
        """
        Save a np array into a csv file.
        ---------------------------------------------
        Parameters:
            data: raw data
            labels: Data names. Labels as a list.
        """
        if isinstance(data, np.ndarray):
            if data.ndim == 1:
                data = np.expand_dims(data,axis=1)
            try:
                f = open(self._comp_file, 'w')
            except IOError:
                print('Can not save file' + self._comp_file)
            else:
                if isinstance(labels, list):
                    labels = [str(item) for item in labels]
                    labels = ','.join(labels)
                    f.write(labels + '\n')
                for line in data:
                    line_str = [str(item) for item in line]
                    line_str = ','.join(line_str)
                    f.write(line_str + '\n')
                f.close()
        else:
            raise ValueError, 'Input must be a numpy array.'


class _PKL(object):
    def __init__(self, _comp_file):
        self._comp_file = _comp_file

    def save_pkl(self, data):
        """
        Save data to .pkl
        ----------------------------
        Parameters:
            data: raw data
        """
        output_class = open(self._comp_file, 'wb')
        cPickle.dump(data, output_class)
        output_class.close()

    def load_pkl(self):
        """
        Load data from .pkl
        ------------------------------
        Parameters:
            filename: file name
            path: path of pointed pickle file
        Return:
            data
        """
        pkl_file = open(self._comp_file, 'rb')
        data = cPickle.load(pkl_file)
        pkl_file.close()
        return data


class _MAT(object):
    def __init__(self, _comp_file):
        self._comp_file = _comp_file

    def save_mat(self, data):
        """
        Save data to .mat
        ---------------------------------------
        Parameters:
            data: raw data dictionary, note that data must be a dictionary data
        """
        savemat(self._comp_file, data)     


class _NIFTI(object):
    def __init__(self, _comp_file):
        self._comp_file = _comp_file

    def save_nifti(self, data, header):
        """
        Save nifti data
	Parameters:
            data: saving data
        """
        img = nib.Nifti1Image(data, None, header)
        nib.save(img, self._comp_file)



