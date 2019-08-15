# Data Analysis
To draw conclusions from and analyze the trends in data, we need to be able to aggregate results over multiple data recordings. Analysis addons in Data Atlas serve exactly this function. To create data analysis, following interface needs to be implemented:

```python
class SumAnalysisAddon:
    @staticmethod
    def on(data=[],experiment=None,tag=None):
        return False

    @staticmethod
    def map(data_dict, dev=False):
        return []

    @staticmethod
    def reduce(mapresults, dev=False):
            addon = {
                    "title": "",
                    "subtitle": "",
                    "priority": 1.0,
                    "plot": None,
                    "html": ""
                    }
				return addon
```

## on()
`def on(data=[],experiment=None,tag=None)`

Arguments:
1. *data* - Array of stings. Each string represents name of a available data type.
1. *experiment* - String. Name of the experiment to which the recording belongs.
1. *tag* - String. Single tag of the recording.

Returns:
* *should_run* - Boolean value, True if the analysis should be executed on data recording of specific experiment type with a specific tag and with specified data types available.

The *on* method must do following:
* Return a boolean value.
* Be defined with the `@staticmethod` decorator.

This method determines on which experiments or tags the analysis will be executed. The analysis is executed individually and cannot aggregate over multiple tags or experiment nor can it filter recording using compounding or more complex rules, if you need more flexibility, use [Analysis Groups](analysis-groups.md). The `on()` method can, however, in addition to filtering on one tag or one experiment, filter on data type available on a recording.
### Inclusion Rules
#### Simple Rules
Analysis can be run on a single or a single tag:
```python
def on(data=[],experiment=None,tag=None):
	if experiment=="FirstExperiment"
		return True	
	return False
```
Wich would execute the analysis on all recordings in the "FirstExperiment" experiment. Or:
```python
def on(data=[],experiment=None,tag=None):
	if tag=="FirstTag"
		return True	
	return False
```

#### Multi-Selection Rules
The same analysis can be be run on multiple experiments, for example: 
```python
def on(data=[],experiment=None,tag=None):
	if experiment=="FirstExperiment" or experiment=="SecondExperiment":
		return True	
	return False
```
The code above will run the analysis for both experiment called "FirstExperiment" and "SecondExperiment". Note, however, that the results will not be aggregated over both experiments, each experiment will have it's own independent analysis. Where aggregation is needed, use [Analysis Group](analysis-groups). Similar applies to tags:
```python
def on(data=[],experiment=None,tag=None):
	if tag=="FirstTag" or tag=="SecondTag":
		return True	
	return False
```
would independantly execute analysis for two groups of recordings which have "FirstTag" or "SecondTag". Recordings which both tags would simply contribute to both analysis. Same analysis can also be exeuted on a number of tags and recordings:
```python
def on(data=[],experiment=None,tag=None):
	if tag=="FirstTag" or recording=="FirstExperiment":
		return True	
	return False
```
Again, independent analyses would would be conducted for recordings with the "FirstTag" tag and recordings of the "FirstExperiment" experiment type. Recordings satisfying both rules would contribute to both analyses.

#### Compound Rules
!> Compound rules over multiple recording types and/or tags are not supported by the Data Analysis. Rules such as `tag=="FirstTag" and recording=="FirstExperiment"` would result in the analysis never being executed. To implement analysis with compound selection rules, use [Analysis Group](analysis-groups).

Rules above can be combined along with *data* types available. For example, assuming we have calcium imaging data "ca" and electrophysiology data "ephys", we can only include recordings which have calcium imaging data available using:
```python
def on(data=[],experiment=None,tag=None):
	if "ca" in data and experiment=="FirstExperiment"
		return True	
	return False
```
which would execute the analysis on all recording of the "FirstExperiment" for which calcium data is available. Same can be done to select recordings with both data types recorded:
```python
def on(data=[],experiment=None,tag=None):
	if "ca" in data and "ephys" in data and experiment=="FirstExperiment"
		return True	
	return False
```
!> Be careful when using rules such as `"ca" in data` on their own. This would result in execution of an independent analysis for each and every experiment type for which recordings with calcium data exist and each and every tag contained in any recording with calcium data. This is rarely desired and may result in longer computer times due to large amount of independent analyses which need to be executed.



## map()
`def map(data_dict, dev=False)`

Arguments:
1. *data_dict* - Dictionary with key values representing the data type names specified in `config.py` and values being the instances of the data classes.
2. *dev=False* - Convenience argument which can be set to True to provide additional information when developing a visualization (see below). Should always default to False.

Returns:
1. *data* - Extracted and aggregated data which is to be sent to the `reduce()` method.


The *on* method must do following:
* Return a value readible by the *reduce()* method.
* Be defined with the `@staticmethod` decorator.


The `map()` and `reduce()` methods, as their name suggest, form the map-reduce model: `map()` receives invidual recordings and from each extracts the necessary data, preprocessing it as much as possible and `reduce()` then receives these results to aggregate theme and output the final plot (or report). To save computation resources and processing time, only the minimum amount of data necessary should be returned by the `map()` method.

To simplify the development process, it is possible to use the *dev* argument to alter the functionality when working locally, offering additional logging or displaying the plot rather than dumping a json structure:
```python
if dev:
	plotly.offline.plot(fig)
else:
	plot = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
	plot = json.loads(plot)
```

## reduce()
`def reduce(mapresults, dev=False)`

Arguments:
1. *mapresults* - An array of objects returned by returned by the `map()` method calls.
2. *dev=False* - Convenience argument which can be set to True to provide additional information when developing a visualization (see below). Should always default to False.

Returns:
1. *addon* - The constructed analysis information, see [Analysis Addon structure](data-analysis#analysis-addon-structure) for more information.

The *on* method must do following:
* Return a correctly structured analysis addon definition
* Be defined with the `@staticmethod` decorator.

> See `map()` method above for more information

To simplify the development process, it is possible to use the *dev* argument to alter the functionality when working locally, offering additional logging or displaying the plot rather than dumping a json structure:
```python
if dev:
	plotly.offline.plot(fig)
else:
	plot = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
	plot = json.loads(plot)
```

## Analysis Addon Structure
```python
{
"title": "Some Analysis Title",
"subtitle": "Some Analysis Subtitle",
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

## Data Analysis Registration
To make *datlas* aware of the Data Analysis, it needs to be registered in the `config.py` file:
```python
from some_analysis_addon import SomeAnalysisAddon
...
addons = [SomeAnalysisAddon]
```
