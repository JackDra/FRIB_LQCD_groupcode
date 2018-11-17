#!/usr/bin/env python

import Data as da
import numpy as np
from warnings import warn
import xarray as xr
'''

Module for resampling of data.

'''
## some default information for bootstrap and jackknife
## you can pass in your own resampling information to the class
default_bootstrap_info = {}
default_bootstrap_info['type'] = 'bootstrap'
default_bootstrap_info['nboot'] = 200
default_bootstrap_info['n_rand'] = 'data_length'
default_jackknife_info = {}
default_jackknife_info['type'] = 'jackknife'
default_jackknife_info['order'] = 1
startseed = 1234
def_nboot = 200


class Resampler(object):

    """
    Resampler class within Resample.py

    Takes some xarray data and resamples along the 'configs' dimension (unless otherwise specified)

    """
    def __init__(self,cfg_class=None,resample_info=default_bootstrap_info,rand_list=None):
        self.rand_list = rand_list
        if cfg_class is not None:
            self.ImportCfgData(cfg_class)
        else:
            self.cfg_class = None
        self.resample_info = resample_info
        if resample_info == 'Def':
            resample_info = default_bootstrap_info
        self.ImportInfo(resample_info)

    def ImportInfo(self,this_info):
        if not isinstance(this_info,dict):
            raise IOError('resample_info must be type dictionary')
        if 'type' not in this_info.keys():
            raise IOError('resample_info must have a type (bootstrap or jackknife)')
        if this_info['type'] == 'bootstrap':
            if 'nboot' not in this_info:
                warn('nboot not in info for bootstrap, using default'+str(default_bootstrap_info['nboot']))
                this_info['nboot'] = default_bootstrap_info['nboot']
            if 'n_rand' not in this_info:
                this_info['n_rand'] = default_bootstrap_info['n_rand']
        if this_info['type'] == 'jackknife':
            if 'order' not in this_info:
                warn('order not in info for jackknife, using default'+str(default_jackknife_info['order']))
                this_info['order'] = default_bootstrap_info['order']
        self.this_info = this_info

    def ImportCfgData(self,cfg_class):
        if type(cfg_class).__name__ in da.InheritanceList:
            self.cfg_class = cfg_class
        else:
            ## if its not a BaseData class object, we assume its some data BaseData can format
            self.cfg_class = da.BaseData(data=cfg_class)
        # if 'configs' not in self.cfg_class.data.dims:
        #     print(self.cfg_class.data)
        #     raise EnvironmentError('Class to perform resampling does not contain "configs" as one of the dimensions')
        self.ncfg = self.cfg_class.ncfg

    def ResampleData(self):
        if not hasattr(self,'this_info'):
            raise EnvironmentError('this_info is not set in resampler')
        if 'bootstrap' in self.this_info['type']:
            self.BootStrapData()
        elif 'jackknife' in self.this_info['type']:
            self.JackKnifeData()
        else:
            raise TypeError(str(self.this_info['type'])+' not recognised as type of resampling method')

    def ResamplePropData(self):
        if not hasattr(self,'this_info'):
            raise EnvironmentError('this_info is not set in resampler')
        if 'bootstrap' in self.this_info['type']:
            self.BootStrapData(data_type='propagator')
        elif 'jackknife' in self.this_info['type']:
            self.JackKnifeData(data_type='propagator')
        else:
            raise TypeError(str(self.this_info['type'])+' not recognised as type of resampling method')

    def JackKnifeData(self,data_type='data'):
        raise NotImplementedError('Jackknife not implemeted yet TODO!!!!')

    def BootStrapData(self,data_type='data'):
        if isinstance(self.this_info['n_rand'],str):
            self.this_info['n_rand'] = self.ncfg
        if self.cfg_class is None:
            raise EnvironmentError('cfg_class not initilised before computing BootStrapData')
        myseed=startseed*self.this_info['n_rand']//self.this_info['nboot']
        # self.Avg = np.average(self.values)
        if not isinstance(self.rand_list,np.ndarray):
            np.random.seed(myseed)
            self.rand_list = np.random.randint(0,high=self.ncfg,size=(self.this_info['nboot'],self.this_info['n_rand']))

        this_iter = enumerate(self.rand_list)
        icb,iboot = next(this_iter)
        def Vector_BS(val):
            return val[iboot].mean()
        this_data = getattr(self.cfg_class,data_type)
        output_dataset = xr.apply_ufunc(Vector_BS,this_data,
                        input_core_dims=[['configs']],
                        vectorize=True,dask='parallelized').to_dataset(name=icb)

        for icb,iboot in this_iter:
            def Vector_BS(val):
                return val[iboot].mean()
            output_dataset[icb] = xr.apply_ufunc(Vector_BS,this_data,
                                    input_core_dims=[['configs']],
                                    vectorize=True,dask='parallelized')
        output_dataset.attrs['resample_type'] = 'bootstrap'
        if 'propagator' in data_type:
            self.cfg_class.ImportResamplePropData(output_dataset,resample_type='boot')
        else:
            self.cfg_class.ImportResampleData(output_dataset,resample_type='boot')
        return self.cfg_class
