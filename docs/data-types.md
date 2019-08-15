# Data Type
Data Type represents a particular type of data which can be analysed, visualized or otherwise represented in the Data Atlas. To define a Data Type, one has to implement a simple class with following minimal structure:

```python
class DataType:
    def __init__(self,base_dir,meta_filename, fill=True):
        if fill:
            self.fill()

    def fill(self):
        pass

    def populate_summary(self, summary):
        return summary

    def generate_db_entry(self):
        entry = {
                "name": "", 
                "summary": {}
                }
        return entry, []


    def get_filename(self):
        return ""
```

The individual methods are described below.

## \_\_init\_\_()
`__init__(self,base_dir,meta_filename, fill=True)`

Arguments:
1. *base_dir* - Directory of where the metadata file was found.
2. *meta_filename* - File name of the metadata file.
3. *fill=True* - `True` if all of the data should be loaded, `False` if only the basic data should be loaded.

Returns:
* Nothing

The constructor must do following:
* Load *ID* of the recording and store it in the class member variable `self.id`
* Load *Experiment Name* of the recording and store it in the class member variable `self.type`
* Load *tags* of the recording and store it in the class member variable `self.tags`
* Call `self.fill()` if *fill* is `True`

It is desirable to load absolute minimum data in the constructor. This avoids frequent slow disk reads and decreases memory footprint of the Data Atlas during exectuion. One may want to store the data in multple files, refer to these files in the metafile and only load them in the `fill()` method. Alternatively parse a necessary part of the file if the format allows it. Fully reading large files in the constructor will likely result in unnecessarily long wait times.

## fill()
`fill(self)`

Arguments:
* None

Returns:
* Nothing

The *fill* method must do following:
* Load all data necessary for the analysis and visualization corresponding to that particular recording

## populate\_summary()
`populate_summary(self, summary)`

Arguments:
1. *summary* - Summary of the whole recording.

Returns:
1. *summary* - The received summary with additional entries.

The *populate\_summary* method must do following:
* Forward *summary* if it is not modifying it

The *populate\_summary* method can do following:
* Add additional entries or override existing ones or othewise modify summary in a way that produces a desirable end result

The main purpose of this method is to aggergate common information about the recording from all information available across all data types. This can be date and time of the recording for example. The Data Atlas starts with empty dictionary `{}` and passes it to a *populate\_summary* method of a first available data type, Then takes the returned result and passes it to the next one and so on. The order in which this is done is unspecified. The format of the *summary* dictionary is specified in the [section regarding Summary](data-types#summary-structure).

## generate\_db\_entry()
`generate_db_entry(self)`

Arguments:
* None

Returns:
1. *entry* - Entry into the database containing details about tbe Data
2. *visualizations* - Array of visualizations. Each visualization follows the [Visualization structure](data-visualization#visualization-structure)

The *generate\_db\_entry* method must do following:
* Return entry specifying the name and summary, see below
* Return empty array or array of one or more dictionaries following the [Visualization structure](data-visualization#visualization-structure)

The main purpose of this method is to extract information specific to the particular data type. Unlike *populate\_summary*, the data reported here should not have a global meaning i.e. it should not be the date, time or the duration of the recording, for example (unless, of course, the individual data comprising the recording is not acquired concurrently). This is done by returning a dictionary with the following format:

```python
{
	"name": "Data Type Name",
	"short_name": "DTN",
	"summary": {}
}
```
* The `"name"` value specifies the name of the data type and is what is displayed as title on the card in the 'Overview' tab of the recording and is required and should not be left empty for disambiguation purposes.
* The `"short_name"` value specifies an abbreviation for the data type name and is what is displayed in the name of the tab for the visualizations specific to that given data type. The value for `"short_name"` is not required and if it is not provided, `"name"` is used instead.
* The `"summary"` value defines the summary specific to the the particular data type. The value has to follow the [Summary structure](data-types#summary-structure).

## get\_filename()
`get_filename(self)`
Arguments:
* None

Returns:
1. *filepath* - String defining where the file loaded is

The *get\_filename* method must do following:
* Return a string, even if empty

This method should return a file name of the data, if at all possible. Generally it is not a bad idea to return the joint `base_dir` and `meta_filename` provided to the constructor. The value returned by this method is inspected by Data Atlas to compile information shown in the 'Details'.

## Summary structure
Summary now officially supports listing key-value pairs and embedding of a youtube video and has following structure:
```python
{
	"entries": [],
	"youtube": ""
}
```
Neither `"entries"` nor `"youtube"` is required.
### Entries
`"entries"` is an array. Each element in the `"entries"` array follows following format:
```python
{
	"icon": "some_icon", 
	"name": "Some Key", 
	"value": "Some Value",
	"list": False
}
```
where 
* `"icon"` is a required string name of a supported icon. Currently only [Material Icons](https://material.io/tools/icons/) are supported.
* `"name"` is a required non-unique name of what the value represents, for exmaple for a Date entry this would be "Date". 
* `"value"` is a required value associated with the name. For example, for a Date entry this would "17. March 2018".
* `"list"` is an optional boolean. This field only takes effect if the *Summary* is in the summary of the recording i.e. in the `populate_summary()` method. By default it is False. When set to True, the value will be listed in the list of recordings, even when listed through Experiment, Tag or Group Analysis details.

**Example**
```python
{ 
	"icon": "date_range", 
	"name": "Date", 
	"value": self.datetime.strftime("%d %b %Y"),
	"list":True
}
```
in `populate_summary()` results in Date entry which is also listed along with other data in the recordings list.

### YouTube
`"youtube"` value is a string which is the youtube video ID. For example, to embed YouTube video [https://www.youtube.com/watch?v=Pbl2-iUAkF0](https://www.youtube.com/watch?v=Pbl2-iUAkF0), one would set `"youtube": "Pbl2-iUAkF0"`. 

## Data Type Registration
To make *datlas* aware of the Data Type, it needs to be registered in the `config.py` file:
```python
from some_data_type import SomeDataType
...
data_types = {
        "type_id" : {
            "dir" : "some_data",
            "class" : SomeDataType
            },
        }
```
where
* `"type_id"` is an unique string by which *datlas* identifies your data. For example in the *data_dict* of the [Data Analysis](data-analysis#map) `map()` will use this string as the key in the key-value pair. For convenience, its suggested to select short but unique strings such as `"ca"` for Calcium Imaging data, `"vr"` for Virtual Reality data and so on.
* `"dir"`is a subdirectory under `dir_data` (see [Configuration](python-library-start#configuration)) where the data of this type can be found.
* `"class"` is a data type class corresponding to the particular data type.
