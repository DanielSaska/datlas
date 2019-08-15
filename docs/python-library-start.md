> This guide assumes you have access to working Datlas server, for more information on self-hosting, see [here](quick-start.md) on set up with docker or [here](quick-start-no-docker.md) without docker.
# Using the *datlas* library
Installation using `pip` will be supported in future releases, however for now, you will need to clone the library directly from the repository.
Let's create `test_env` environment and a python virtual environment for testing:
```console 
mkdir test_env
cd test_env
python3 -m virtualenv ./env
source env/bin/activate
git clone https://github.com/DanielSaska/datlas
pip install -r datlas/requirements.txt
mkdir -p data/noise pickles
```
We have also created some directories. `data/noise` is where we will store our data and `pickles` is where the library will store intermediary pickle files.

## Generate some data
First we need some data. For now, lets generate some gaussian noise:
```python
import numpy as np
import json
from bson import objectid

for i in range(10):
    noise = list(np.random.normal(0,1,100))
    json.dump({
        "id": str(objectid.ObjectId()), # Our recording needs an unique ID
        "experiment": "TestExperiment", # Which experiment does this recording belong to
        "tags": ["Testing","Example"], #Some tags for our recording
        "data":noise
        },open("data/noise/example{}_meta.json".format(i),"w"))
```
> In the current version, the file loaded by datlas must end in *meta.json*. This constraint will be released in future releases.

## Importing data
Now we need to get our data into a format which Data Atlas can understand we do this by creating a class in `noise_data_type.py` as follows:

```python
import json
import os

class NoiseDataType:
    def __init__(self,base_dir,meta_filename, fill=True):
        self.base_dir = base_dir
        self.meta_filename = meta_filename

        with open(os.path.join(self.base_dir,self.meta_filename)) as meta_file:
            j = json.load(meta_file)
            self.id = j["id"] #Class must have ID
            self.type = j["experiment"] #Class must have experiment type
            self.tags = j["tags"] #Class must have tags array (can be empty)
            self.data = j["data"]

        if fill:
            self.fill()

    def fill(self):
        pass


    def populate_summary(self, summary):
        return summary


    def generate_db_entry(self):
        entry = {
                "name": "Gaussian Noise", #This is the full name of our data type
                "short_name": "Noise", #Short name (not required)
                "summary": {}
                }
        return entry, []


    def get_filename(self):
        return os.path.join(self.base_dir,self.meta_filename)
```
The additional methods offer more advanced functionality and are described in the [Data Types](/data-types.md) section.

## Configuration

Now we conigure Data Atlas with our newly created data type by creating `config.py`:
```python
from noise_data_type import NoiseDataType

#--- Processing Configuration
n_threads = 4; #Number of threads the data atlas is allowed to run

#--- Connection Configuration
connection = "DIRECT" #For now a direct connetion is the only option
uri_mongodb = "mongodb://localhost:27017/datlas" #When using a direct connection, provide mongodb uri

#--- Data Configuration
dir_data = "./data" #This is where your data lives, requires (at least) read-only access
dir_pickles = "./pickles" #This is where data pickles will be created, requires read-write access

#Data types with their directories and respective data classes
data_types = {
        "noise" : {
            "dir" : "noise",
            "class" : NoiseDataType
            },
        }
addons = []
groups = []
```
We also need to create `commit.sha` which stores the version of our data types and analysis. Data Atlas uses this avoid parsing data which has already been analysed and included in the database. In [Automated Deployment](automated-deployment.md) environment, this file can be created as part of the build but for now lets just manually initialize it to '1' by running `echo 1 >> commit.sha`.


## Run
To let Data Atlas analyze your data, simply use the run function using the configuration you just created:

```python
from datlas.run import run
import config as cfg

run(cfg)
```

Run and that it! Now access DataAtlas from your web browser and you should see your newly added experiments. Follow the next steps to create [data visualizations](example-visualizaiton.md) and [data analysis](example-analysis.md).





