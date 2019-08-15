# Analysis Groups
Analysis groups are more powerful wrappers for [Data Analysis Addons](data-analysis). Unlike the analysis addons, they provide ability to select recordings using compound and more complex rules. Basic structure is as follows:
```python
class AnalysisGroup:
    def on(data,experiment,tags):
        return False

    def addons():
        return []

    def name():
        return ""

    def description():
        return ""
```

## on()
`def on(data,experiment,tags)`

Arguments:
1. *data* - Array of stings. Each string represents name of a available data type.
1. *experiment* - String. Name of the experiment to which the recording belongs.
1. *tag* - Array of strings. All tags of the recording.

Returns:
* *should_run* - Boolean value, True if the analysis should be executed on data recording of specific experiment type with a specific tag and with specified data types available.

This method is called individually on every available recording found. At the time of calling, all available data types have been found and all tags are provided. See [example](analysis-groups#example) below.

## addons()
`def addons()`

Arguments:
* None

Returns:
1. *addons* - List containing classes of the addons which should be applied to this group.

Note that the `on()` method of the analysis addon itself will be ignored. The selection of the data is done by the `on()` method of the Analysis Group.

## name()
`def name()`

Arguments:
* None

Returns:
1. *description* - String containing the name of the analysis group displayed in the web interface

## description()
`def description()`

Arguments:
* None

Returns:
1. *description* - String containing the description of the analysis group displayed in the web interface



## Example
The following example creates an analysis group which will include all recordings in the 'OMR' experiment which have 'plane' and '7dpf' in the tags and have 'ca' and 'ephys' data.

```python
from .addons.first_analysis_addon import FirstAnalysisAddon
from .addons.second_analysis_addon import SecondAnalysisAddon

class SomeAnalysisGroup:
    def description():
        return "This is some analysis group"

    def on(data,experiment,tags):
        if "7dpf" not in tags:
            return False
        if "ca" not in data:
            return False
        if "plane" in tags:
            return False
        if "ephys" in data:
            return False
        if experiment != "OMR":
            return False
        return True

    def addons():
        return [FirstAnalysisAddon,SecondAnalysisAddon]

    def name():
        return "Analysis Group Test"
```
