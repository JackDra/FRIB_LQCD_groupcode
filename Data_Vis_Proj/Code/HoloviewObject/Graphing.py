import numpy as np
import holoviews as hv
hv.extension('bokeh')

xs = [0.1* i for i in range(100)]
curve =  hv.Curve((xs, [np.sin(x) for x in xs]))
scatter =  hv.Scatter((xs[::5], np.linspace(0,1,20)))

def GraphMaker():
    Graph = curve * Scatter
    return Graph 
