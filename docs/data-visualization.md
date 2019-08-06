# Data Visualization
Data Visualization represents an object capable of generating visualizaiton based on specific data input. The main objective of data visualizations is to provide insight into the recording data, for example plotting a trace of the recorded neuron or correlation between recorded sources within the recording. Unline [Data Analysis](data-analysis), Data Visualization does not operate on multiple recordings and only has access to the data of the one particular recording to which it is applied to. The concept of Data Visualization is a recommended design pattern and the user is free to opt for a different way of implementing this concept if it better fits their framework. The suggested implementation is called using `DataVisualization.run(self)` from the `DataType.generate_db_entry()` method as illustrated in [Example Visualziation](example-visualization). The suggested implemention is outline as follows:


```python
class DataVisualization:
    @staticmethod
    def run(data, dev = False):
        visualization = {
                "title": "",
                "subtitle": "",
                "priority": 1.0,
                "plot": {}
                "html": ""
                }
        return visualization
```

## run()
`def run(data, dev = False)`

Arguments:
1. *data* - Instance of a Data Type class on which the visualization should be generated.
2. *dev=False* - Convenience argument which can be set to True to provide additional information when developing a visualization (see below). Should always default to False.

Returns:
1. *visualization* - The constructed visualization information, see [Visualization structure](data-visualization#visualization-structure) for more information.

The *run* method must do following:
* Return a correctly structured visualizaiton definition

The *run* method can do following:
* Use information supplied in *data* to deduce correct visualization information, e.g title, subtitle
* Use information supplied in *data* to construct a valid plot.ly figure representing the data
* Use information supplied in *data* to construct a valid HTML excerpt providing information about the data or additional information.


To simplify the development process, it is possible to use the *dev* argument to alter the functionality when working locally, offering additional logging or displaying the plot rather than dumping a json structure:

```python
if dev:
	plotly.offline.plot(fig)
else:
	plot = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
	plot = json.loads(plot)
```

## Visualization Structure
Each Visualziation represents one card in the details for the particular data type for each recording and follows this structure:
```python
{
	"title": "Some Card Title",
	"subtitle": "Some Card Subtitle",
	"priority": 1.0,
	"plot": {},
	"html": ""
}
```
where
* `"title"` is the required string title of the visualization card,
* `"subtitle"` is the required string subtitle of the visualization card,
* `"priority"` is an upcoming feature specifying the order of visualization with visualizations with higher priorities floating to the top,
* `"plot"` is (currently) required dictionary returned by Plotly. It is highly recommended to encode the Plotly figure to string using `plot = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)` and then re-decoding it using `plot = json.loads(plot)` to avoid encoding problems when the plot is saved into the database.
* `"html"` allowows the display of custom html in the visualization card.
