import base64
from bokeh.models import ColumnDataSource, CustomJS
from bokeh.models.widgets import Button

def new_upload_button(save_path,
                      callback,
                      label="Upload Data File"):
    def file_callback(attr, old, new):
        raw_contents = source.data['contents'][0]
        file_name = source.data['name'][0]
        # remove the prefix that JS adds
        prefix, b64_contents = raw_contents.split(",", 1)
        file_contents = base64.b64decode(b64_contents)
        callback(file_name, file_contents)

    source = ColumnDataSource({'contents': [], 'name': []})
    source.on_change('data', file_callback)

    button = Button(label=label, button_type="success")
    button.callback = CustomJS(args=dict(source=source), code=_upload_js)
    return button, source

_upload_js = """
function read_file(filename) {
    var reader = new FileReader();
    reader.onload = load_handler;
    reader.onerror = error_handler;
    // readAsDataURL represents the file's data as a base64 encoded string
    reader.readAsDataURL(filename);
}

function load_handler(event) {
    var b64string = event.target.result;
    source.data = {'contents' : [b64string], 'name':[input.files[0].name]};
    source.change.emit()
}

function error_handler(evt) {
    if(evt.target.error.name == "NotReadableError") {
        alert("Can't read file!");
    }
}

var input = document.createElement('input');
input.setAttribute('type', 'file');
input.onchange = function(){
    if (window.FileReader) {
        read_file(input.files[0]);
    } else {
        alert('FileReader is not supported in this browser');
    }
}
input.click();
"""

from bokeh.io import curdoc
from bokeh.layouts import gridplot
from bokeh.models import Button

def initialize_empty():
    from bokeh.plotting import figure
    plot = figure(plot_width=600, plot_height=400)
    data = {}
    plot_series = {}
    return plot, data, plot_series

plot, data, plot_series = initialize_empty()

def upload_file(file_name, file_content):
    import pandas as pd
    import io as io
    file_data = pd.read_csv(io.StringIO(file_content.decode("utf-8")) )

    data[file_name] = file_data
    plot_series[file_name] = plot.asterisk(data[file_name]["x"], data[file_name]["y"], size=10, color="navy", alpha=0.5)    



upload, source = new_upload_button(".", upload_file)

grid = gridplot( [ [plot],  [upload] ]  )

curdoc().add_root(grid)
