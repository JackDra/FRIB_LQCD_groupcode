import os as os
import numpy as np
import pandas as pd
import xarray as xr

def tokenizer(fname):
    with open(fname) as f:
        chunk = []
        for line in f:
            if len(line.strip()) == 0:
                yield chunk
                chunk = []
                continue
            chunk.append(line)

def extractData():
    arrays = [np.loadtxt(A) for A in tokenizer('/home/giovanni/Desktop/group_meeting_data/TestData/FlowNewForm_sample/RC32x64_Kud01375400Ks01364000-a-/PerGF/q_flow_b1.90_ng2510.out')]
    obs = pd.DataFrame()
    for mat in arrays:
        obs[mat[0,0]] = mat[1:,1]
    dat = xr.DataArray(obs)
    dat = dat.rename(dim_0="t_eucl", dim_1="t_flow")
    print(dat.sel(t_flow=7.02).sum())
    


if __name__ == "__main__":
    extractData()
