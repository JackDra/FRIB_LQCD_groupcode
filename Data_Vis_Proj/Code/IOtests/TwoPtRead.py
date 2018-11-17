#!/mnt/home/kimjangh/anaconda3/bin/python3.6

import re
import xarray as xr
import numpy as np

def read_meson_Old( filename, read_real=True ):
	flag_gamma=False
	flag_mom=False
	flag=False
	with open(filename,'r') as this_file:
		values =[]
		for line in this_file:
			if "<gamma_value>0</gamma_value>" in line:
				flag_gamma=True
			elif ("<sink_mom_num>0</sink_mom_num>" in line) and (flag_gamma):
				flag_mom=True
			elif flag_gamma and flag_mom and "<mesprop>" in line:
				flag=True
			elif "</mesprop>" in line or "</Shell_Point_Wilson_Mesons>" in line:
				flag_gamma=flag_mom=flag=False
			elif (flag_gamma and flag_mom and flag and "re" in line and read_real) \
				or (flag_gamma and flag_mom and flag and "im" in line and not read_real):
				word= re.split( r'[><]', line)
				values.append(float(word[2]))
	return values


def read_meson( filename, gamma_val=0,sink_mom='0 0 0',read_real=True ):
	flag_gamma=False
	flag_mom=False
	gamma_string = "<gamma_value>"+str(gamma_val)+"</gamma_value>"
	sink_string = "<sink_mom>"+sink_mom+"</sink_mom>"
	with open(filename,'r') as this_file:
		values =[]
		for line in this_file:
			if (flag_gamma and flag_mom) and 	(("<re>" in line and read_real) or \
												 ("<im>" in line and not read_real)):
				word= re.split( r'[><]', line)
				values.append(float(word[2]))
			elif "</mesprop>" in line:
				flag_mom=False
			elif "<sink_mom>" in line:
				flag_mom=flag_gamma and (sink_string in line)
			elif "<gamma_value>" in line:
				flag_gamma = gamma_string in line
			# elif flag_gamma and flag_mom and "<mesprop>" in line:
			# 	flag=True
			elif "</" in line and "Mesons>" in line:
				return values
	return values

def read_meson_gen( filename, gamma_list=[15],sink_mom_list=['0 0 0'],read_cmplx=False ):
	flag_gamma=False
	flag_mom=False
	gamma_string_list = ["<gamma_value>"+str(igamma)+"</gamma_value>" for igamma in gamma_list]
	sink_string_list = ["<sink_mom>"+imom+"</sink_mom>" for imom in sink_mom_list]
	this_mom = None
	this_gamma = None
	with open(filename,'r') as this_file:
		values = []
		if read_cmplx: values_im = []
		for line in this_file:
			if (flag_gamma and flag_mom) and 	(("<re>" in line) or \
												 ("<im>" in line and read_cmplx)):
				word= re.split( r'[><]', line)
				if "<im>" in line:
					values_im.append(float(word[2]))
				else:
					values.append(float(word[2]))
			elif "</mesprop>" in line:
				if flag_gamma and flag_mom:
					if read_cmplx:
						yield this_gamma,this_mom,values,values_im
						values_im = []
					else:
						yield this_gamma,this_mom,values
				values = []
				flag_mom=False
			elif "<sink_mom>" in line:
				flag_mom=flag_gamma and any([isink in line for isink in sink_string_list])
				if flag_mom:
					for imom,mom_out in zip(sink_string_list,sink_mom_list):
						if imom in line:
							this_mom = mom_out
			elif "<gamma_value>" in line:
				flag_gamma = any([igamma in line for igamma in gamma_string_list])
				if flag_gamma:
					for igamma,ig_out in zip(gamma_string_list,gamma_list):
						if igamma in line:
							this_gamma = ig_out
			# elif flag_gamma and flag_mom and "<mesprop>" in line:
			# 	flag=True
			elif "</" in line and "Mesons>" in line:
				return


def read_meson_list(filename, gamma_list=[15],sink_mom_list=['0 0 0'],read_cmplx=False ):
	data = []
	gamma_mom_dict={}
	t_len = None
	if read_cmplx:
		raise NotImplementedError('read_cmplx not implemented yet')
	for igamma,imom,real_list in read_meson_gen(this_file,gamma_list=gamma_list,sink_mom_list=sink_mom_list,read_cmplx=read_cmplx):
		if t_len is None:
			t_len = len(real_list)
		elif t_len != len(real_list):
			out_str = 'length of t values is not consistant in file:\n'
			out_str += filename +'\n'
			out_str += 'At index: \n'
			out_str += ', '.join(str(igamma),imom)+ '\n'
			out_str += 'this t_len is:'+str(len(real_list))+'\n'
			out_str += 'first t_len is:'+str(t_len)+'\n'
			raise IOError(out_str)
		if igamma not in gamma_mom_dict.keys():
			gamma_mom_dict[igamma] = []
		gamma_mom_dict[igamma].append(imom)
		data += real_list
		# print()
		# print('gamma=',igamma)
		# print('mom=',imom)
		# print('t_len=',t_len)
		# print()
		# print('    '+',\n     '.join(map(str,real_list)))
		# print('')
		# print('    '+',\n     '.join(map(str,cmplx_list)))
	first_mom_list = list(gamma_mom_dict.values())[0]
	# first_gamma = gamma_mom_dict.keys()[0]
	for igamma,imom_list in gamma_mom_dict.items():
		if imom_list != first_mom_list:
			out_str = 'Missmatch in momemtum lists for gamma indicies:\n'
			out_str += filename +'\n'
			out_str += 'At index: \n'
			out_str += str(igamma)+ '\n'
			out_str += 'this mom list is:'+imom_list+'\n'
			out_str += 'first mom list is:'+first_mom_list+'\n'
			raise IOError(out_str)
	this_coords = {}
	this_coords['mes_num'] = list(gamma_mom_dict.keys())
	this_coords['momentum'] = list(gamma_mom_dict.values())[0]
	this_coords['sink_time'] = range(t_len)
	data = np.array(data).reshape(len(this_coords['mes_num']),len(this_coords['momentum']),t_len)
	data = xr.DataArray(data,name=filename,coords=this_coords,dims=list(this_coords.keys()))
	return data
# def read_meson_file(filename, gamma_list=[15],sink_mom_list=['0 0 0'],read_cmplx=True):

# if __name__ == '__main__':
this_file = '/home/jackdra/LQCD/Scripts/group_meeting/Data_Vis_Proj/TestData/cfunsg5/RC32x64_Kud01375400Ks01364000/twoptRandT/twoptsm64si16/RC32x64_B1900Kud01375400Ks01364000C1715-a-004010_xsrc102_k1375400_tsrc0sm64si16_nucleon.2cf.xml'
# data = read_meson(this_file,gamma_val=15,sink_mom='2 0 0',read_real=True)
# data

this_mom_list = ['0 0 0','1 0 0','2 0 0']
this_gamma_list = [15,14,13]
data = read_meson_list(this_file, gamma_list=this_gamma_list,sink_mom_list=this_mom_list )

print(data)

print(data.sel(mes_num=15,sink_time=5)+data.sel(mes_num=15,sink_time=7))


data.to_netcdf('/home/jackdra/LQCD/Scripts/group_meeting/Data_Vis_Proj/Code/IOtests/test_2pt.nc')


data2 = xr.open_dataarray('/home/jackdra/LQCD/Scripts/group_meeting/Data_Vis_Proj/Code/IOtests/test_2pt.nc')

data2
