#!/usr/bin/env python

import pandas as pa
import numpy as np
import xarray as xr
from Data import BaseData,GetPlotVals_Resp
from warnings import warn
import Resample as rs

'''

Module for FlowOp class, which inherits from BaseData

'''

class FlowOp(BaseData):
    """
    FlowOp class within FlowedOps.py

    contains information and routines for Flowed Operator types.

    using BaseData routines, we extend and overwrite specific for flowed operators

    See BaseData for other functions

    """
    def __init__(self,data=None,file_list=None,**attr_dict):
        super().__init__(data=data,file_list=file_list,**attr_dict)
        self.xrdata_types += ['propagator','res_prop','effm_data']
        self.xrdata_wipe += [True,False,False]

    def ComputeEffMass(self,delta_t=1):
        if not hasattr(self,'has_t') or not self.has_t:
            raise EnvironmentError('cannot compute effective mass on flowed operator with no times')
        if len(self.res_prop) == 0:
            print('ComputeEffMass was called before doing res_prop construction, attempting resample now')
            self.ComputeProp()
        shift_index = self.res_prop[...,:-1].coords['time']
        self.effm_data = np.log(self.res_prop[...,:-1]/self.res_prop[...,1:].assign_coords(time=shift_index))
        self.effm_data.attrs['resample_type'] = self.res_prop.attrs['resample_type']

    def ComputeProp(self):
        if not hasattr(self,'has_t') or not self.has_t:
            # raise EnvironmentError('cannot compute propagator for flowed operators without times')
            print('data has not time, propagator construction is skipped')
            return
        this_iter = iter(range(list(self.data.shape)[-1]))
        self.propagator = self.data[...,next(this_iter)]*self.data
        for it in this_iter:
            self.propagator += self.data[...,it]*self.data
        self.propagator = self.propagator/list(self.data.shape)[-1]
        # self.ResamplePropData(resample_info=resample_info)

    def ResamplePropData(self,resample_info='Def'):
        if not hasattr(self,'propagator'):
            self.ComputeProp()
        if not hasattr(self,'propagator'):
            raise EnvironmentError('Resample Prop Data failed, does data have time to it?')
        ## the resampler will take the class object, and add self.resampledata to it
        this_resampler = rs.Resampler(cfg_class=self,resample_info=resample_info)
        ## the return type of this is this class itself with the added data in it self.resampledata
        self = this_resampler.ResamplePropData()

    def ResampleData(self,resample_info='Def'):
        super().ResampleData(resample_info=resample_info)
        self.ResamplePropData(resample_info=resample_info)


    def ImportResamplePropData(self,this_data,wipe_configs=False,resample_type=None):
        '''
        Imports the data into the class.
        takes:  xarray.Dataset,     xarray.DataArray
                pandas.DataFrame,   pandas.Series
                list,               numpy.array
        '''
        if isinstance(this_data,xr.DataArray):
            self.res_prop = this_data
        else:
            if resample_type is None:
                raise IOError('resample_type must be set (bootstrap or jackknife) for indexing')
            array_name = resample_type+'_data'
            dim_name = resample_type+'_config'
            if isinstance(this_data,xr.Dataset):
                ## assumes dataset index is for configuraitons
                self.res_prop = this_data.to_array(name=array_name,dim=dim_name)
            elif isinstance(this_data,pa.DataFrame):
                ## dataframe has a column called 'configs', assumes 1D data
                self.res_prop = xr.DataArray(this_data[array_name].values,name=array_name)
            elif isinstance(this_data,pa.Series):
                ## series just pulls the column, assumes 1D data
                self.res_prop = xr.DataArray(this_data.values,name=this_data.name)
                self.res_prop = self.res_prop.rename({self.data.dims[0]:dim_name})
            elif isinstance(this_data,(list,np.ndarray)):
                ## assumes first dimension is the configurations
                this_data = np.array(this_data)
                if isinstance(this_data[tuple(map(int,np.zeros(this_data.ndim)))],list):
                    raise IOError('importing resample data is not tensor')
                self.res_prop = xr.DataArray(this_data)
                self.res_prop = self.res_prop.rename({self.data.dims[0]:dim_name})
            else:
                raise IOError('import resample data type not recognised:' + str(type(this_data)))
            self.res_prop.attrs['resample_type'] = resample_type
        self.Write()


    def ImportData(self,this_data):
        super().ImportData(this_data=this_data)
        if len(self.data.dims) > 3 or len(self.data.dims) < 2:
            raise EnvironmentError('Flowed operator function must have 3 or 2 dimesions\
                                   configuraitons, flow time and (can have) euclidean time')
        self.has_t = len(self.data.dims) == 3
        ## we assume ordering of dimensions of configs, moms, tsinks
        tflow_dim_label = {self.data.dims[1]:range(self.data.shape[1])}
        self.data = self.data.assign_coords(**tflow_dim_label)
        self.data = self.data.rename({self.data.dims[1]:'flow_time'})
        if self.has_t:
            t_sim_label = {self.data.dims[2]:range(self.data.shape[2])}
            self.data = self.data.assign_coords(**t_sim_label)
            self.data = self.data.rename({self.data.dims[2]:'time'})

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
    #     super().Write(out_file=out_file,xr_list=['data','resampledata','res_prop','propagator'])
    #     super().Write(out_file=out_file)

    def GetPlotEffM_Resp(self,**kwargs):
        if len(self.effm_data) > 0:
            return GetPlotVals_Resp(self.effm_data,**kwargs)
        else:
            raise EnvironmentError('no effm_data present in FlowOp instance')

def CreateFlowTestData():
    ## dims are [momentum, state]
    energy_states = np.array([[0.2,0.4,0.8,1.6] for ival in range(10)])
    coeff_list = np.array([[1/ic,0.5,0.25*ic,0.125*ic**2] for ic in range(1,11)])

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
    twopt_test_file = '/home/jackdra/LQCD/Scripts/group_meeting/Data_Vis_Proj/Code/IOtests/Flowtest'
    base_data = FlowOp(data=np.rollaxis(np.array(values).reshape((nmom,nt,ncfg)),2),
                          out_file=twopt_test_file)
    return base_data

if __name__ == '__main__':
    this_data = CreateFlowTestData()
    this_data.ResampleData()
    xvals,yvals,yerrvals = this_data.GetPlotVals_Resp(flow_time=5)
    this_data.ComputeEffMass()
    this_data.effm_data.sel(flow_time=5).mean('boot_config')
    this_data.effm_data.sel(flow_time=5).std('boot_config')
    effm_xvals,effm_yvals,effm_yerrvals = this_data.GetPlotEffM_Resp(flow_time=4)
    
