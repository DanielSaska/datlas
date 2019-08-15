# Example of Data Visualization
Having data on its own in Data Atlas is not very useful. Lets see how we can visualize the data for inspection. This page continues from where [*datlas* usage](python-library-start.md) left off.

To allow plotting, Data Atlas uses [Plot.ly](https://plot.ly/) libraries. Lets plot the random samples we generated for each of the noise data 'recordings'. To do this, add the following to your `noise_data_type.py`:
```python
import plotly
import plotly.graph_objs as plygo

class BasicVisualization:
    @staticmethod
    def run(data, dev = False):

        fig = plotly.tools.make_subplots(rows=1, cols=1, print_grid=False)
        p_fig = plygo.Scatter(
            name="Random Data",
            y=data.data,
            xaxis='x1',
            yaxis='y1',
            line=dict(color = ('#6bbd46')))



        xaxis=dict(title="Samples")
        yaxis=dict(title="Value")

        main_layout = dict(
            title='',
            margin = dict(t=16,l=64,r=16,b=64),
            showlegend=False,
            xaxis1=dict(xaxis, **dict(domain=[0.0, 1.0], anchor='y1')),
            yaxis1=dict(yaxis, **dict(domain=[0.0, 1.00], anchor='x1')),
        )

        fig = dict(data=[p_fig], layout=main_layout)
        if dev:
            plotly.offline.plot(fig)
        else:
            #Make sure to re-encode using the Plotly encoder to avoid parsing problems
            plot = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            plot = json.loads(plot) #Reencode the data

        visualization = {
                "title": "Gaussian Value", #Title of the card
                #Subtitle of the card
                "subtitle": "The sequence of randomly generated values from a gaussian distribution",
                "priority": 1.0,
                "plot": plot, #The actual plotly structure
                "html": ""
                }
        return visualization
```
and then modify your `generate_db_entry()` method:
```python
    def generate_db_entry(self):
        entry = {
                "name": "Gaussian Noise",
                "short_name": "Noise",
                "summary": {}
                }
        return entry, [BasicVisualization.run(self)]
```

Of course, nothing prevents you from making thsi a method of the `NoiseDataType` itself or even doing the plotting in the `generate_db_entry()` method itself. Also note that if you instantiate the `NoiseDataType` yourself and then call `BasicVisualization.run` with `dev=True` on it, it will plot the figure locally into a html file which is great when you are creating the plots for the first time or you need to troubleshoot.

Accessing the Data Atlas in a web browser after re-running the processing (don't forget to change the `commit.sha` if need be) should give you the plot for the gaussian data:
//TODO

Next, you you will learn about [analyzing the data](example-analysis.md).


