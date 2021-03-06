# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 et:

import os
import numpy as np
from scipy import stats
from sklearn import preprocessing
from scipy.spatial.distance import pdist

from ATT.algorithm import tools
from ATT.util import plotfig
from ATT.interface import iofiles

pjoin = os.path.join

class FeatureDescription(object):
    def __init__(self, meas, regions, outlier_method = 'iqr', outlier_range = [-3, 3], mergehemi = False, figure = False):
        """
        Parameters:
        -------------
        meas: measdata
              for clarity, measdata should contain 1 feature.
              meas are matrix of (nsubject)x(nregions)
              each feature should has order r/l or l/r
              Therefore feature classification is nfeature/2
        regions: regions contain in meas.
                 Note that if you would like to merge hemisphere, regions should be regions have no hemispheric identity
        outlier_method: remove outlier criterion, 'iqr' or 'std' or 'abs'
        outlier_range: outlier range
        mergehemi: whether merge signals between hemispheres or not
        figure: whether plot figure or not
        """
        if isinstance(meas, list):
            meas = np.array(meas)
        if mergehemi:
            data = np.empty((meas.shape[0], meas.shape[1]/2))
            data_removed = np.empty((meas.shape[0], meas.shape[1]/2))
            n_removed = np.empty(meas.shape[1]/2)
            for i in range(data.shape[1]):
                data[:,i] = tools.hemi_merge(meas[:,2*i], meas[:,2*i+1])
            feat_stats = np.empty((5, meas.shape[1]/2))
            for i in range(data.shape[1]):
                n_removed[i], data_removed[:,i] = tools.removeoutlier(data[:,i], meth = outlier_method, thr = outlier_range)
        else:
            data = meas
            feat_stats = np.empty((5, meas.shape[1]))
            data_removed = np.empty((meas.shape[0], meas.shape[1]))
            n_removed = np.empty(meas.shape[1])
            for i in range(data.shape[1]):
                n_removed[i], data_removed[:,i] = tools.removeoutlier(data[:,i], meth = outlier_method, thr = outlier_range)
        
        self.regions = regions
        self.nsubj = meas.shape[0]
        self.figure = figure
        self.n_removed = n_removed
        self.data_removed = data_removed
        self.feat_stats = feat_stats

    def statisfeature(self):
        """
        Make bar plot and statistical data by mean and standard deviation
        ----------------------------------
        Returns:
            feat_stats: statistics for a feature
            rows are [mean, std, n_removed, t, p], respectively
        """
        # Feature description
        for i in range(self.data_removed.shape[1]):
            [t, p] = stats.ttest_1samp(tools.listwise_clean(self.data_removed)[:,i], 0)
            self.feat_stats[:, i] = [np.nanmean(self.data_removed[:,i]), np.nanstd(self.data_removed[:,i]), self.n_removed[i], t, p]    

        if self.figure:
            plotfig.plot_bar(np.nanmean(self.data_removed, axis=0).reshape((self.data_removed.shape[1]/2, 2)), 'title', self.regions, 'values', stats.sem(tools.listwise_clean(self.data_removed)).reshape((self.data_removed.shape[1]/2,2)))    
        return self.feat_stats


class FeatureRelation(object):
    # Class for feature relationship
    def __init__(self, meas, keys, outlier_method = 'iqr', outlier_range = [-3, 3], mergehemi = False, figure = False):
        """
        Parameters:
            meas: raw data
            keys: keys(or label) of raw data
            outlier_method: outlier analysis
            
             
        """
        if isinstance(meas, list):
            meas = np.array(meas)
        # Merge hemispheres and remove outlier
        if mergehemi:
            data = np.empty((meas.shape[0], meas.shape[1]/2))
            data_removed = np.empty((meas.shape[0], meas.shape[1]/2))
            n_removed = np.empty(meas.shape[1]/2)
            for i in range(data.shape[1]):
                data[:,i] = tools.hemi_merge(meas[:,2*i], meas[:,2*i+1])
            for i in range(data.shape[1]):
                n_removed[i], data_removed[:,i] = tools.removeoutlier(data[:,i], meth = outlier_method, thr = outlier_range)
        else:
            data = meas
            data_removed = np.empty((meas.shape[0], meas.shape[1]))
            n_removed = np.empty(meas.shape[1])
            for i in range(data.shape[1]):
                n_removed[i], data_removed[:,i] = tools.removeoutlier(data[:,i], meth = outlier_method, thr = outlier_range)   

        self.keys = keys
        self.figure = figure
        self.data_removed = data_removed
        self.n_removed = n_removed 
        self.mergehemi = mergehemi

    def feature_prediction1(self, method = 'pearson'):
        """
        Pearson correlation or spearman correlation between features
        If meas contains just two features, figures plot scatters.
        If there're multi-features, figures plot heatmap
        -----------------------------------------------
        Parameters:
            method: 'pearson' or 'spearman'
                    'pearson' means do pearson correlation
                    'spearman' means do spearman correlation
        Output:
            corr: correlation array or matrix
            pval: significance array or matrix of correlation 
        """
        if method == 'pearson':
            calfunc = stats.pearsonr
        elif method == 'spearman':
            calfunc = stats.spearman
        else:
            raise Exception('No such method now')

        if self.data_removed.ndim == 1:
            self.data_removed = np.expand_dims(self.data_removed, axis = 1)
        if self.data_removed.shape[1] == 1:
            raise Exception('No way to do correlation!')
        elif self.data_removed.shape[1] == 2:
            corr, pval = calfunc(tools.listwise_clean(self.data_removed)[:,0], tools.listwise_clean(self.data_removed)[:,1])
            if self.figure:
               plotfig.plot_corr(self.data_removed[:,0], self.data_removed[:,1], self.keys, method)  
        else:
            corr, pval = tools.calwithincorr(tools.listwise_clean(self.data_removed), method)
            if self.figure:
                plotfig.plot_mat(corr, self.keys, self.keys)
        return corr, pval

    def feature_prediction2(self, estimator):
        """
        Estimate prediction relationship using linear model
        Please install sklearn when using it
        Note that the first/two data is the DV (Dependent variable) 
        ---------------------------------------------------
        Parameters:
            estimator: linear model estimator
        Return:
            r2: determined values
            beta: scaled beta
            t: t values of each beta
            tpval: p values of each t
            f: f values of model test
            fpval: p values of f
        Note that if there're two hemispheres, output measurement should be xx*2 array. That follows order of raw data.
        """
        if self.mergehemi:
            measdata = tools.listwise_clean(self.data_removed)
            tval = np.empty((measdata.shape[1]-1,1))
            tpval = np.empty((measdata.shape[1]-1,1))
            for i in range(measdata.shape[1]-1):
                c = np.zeros(measdata.shape[1]-1)
                c[i] = 1
                r2, beta, tval[i], tpval[i], f, fpval = tools.lin_betafit(estimator, measdata[:,1:], measdata[:,0], c)
        else:
            measdata1 = tools.listwise_clean(self.data_removed[:,0::2])
            measdata2 = tools.listwise_clean(self.data_removed[:,1::2])
            
            r2 = np.empty(2)
            beta = np.empty((measdata1.shape[1]-1, 2))
            tval = np.empty((measdata1.shape[1]-1, 2))
            tpval = np.empty((measdata1.shape[1]-1, 2))
            f = np.empty(2)
            fpval = np.empty(2)
            for i in range(measdata1.shape[1]-1):
                c = np.zeros(measdata1.shape[1]-1) 
                c[i] = 1
                r2[0], beta[:,0], tval[i,0], tpval[i,0], f[0], fpval[0] = tools.lin_betafit(estimator, measdata1[:,1:], measdata1[:,0], c)
                r2[1], beta[:,1], tval[i,1], tpval[i,1], f[1], fpval[1] = tools.lin_betafit(estimator, measdata2[:,1:], measdata2[:,0], c)
        if self.figure:
            if self.mergehemi:
                xlbl = self.keys[1:]
                plotfig.plot_bar(beta, 'Scaled beta', xlbl, 'beta values', ['beta values'])
            else:
                xlbl1 = self.keys[2::2]
                xlbl2 = self.keys[3::2]
                plotfig.plot_bar(beta[:,0], 'Scaled beta', xlbl1, 'beta values', ['beta values'])
                plotfig.plot_bar(beta[:,1], 'Scaled beta', xlbl2, 'beta values', ['beta values'])
        return r2, beta, tval, tpval, f, fpval

    def feature_prediction3(self, estimator, n_fold=3, isshuffle=True, cvmeth = 'shufflesplit', score_type = 'r2', n_perm = 1000): 
        """
        Test if linear regression r2 is significative by using permutation cross validation
        Note that the first/two data is the DV (Dependent variable)
        --------------------------------------------------------------
        Parameters:
            estimator: linear model estimator
            n_fold: cross validation number of fold
            isshuffle: Whether shuffle data in cross validation at first
            cvmethod: cross validation method.
                      'kfold' or 'shufflesplit' is affordable
            score_type: scoring type
            n_perm: permutation number
        Return:
            scores: model scores
            permutation_scores: model scores in permutation
            pvalues: p values of permutation test            
            Note that if there're two hemispheres, output measurement should be xx*2 array. That follows order of raw data.
        """
        if self.mergehemi:
            measdata = tools.listwise_clean(self.data_removed)
            scores, n_scores, pvalues = tools.permutation_cross_validation(estimator, measdata[:,1:], measdata[:,0], n_fold, isshuffle, cvmeth, score_type, n_perm)
        else:
            scores = np.empty(2)
            n_scores = np.empty((n_perm, 2))
            pvalues = np.empty(2)
            measdata1 = tools.listwise_clean(self.data_removed[:,0::2])
            measdata2 = tools.listwise_clean(self.data_removed[:,1::2])
            scores[0], n_scores[:,0], pvalues[0] = tools.permutation_cross_validation(estimator, measdata1[:,1:], measdata1[:,0], n_fold, isshuffle, cvmeth, score_type, n_perm)
            scores[1], n_scores[:,1], pvalues[1] = tools.permutation_cross_validation(estimator, measdata2[:, 1:], measdata2[:,0], n_fold, isshuffle, cvmeth, score_type, n_perm)
        if self.figure:
            if self.mergehemi:
                xlbl = self.keys
                plotfig.plot_hist(n_scores, xlbl, scores, pvalues)
            else:
                xlbl1 = self.keys[2::2]
                xlbl2 = self.keys[3::2]
                plotfig.plot_hist(n_scores[:,0], xlbl1, scores[0], pvalues[0])
                plotfig.plot_hist(n_scores[:,1], xlbl2, scores[1], pvalues[1])
        return scores, n_scores, pvalues

class ComPatternMap(object):
    def __init__(self, data, regions, outlier_method = 'iqr', outlier_range = [-3, 3], mergehemi = False, figure = False):
        """
        Parameters:
            data: raw data. It could be 2D or 3D data.
                  2D data is activation data. Which is the form of nsubj*regions
                  3D data is roi resting data. Which is the form of timeseries*regions*nsubj
            regions: region names
            outlier_method: criterion of outlier removed, 'iqr' or 'std' or 'abs'
            outlier_range: outlier range
            mergehemi: whether merge signals between hemispheres or not
            figure: whether plot figures or not                     
        """
        if not isinstance(regions, list):
            regions = regions.tolist()
        if mergehemi:
            if data.ndim == 2:
                n_removed = np.empty(data.shape[1]/2)
                data_comb = np.empty((data.shape[0], data.shape[1]/2))
                data_removed = np.empty((data.shape[0], data.shape[1]/2))      
                for i in range(data_comb.shape[1]):
                    data_comb[:,i] = tools.hemi_merge(data[:,2*i], data[:,2*i+1])
                for i in range(data_comb.shape[1]):
                    n_removed[i], data_removed[:,i] = tools.removeoutlier(data_comb[:,i], meth = outlier_method, thr = outlier_range)
            elif data.ndim == 3:
                n_removed = np.empty((data.shape[1]/2, data.shape[2]))
                data_comb = np.empty((data.shape[0], data.shape[1]/2, data.shape[2]))
                data_removed = np.empty((data.shape[0], data.shape[1]/2, data.shape[2]))
                for i in range(data_comb.shape[1]):
                    for j in range(data_comb.shape[2]):
                        data_comb[:,i,j] = tools.hemi_merge(data[:,2*i,j], data[:,2*i+1,j])
                for i in range(data_comb.shape[1]):
                    for j in range(data_comb.shape[2]):
                        n_removed[i,j], data_removed[:,i,j] = tools.removeoutlier(data_comb[:,i,j], meth = outlier_method, thr = outlier_range)
            else:
                raise Exception('Support 2D or 3D data now')
        else:
            data_comb = data
            if data.ndim == 2:
                n_removed = np.empty(data.shape[1])
                data_removed = np.empty((data_comb.shape[0], data_comb.shape[1]))
                for i in range(data_comb.shape[1]):  
                    n_removed[i], data_removed[:,i] = tools.removeoutlier(data_comb[:,i], meth = outlier_method, thr = outlier_range)
            elif data.ndim == 3:
                n_removed = np.empty((data.shape[1], data.shape[2]))
                data_removed = np.empty((data_comb.shape[0], data_comb.shape[1], data_comb.shape[2]))
                for i in range(data_comb.shape[1]):
                    for j in range(data_comb.shape[2]):
                        n_removed[i,j], data_removed[:,i,j] = tools.removeoutlier(data_comb[:,i,j], meth = outlier_method, thr = outlier_range)
            else:
                raise Exception('Support 2D or 3D data now')
  
        self.regions = regions
        self.data_removed = data_removed
        self.n_removed = n_removed
        self.mergehemi = mergehemi
        self.figure = figure

    def patternmap(self, meth = 'correlation'):
        if self.data_removed.ndim == 2:
            self.data_removed = np.expand_dims(self.data_removed, axis = 2)
        distance = []
        corrmatrix = np.empty((self.data_removed.shape[1], self.data_removed.shape[1], self.data_removed.shape[2]))
        corrpval = np.empty((self.data_removed.shape[1], self.data_removed.shape[1], self.data_removed.shape[2]))
        for i in range(self.data_removed.shape[2]):
            cleandata = tools.listwise_clean(self.data_removed[...,i])
            corrmatrix[...,i], corrpval[...,i] = tools.calwithincorr(cleandata)
            distance.append(pdist(cleandata.T, meth))
        distance = np.array(distance)
        if self.figure is True:
            plotfig.plot_hierarchy(np.mean(distance, axis = 0), self.regions)
            plotfig.plot_mat(np.mean(corrmatrix, axis = 2), self.regions, self.regions)
        return corrmatrix, distance

class EvaluateMap(object):
    def __init__(self, issave = False, savepath= '.'):
        self.issave = issave
        self.savepath = savepath
    def dice_evaluate(self, data1, data2, filename = 'dice.pkl'):
        """
        Evaluate drawing accuracy by dice coefficient
        -------------------------------------------
        Parameters:
            data1, data2: raw data
            filename: if save, output file name. By default is dice.pkl 
        Output:
            dice: dice coefficient
        """
        if data1.ndim != data2.ndim:
            raise Exception('Two raw data need have the same dimensions')
        label1 = np.unique(data1)[1:]
        label2 = np.unique(data2)[1:]
        label = np.sort(np.unique(np.concatenate((label1, label2))))
        if data1.ndim == 3:
            data1 = np.expand_dims(data1, axis = 3)
        if data2.ndim == 3:
            data2 = np.expand.dims(data2, axis = 3)
        dice = np.empty((data1.shape[3], label.shape[0]))
        for i in range(data1.shape[3]):
            for j in range(label.shape[0]):
                data_mul = (data1[...,i] == (j+1)) * (data2[...,i] == (j+1))
                data_sum = (data1[...,i] == (j+1)) + (data2[...,i] == (j+1))
                if not np.any(data_sum[data_sum!=0]):
                    dice[i, j] = np.nan
                else:
                    dice[i, j] = 2.0*np.sum(data_mul)/(np.sum(data1[...,i] == (j+1)) + np.sum(data2[...,i] == (j+1)))
        if self.issave:
            iofiles.save_pkl(dice, filename, self.savepath) 
        return dice


