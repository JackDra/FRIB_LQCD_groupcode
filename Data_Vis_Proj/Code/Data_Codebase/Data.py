#!/usr/bin/env python

import pandas as pa
import xarray as xr
import numpy as np
import os
import pickle as pik
import Resample as rs
from warnings import warn


'''

Module for basic "Data" class

'''

## pulls out the x,y,yerr values for plotting
## kwargs is the same as the kwargs that goes into .sel(...) for xarray dataarrays
def GetPlotVals_Resp(this_xr,**kwargs):
    if 'resample_type' not in this_xr.attrs.keys():
        print(this_xr.attrs)
        raise IOError('this_xr must have resample_type in attrs')
    elif this_xr.attrs['resample_type']+'_config' not in this_xr.dims:
        print(this_xr.dims)
        raise IOError(this_xr.attrs['resample_type']+'_config not in data dims')
    resp_dim = this_xr.attrs['resample_type']+'_config'
    this_sel = this_xr.sel(**kwargs)
    if len([x for x in this_sel.dims if x != resp_dim]) != 1:
        print([x for x in this_sel.dims if x != resp_dim])
        raise IOError('getplotvals must remove all but 1 other dims before plotting')
    mean = this_sel.mean(dim=resp_dim)
    std = this_sel.std(dim=resp_dim).values
    xvals = mean.coords[mean.dims[0]].values
    mean = mean.values
    return xvals,mean,std

def GetPlotVals_Resp_2D(this_xr,**kwargs):
    if 'resample_type' not in this_xr.attrs.keys():
        print(this_xr.attrs)
        raise IOError('this_xr must have resample_type in attrs')
    elif this_xr.attrs['resample_type']+'_config' not in this_xr.dims:
        print(this_xr.dims)
        raise IOError(this_xr.attrs['resample_type']+'_config not in data dims')
    resp_dim = this_xr.attrs['resample_type']+'_config'
    this_sel = this_xr.sel(**kwargs)
    if len([x for x in this_sel.dims if x != resp_dim]) != 2:
        print([x for x in this_sel.dims if x != resp_dim])
        raise IOError('getplotvals 2D must remove all but 2 other dims before plotting')
    mean = this_sel.mean(dim=resp_dim)
    std = this_sel.std(dim=resp_dim).values.flatten()
    xvals = mean.stack(plot_x=(mean.dims[0],mean.dims[1]))
    xvals = xvals.coords[xvals.dims[0]].values
    mean = mean.values.flatten()
    return xvals,mean,std


InheritanceList = ['BaseData','TwoPtCorr','FlowOp']
class BaseData(object):
    """
    BaseData class within Data.py

    contains information and routines for "Data" types.

    These functions will be the generic functions and data
    to be communicated with "holoviews controler class"

    TODO:
        -Plotting via some plotting plane
        -operator overloading
        -Widget maker

    """

    def __init__(self, data=None,file_list=None,**attr_dict):
        self.file_list = pa.DataFrame()
        '''
        columns: file_paths, stream, config_number, (etc...)

        index: configuration number

        '''

        self.data = xr.DataArray([])

        '''
        N dimensional data to reflect the configuraiton data:

        we assume there is a dimension labeled 'configs' for the configuations index
        ImportData takes this into account.

        '''

        self.resampledata = xr.DataArray([])

        '''
        N dimensional data to reflect the resambled data via bootstrapping:

        we assume there is a dimension labeled 'configs' for the configuations index
        ImportData takes this into account.

        '''
        ## list of all the xarray datatypes in the class to be written to file separatly
        self.xrdata_types = ['data','resampledata']
        self.xrdata_wipe = [True,False]

        ## attr_dict will be pulled into BaseData "self" attributes.
        self.__dict__.update(attr_dict)

        if data is not None:
            self.ImportData(data)

        if file_list is not None:
            self.ImportFileList(file_list)
        elif 'data_folder' in attr_dict:
            self.GetFileList()

    def ResampleData(self,resample_info='Def'):
        ## the resampler will take the class object, and add self.resampledata to it
        if isinstance(self.data,str):
            print('Warning, resampling without having data loaded into memory, \
                  loading now')
            self.Load()
        this_resampler = rs.Resampler(cfg_class=self,resample_info=resample_info)
        ## the return type of this is this class itself with the added data in it self.resampledata
        self = this_resampler.ResampleData()

    def ImportResampleData(self,this_data,wipe_configs=False,resample_type=None):
        '''
        Imports the data into the class.
        takes:  xarray.Dataset,     xarray.DataArray
                pandas.DataFrame,   pandas.Series
                list,               numpy.array
        '''
        if isinstance(this_data,xr.DataArray):
            self.resampledata = this_data
        else:
            if resample_type is None:
                raise IOError('resample_type must be set (bootstrap or jackknife) for indexing')
            array_name = resample_type+'_data'
            dim_name = resample_type+'_config'
            if isinstance(this_data,xr.Dataset):
                ## assumes dataset index is for configuraitons
                self.resampledata = this_data.to_array(name=array_name,dim=dim_name)
            elif isinstance(this_data,pa.DataFrame):
                ## dataframe has a column called 'configs', assumes 1D data
                self.resampledata = xr.DataArray(this_data[array_name].values,name=array_name)
            elif isinstance(this_data,pa.Series):
                ## series just pulls the column, assumes 1D data
                self.resampledata = xr.DataArray(this_data.values,name=this_data.name)
                self.resampledata = self.resampledata.rename({self.data.dims[0]:dim_name})
            elif isinstance(this_data,(list,np.ndarray)):
                ## assumes first dimension is the configurations
                this_data = np.array(this_data)
                if isinstance(this_data[tuple(map(int,np.zeros(this_data.ndim)))],list):
                    raise IOError('importing resample data is not tensor')
                self.resampledata = xr.DataArray(this_data)
                self.resampledata = self.resampledata.rename({self.data.dims[0]:dim_name})
            else:
                raise IOError('import resample data type not recognised:' + str(type(this_data)))
            self.resampledata.attrs['resample_type'] = resample_type
        this_xrwipe = self.xrdata_wipe
        this_xrwipe[0] = wipe_configs
        self.Write(wipe_xr=this_xrwipe)

    def ImportData(self,this_data):
        '''
        Imports the data into the class.
        takes:  xarray.Dataset,     xarray.DataArray
                pandas.DataFrame,   pandas.Series
                list,               numpy.array
        '''
        if isinstance(this_data,xr.Dataset):
            ## assumes dataset index is for configuraitons
            self.data = this_data.to_array('configs')
        elif isinstance(this_data,xr.DataArray):
            self.data = this_data
        elif isinstance(this_data,pa.DataFrame):
            ## dataframe has a column called 'configs', assumes 1D data
            self.data = xr.DataArray(this_data['configs'].values,name='configs')
        elif isinstance(this_data,pa.Series):
            ## series just pulls the column, assumes 1D data
            self.data = xr.DataArray(this_data.values)
            self.data = self.data.rename({self.data.dims[0]:'configs'})
        elif isinstance(this_data,(list,np.ndarray)):
            ## assumes first dimension is the configurations
            this_data = np.array(this_data)
            if isinstance(this_data[tuple(map(int,np.zeros(this_data.ndim)))],list):
                raise IOError('importing data is not tensor')
            self.data = xr.DataArray(this_data)
            self.data = self.data.rename({self.data.dims[0]:'configs'})
        else:
            raise IOError('import data type not recognised:' + str(type(this_data)))
        if 'configs' not in self.data.dims:
            raise IOError('data passed in must have a co-ordinate "configs"')
        self.ncfg = self.data.sizes['configs']

    def ImportFileList(self,file_list):
        '''
        Imports the list of paths to configuation data into the class to be read in
        takes:  pandas.DataFrame,   pandas.Series
                list,               numpy.array
        '''
        if isinstance(file_list,pa.DataFrame):
            self.file_list = file_list
        elif isinstance(file_list,pa.Series):
            ## just makes dataframe out of series containing paths to configuations.
            self.file_list = file_list.to_frame('file_paths')
        elif isinstance(file_list,(list,np.ndarray)):
            ## just makes dataframe out of list of paths to configuations
            self.file_list = pa.Series(file_list).to_frame('file_paths')
        else:
            raise IOError('file list type not recognised:' + str(type(file_list)))
        if 'file_paths' not in self.file_list.columns:
            raise IOError('file_paths not found when importing file')


    ## takes data_folder string and creates a pandas dataframe
    ## which includes all file paths
    def GetFileList(self,data_folder='PreDefined'):
        if data_folder !=  'PreDefined':
            self.data_folder = data_folder
        elif not hasattr(self,'data_folder'):
            raise EnvironmentError('data_folder varaible has not been defined before calling GetFileList')


    ## this needs to be generic, make it simple just for debugging perpouses,
    ## it will be extended from child classes.
    def Read(self,delim=' '):
        pass

    def ReadFile(self,this_file,delim=' '):
        pass

    def Read_Previous(self,force_nc_file=None,xr_list='Def'):
        ## reads a previously computed file in 'read_file'
        ## force_nc_file can be used to fix the class if the .p file has been moved
        with open(self.out_file,'rb') as f:
            self.__dict__.update(pik.load(f))
        if force_nc_file is not None:
            self.data = xr.open_dataarray(force_nc_file)
        else:
            if xr_list == 'Def':
                xr_list = self.xrdata_types
            for ixr in xr_list:
                this_dataname = object.__getattribute__(self,ixr)
                if not isinstance(this_dataname,str):continue
                if not os.path.isfile(this_dataname):
                    out_str = 'netcdf file missing, which is referenced by class: \n'
                    out_str += 'read file: \n'
                    out_str += self.out_file + '\n'
                    out_str += 'netcdf file: \n'
                    out_str += this_dataname
                    raise EnvironmentError(out_str)
                setattr(self,ixr,xr.open_dataarray(this_dataname))

    def Load(self,read_file = None,force_nc_file=None,xr_list='Def'):
        ## Load calls Read_Previous if file present, if not calls Read
        if read_file is not None:
            self.out_file = read_file
        elif not hasattr(self,'out_file'):
            print('no read file specified, defaulting back to raw data to read')
            self.Read()
            return
        if self.out_file[-2:] != '.p':
            self.out_file += '.p'
        if os.path.isfile(self.out_file):
            print('found saved file to read')
            print(self.out_file)
            self.Read_Previous(force_nc_file=force_nc_file,
                               xr_list=xr_list)
        else:
            print('output file not found in load, reading in raw data')
            self.Read()

    def Write(self,out_file = None,xr_list='Def',wipe_xr='Def'):
        '''
            Writes its self file in pickle format (in dict form)
            self.data is saved in a separate file as netcdf format,
            which is then refered to as a path in self.data
        '''
        if len(self.data) == 0:
            print('Warning: Writing class that has not data contained')
        if out_file is not None:
            self.out_file = out_file
        elif not hasattr(self,'out_file'):
            warn('No output file define in data, skipping write')
            return
        if self.out_file[-2:] != '.p':
            self.out_file += '.p'
        if xr_list == 'Def':
            xr_list = self.xrdata_types
        if wipe_xr == 'Def':
            wipe_xr = self.xrdata_wipe
        xr_hold_list = [None for _ in xr_list]
        for ic,ixr in enumerate(xr_list):
            if not hasattr(self,ixr): continue
            xr_data = object.__getattribute__(self,ixr)
            if not isinstance(xr_data,str) and len(xr_data) > 0:
                xr_hold_list[ic] = xr_data.copy()
                this_file = self.out_file.replace('.p','_'+ixr+'.nc')
                setattr(self,ixr,this_file)
        with open(self.out_file,'wb') as f:
            pik.dump(self.__dict__,f)
        # if isinstance(self.data,str) :
        for ixr_hold,ixr_wipe,ixr in zip(xr_hold_list,wipe_xr,xr_list):
            if ixr_hold is not None:
                ixr_hold.to_netcdf(object.__getattribute__(self,ixr))
                if not ixr_wipe:
                    setattr(self,ixr,ixr_hold)

    def GetPlotVals_Resp(self,**kwargs):
        if len(self.resampledata) > 0:
            return GetPlotVals_Resp(self.resampledata,**kwargs)
        elif len(self.data) > 0:
            return GetPlotVals_Resp(self.data,**kwargs)
        else:
            raise EnvironmentError('no data present in BaseData instance')

    def GetPlotVals_Resp_2D(self,**kwargs):
        if len(self.resampledata) > 0:
            return GetPlotVals_Resp_2D(self.resampledata,**kwargs)
        elif len(self.data) > 0:
            return GetPlotVals_Resp_2D(self.data,**kwargs)
        else:
            raise EnvironmentError('no data present in BaseData instance')

    def __str__(self):
        ## printing the class shows the name (if defined) and data/resampled data
        out_str = ''
        if hasattr(self,'name'):
            out_str += self.name +' \n'
        if len(self.data) > 0:
            out_str += '     Data:' +' \n'
            out_str += str(self.data) + '\n'
        if len(self.resampledata) > 0:
            out_str += '     Resampled Data:' +' \n'
            out_str += str(self.resampledata) +' \n'
        return out_str

    def __getitem__(self,key):
        #pioritizes resampled data over regular data
        if len(self.resampledata) > 0:
            return self.resampledata[key]
        elif len(self.data) > 0:
            return self.data[key]
        else:
            raise EnvironmentError('cannot __getitem__ if no data is present')

    def __setitem__(self,key,val):
        #pioritizes resampled data over regular data
        if len(self.resampledata) > 0:
            self.resampledata[key] = val
        elif len(self.data) > 0:
            self.data[key] = val
        else:
            raise EnvironmentError('cannot __setitem__ if no data is present')

    # def __getattribute__(self,name):
    #     if name in ['data','resampledata']:
    #         this_object = object.__getattribute__(self,name)
    #         if name == 'data' and isinstance(this_object,str):
    #             object.__getattribute__(self,'Read_Previous')(cfg_data=True,
    #                                                         resample_data=False)
    #         if name == 'resampledata' and isinstance(this_object,str):
    #             object.__getattribute__(self,'Read_Previous')(cfg_data=False,
    #                                                         resample_data=True)
    #     return object.__getattribute__(self,name)



## This is some test data to test the class with.
def TestData():
    ## data_shape is analogous to the dimension of our data (e.g. 5 flow times, 3 tsinks )
    data_shape = [5,3,4,6]
    ncfg = 200
    tot_shape = [ncfg]+data_shape
    tot_len = ncfg*np.prod(data_shape)
    # this_coords = {}
    # for idim,ishape in enumerate(data_shape):
    #     this_coords['dim'+str(idim)] = range(ishape)

    values = np.random.uniform(size=tot_shape)
    values2 = (np.arange(tot_len)/tot_len).reshape(tot_shape)
    values3 = np.random.normal(loc=0.5,scale=0.25,size=tot_shape)
    base_data1 = BaseData(data=values)
    base_data2 = BaseData(data=values2)
    base_data3 = BaseData(data=values3)

    # this_dataset1 = xr.Dataset()
    # this_dataset2 = xr.Dataset()
    # this_dataset3 = xr.Dataset()
    # for icount,(ival1,ival2,ival3) in enumerate(zip(values,values2,values3)):
    #     cfg_str = 'cfg'+str(icount).zfill(4)
    #     this_dataset1[cfg_str] = xr.DataArray(ival1,name=cfg_str,coords=this_coords,dims=list(this_coords.keys()))
    #     this_dataset2[cfg_str] = xr.DataArray(ival2,name=cfg_str,coords=this_coords,dims=list(this_coords.keys()))
    #     this_dataset3[cfg_str] = xr.DataArray(ival3,name=cfg_str,coords=this_coords,dims=list(this_coords.keys()))
    # base_data1 = BaseData(attr_dict={'data':this_dataset1})
    # base_data2 = BaseData(attr_dict={'data':this_dataset2})
    # base_data3 = BaseData(attr_dict={'data':this_dataset3})
    # base_data1 = BaseData(data=this_dataset1)
    # base_data2 = BaseData(data=this_dataset2)
    # base_data3 = BaseData(data=this_dataset3)
    return base_data1,base_data2,base_data3

def TestFN(this_data):
    test_filelist = []
    test_filelist.append('/home/jackdra/LQCD/Scripts/group_meeting/Data_Vis_Proj/TestData/FlowNewForm_sample/RC32x64_Kud01375400Ks01364000-a-/PerGF/q_flow_b1.90_ng2530.out')
    test_filelist.append('/home/jackdra/LQCD/Scripts/group_meeting/Data_Vis_Proj/TestData/FlowNewForm_sample/RC32x64_Kud01375400Ks01364000-a-/PerGF/q_flow_b1.90_ng2560.out')
    this_data.ImportFileList(pa.Series(test_filelist).to_frame('file_paths'))
    return this_data

if __name__ == '__main__':
    # from Data import TestData
    testdata,testdata2,testdata3 = TestData()
    plot_data = testdata.data.sel(dim_1=0,dim_2=0,dim_3=0,dim_4=0).values
    testFNimport = TestFN(testdata)
    my_out_file = 'testdata.p'
    testdata.Write(out_file=my_out_file,wipe_xr=[False,False])
    testload = BaseData()
    testload.Load(read_file=my_out_file)
    testdata.ResampleData()

    this_testdata = testdata.resampledata.sel(dim_1=0,dim_2=0,dim_3=0,dim_4=0)
    xvals,yvals,yvalerr = testdata.GetPlotVals_Resp(dim_1=0,dim_2=0,dim_3=0)
    xvals_2D,yvals_2D,yvalerr_2D = testdata.GetPlotVals_Resp_2D(dim_1=0,dim_3=0)

    base_data = BaseData()
    base_data.Load(read_file='/my/file/name.p')
    print(testdata)
    testdata[0,0,0,0,0]
    testdata.resampledata[0,0,0,0,0]
    testdata.Write()
    object.__getattribute__(testdata,'data')
    testdata.Load()
    object.__getattribute__(testdata,'resampledata')
    testdata.resampledata
