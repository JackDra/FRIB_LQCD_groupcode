from bokeh.io import curdoc
from bokeh.layouts import gridplot
from bokeh.models import Button
from bokeh_extensions.uploadButton import upload_button

data = {}
plot_series = {}
plot_series_info = {}
file_handels = {}

def initialize_empty():
    from bokeh.plotting import figure
    plot = figure(plot_width=600, plot_height=400)
    return plot


def upload_file(file_name, file_content):
    import xarray as xr    

    data[file_name] = xr.open_dataarray( file_name ) # to improve
    #plot_data_info = {}
    #for dim in [file_name].dims:
    #    plot_data_info[dim] = 0
    #plot_data_info["dim1"] = "x"
    #plot_data_info["dim2"] = "y"
    #plot_series_info[file_name] = plot_data_info

    #plot_series[file_name] = updatePlot(file_name)   

    from bokeh.layouts import widgetbox
    from bokeh.models.widgets import Paragraph
    file_name_text = Paragraph(text=file_name, width=200, height=100)
    
    sliders = generateSliders(file_name)
    file_handels[file_name] = widgetbox([file_name_text] + sliders)

    from bokeh.models.widgets import Slider
    aa = Slider(start=0, end=10, step=1)
    grid = gridplot( [ [plot, aa],  [upload], file_handels.values() ]  )
    curdoc().clear()    
    curdoc().add_root(grid)      

#def update_plot():
#    for key in 

def generateSliders(file_name):
    from bokeh.models.widgets import Slider
    sliders = []
    dataarray = data[file_name]
    for dim in dataarray.dims:
        slider = Slider(start=0, end=dataarray.sizes[dim], step=1)
        #def change_value(attr, old, new):
        #    data
        #slider.on_change("value", change_value)
        slider.title = dim
        sliders.append(slider)
    return sliders



plot = initialize_empty()
upload, source = upload_button(".", upload_file)
grid = gridplot( [ [plot],  [upload], file_handels.values() ]  )
curdoc().add_root(grid)
