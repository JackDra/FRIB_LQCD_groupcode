#!/usr/bin/env python

import pandas as pa
import numpy as np
from Data import BaseData,GetPlotVals_Resp
from warnings import warn

'''

Module for TwoPtCorr class, which inherits from BaseData

'''

class TwoPtCorr(BaseData):
    """
    TwoPtCorr class within TwoPointCorr.py

    contains information and routines for two-point correlator types.

    using BaseData routines, we extend and overwrite specific for 2pt corr

    See BaseData for other functions

    """
    def __init__(self,data=None,file_list=None,**attr_dict):
        super().__init__(data=data,file_list=file_list,**attr_dict)
        if not hasattr(self,'meson_or_baryon'):
            warn('meson_or_baryon not passed to TwoPtCorr initialization, assuming baryon')
            self.meson_or_baryon = 'baryon'
        self.xrdata_types += ['effm_data']
        self.xrdata_wipe += [False]

    def ComputeEffMass(self,delta_t=1):
        if len(self.resampledata) == 0:
            print('ComputeEffMass was called before doing resampling, attempting resample now')
            self.ResampleData()
        if 'baryon' in self.meson_or_baryon.lower():
            shift_index = self.resampledata[...,:-1].coords['t_sep']
            self.effm_data = np.log(self.resampledata[...,:-1]/self.resampledata[...,1:].assign_coords(t_sep=shift_index))
            self.effm_data.attrs['resample_type'] = self.resampledata.attrs['resample_type']
        elif 'meson' in self.meson_or_baryon.lower():
            raise NotImplementedError(self.meson_or_baryon + ': Effective mass not implemented yet for Mesons\
                                      (needs numerical solver)')
        else:
            raise EnvironmentError('meson_or_bayron is not set to meson or baryon...')

    def ImportData(self,this_data):
        super().ImportData(this_data=this_data)
        if len(self.data.dims) != 3:
            raise EnvironmentError('Two point correlation function must have 3 dimesions\
                                   configuraitons, momentum and source-sink separation')
        ## we assume ordering of dimensions of configs, moms, tsinks
        mom_dim_label = {self.data.dims[1]:range(self.data.shape[1])}
        tsink_sim_label = {self.data.dims[2]:range(self.data.shape[2])}
        self.data = self.data.assign_coords(**mom_dim_label)
        self.data = self.data.assign_coords(**tsink_sim_label)
        self.data = self.data.rename({self.data.dims[1]:'momentum'})
        self.data = self.data.rename({self.data.dims[2]:'t_sep'})

    # def ImportFileList(self,file_list):
    #     super().ImportFileList(file_list)

    # def GetFileList(self,data_folder='PreDefined'):
    #     super().GetFileList(data_folder=data_folder)

    # def Read(self,delim=' '):
    #     super().Read(delim=delim)

    def ReadFile(self,delim=' '):
        pass

    # def Read_Previous(self,read_file = None,force_nc_file=None):
    #     super().Read_Previous(read_file=read_file,force_nc_file=force_nc_file)

    # def Load(self,read_file = None,force_nc_file=None):
    #     super().Load(read_file=read_file,force_nc_file=force_nc_file)

    # def Write(self,out_file = None):
    #     super().Write(out_file=out_file,xr_list=['data','resampledata','effm_data'])

    def GetPlotEffM_Resp(self,**kwargs):
        if len(self.effm_data) > 0:
            return GetPlotVals_Resp(self.effm_data,**kwargs)
        else:
            raise EnvironmentError('no effm_data present in TwoPointCorr instance')

def CreateC2TestData():
    ## dims are [momentum, state]
    energy_states = np.array([[0.2,0.4,0.8,1.6],
                              [0.25,0.45,0.85,1.65],
                              [0.32,0.52,0.9,1.67],
                              [0.6,0.9,1.1,2.3]])
    coeff_list = np.array([[1,0.5,0.25,0.125],
                           [1,0.7,0.6,0.5],
                           [1,1,1,1],
                           [1,2,5,11],])

    coeff_err_per = 0
    energy_err_per = 2
    ncfg = 100
    nt = 64
    nmom,nstates = energy_states.shape
    coeff_err = np.random.normal(loc=0,scale=coeff_err_per,size=list(coeff_list.shape)+[ncfg])
    energy_states_err = np.random.normal(loc=0,scale=energy_err_per,size=list(energy_states.shape)+[ncfg])
    def exp_fun(it,imom):
        rand_coeff = np.array([iblist+icoeff for iblist,icoeff in zip(coeff_list[imom,:],coeff_err[imom,:,:])])
        rand_err = np.array([np.exp(-iblist*it)*np.exp(-ierr) for iblist,ierr in zip(energy_states[imom,:],energy_states_err[imom,:,:])])
        # rand_err_p1 = np.array([ierr + iblist*(it+1) for iblist,ierr in zip(energy_states,energy_states_err)])
        #     numer = rand_coeff[0]* np.exp(-rand_err[0])
        #     denom = rand_coeff[0]* np.exp(-rand_err_p1[0])
        #     print(np.log(np.mean(numer)/
        #                  np.mean(denom)),np.mean(rand_err[0]))
        return np.sum( rand_coeff* rand_err,axis=0)
    # data_shape = [coeff_list.shape[1],coeff_list.shape[2],6]
    data_shape = [nmom,nstates,nt]
    values = []
    for imom in range(data_shape[0]):
        for it in range(data_shape[2]):
            values.append(exp_fun(it,imom))
    twopt_test_file = '/home/jackdra/LQCD/Scripts/group_meeting/Data_Vis_Proj/Code/IOtests/C2test'
    base_data = TwoPtCorr(data=np.rollaxis(np.array(values).reshape((nmom,nt,ncfg)),2),
                          out_file=twopt_test_file,meson_or_baryon='baryon')
    return base_data

if __name__ == '__main__':
    this_data = CreateC2TestData()
    this_data.ResampleData()
    xvals,yvals,yerrvals = this_data.GetPlotVals_Resp(momentum=0)
    this_data.ComputeEffMass()
    this_data.effm_data.sel(momentum=0).mean('boot_config')
    this_data.effm_data.sel(momentum=0).std('boot_config')
    effm_xvals,effm_yvals,effm_yerrvals = this_data.GetPlotEffM_Resp(momentum=0)
    
