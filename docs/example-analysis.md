# Example of Data Analysis
To draw conclusions from and analize the trends in data, we need to be able to aggregate results over multiple data recordings. Analysis addons in Data Atlas serve exactly this function.

Each analysis addon consists of three methods:
* `on()`,
* `map()`,
* and `reduce()`.

The `on()` method determines on which experiments or tags the analysis will be executed. The analysis is executed individually and cannot aggregate over multiple tags or experiment nor can it filter recording using compounding or more complex rules, if you need more flexibility, use [Analysis Groups](analysis-groups.md). The `on()` method can, however, in addition to filtering on one tag or one experiment, filter on data type available on a recording.

The `map()` and `reduce()` methods, as their name suggest, form the map-reduce model: `map()` receives invidual recordings and from each extracts the necessary data, preprocessing it as much as possible and `reduce()` then receives these results to aggregate theme and output the final plot (or report).

Following on our [Gaussian Data example](python-library-start.md), lets create analysis of the average value the data points in each recordng sum up to. 
```python
import numpy as np
import json
import plotly
import plotly.graph_objs as plygo

class SumAnalysisAddon:
    @staticmethod
    def on(data=[],experiment=None,tag=None):
        if "noise" in data and experiment=="TestExperiment":
            return True
        return False

    @staticmethod
    def map(data_dict, dev=False):
        d = data_dict["noise"]
        s = np.sum(d.data) #Sum the data points
        return s



    @staticmethod
    def reduce(mapresults, dev=False):
        #Here mapresults is array of values returned by the map() method

        #Trace for all datapoints
        trace = plygo.Scatter(
                x = mapresults,
                y = [0]*len(mapresults),
                mode = 'markers',
                name = 'Data Points'
                )

        #Trace for the average
        trace_avg = plygo.Scatter(
                x = [np.mean(mapresults)],
                y = [0],
                mode = 'markers',
                marker = dict(
                    size = 10,
                    color = 'rgba(255, 182, 193, .9)',
                    line = dict(width = 2,)
                    ),
                name = 'Average'
                )


        layout = dict(title = 'Avg. of sums',
                yaxis = dict(zeroline = False),
                xaxis = dict(zeroline = False)
                )
        fig = dict(data=[trace,trace_avg],layout=layout)

        if dev:
            plotly.offline.plot(fig)
        else:
            plot = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            plot = json.loads(plot) #Reencode the data

            addon = {
                    "title": "Avg. sum of random values",
                    "subtitle": "Average sum of random values drawn from a gaussian distribution",
                    "priority": 1.0,
                    "plot": plot,
                    "html": ""
                    }
            return addon
```

We also need to register the analysis in the configuration:
```python
from sum_analysis_addon import SumAnalysisAddon
...
addons = [SumAnalysisAddon]
```

After re-running the data through the Data Atlas, you should see the newly added analysis under the *TestExperiment* experiment.
