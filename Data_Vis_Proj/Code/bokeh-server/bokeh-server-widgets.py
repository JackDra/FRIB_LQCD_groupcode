from bokeh.io import curdoc
from bokeh.layouts import gridplot, row, column, widgetbox, layout
from bokeh_extensions.uploadButton import upload_button
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Whisker

import numpy as np

# create the figure plane
figure_plane = figure(plot_width=900, plot_height=600)

# create some random data and a data source
data_x = np.linspace(0,100,100)
data_y = np.random.rand(100)*4+data_x
data_y_err = np.random.rand(100)
source = ColumnDataSource(data=dict(base=data_x, lower=data_y-data_y_err, upper=data_y+data_y_err))

# add the data to the figure
figure_plane.add_layout(Whisker(source=source, base="base", upper="upper", lower="lower"))
figure_plane.circle(x=data_x, y=data_y)

# create widgets...
from bokeh.models.widgets import RangeSlider
slider_xrange = RangeSlider(start=0, end=1000, step=1, value=(2,400))
slider_xrange2 = RangeSlider(start=0, end=1000, step=1, value=(2,400))

# define the handle functions 
def update_xrange(attr, old, new):
    figure_plane.x_range.start=slider_xrange.value[0]
    figure_plane.x_range.end=slider_xrange.value[1]

# assign the functions
slider_xrange.on_change("value", update_xrange)

# add widgets to layout (here you have to add all the widgets you create using
# columns, widgetbox or row to arrange them)
plot_controls = widgetbox(slider_xrange, slider_xrange2)

# create the main plot view
layout = layout( [[figure_plane, plot_controls],  ] )
curdoc().add_root(layout)
