# Synopsis

This is the forecasting and analytics engine for Project Nantum. 
It is intended to provide:

* Building BMS start-up recommendations
* Building electric usage forecasts 
* Building occupancy forecasts
* Building water usage forecasts

# Code Example

The project is organized as a series of subpackages, each
corresponding to one directory. Directory names indicate either the analytics
model implemented in its modules, or the type of data its modules
manipulate and forecast. For example, the electric directory 
will have modules related to steam forecasting, the Random Forest 
directory will have modules related to building a Random Forest model, 
and so on.

The directories dealing with model building and execution (random_forest,
svm, and sarima) have:

* run.py : Entry point for the modules in the directory
* model.py : Model-related code

The remaining directories house utility scripts related to data pulling,
parsing, migration, and munging, and are dependencies of the model 
building modules.

The entry point for running all the forecasts is located at 
`$AN_PREDICTIONS_ROOT/larkin/run.py`

# Installation

* [Install the Python 2.7 version of 
Anaconda 2.5.0 (64-bit)](https://www.continuum.io/downloads).
* Download the desired release of the analytics suite from 
[https://github.com/
PrescriptiveData/
an_predictions/releases](https://github.com/PrescriptiveData/an_predictions/releases)
to your local hard drive.
* From a bash shell, run `pip install $AN_PREDICTIONS_ROOT`.


# Execution

Once installation is successful, execute `run_analytics` in a bash shell 
(it is automatically added to your `PATH` environment variable 
by the installation process). 

NEW: 

* For options, execute `run_analytics -h`. You will find some goodies :).

* Please make sure to copy over the test weather database (history and forecasts
collections) currently being used
by analytics. We have built an archive of forecast data that is required for
the feature of running previous predictions to work properly.
 
* After installation, please setup a scheduler to
execute the `$AN_PREDICIONS_ROOT/larkin/weather/run.py` script
every 15 minutes, in order to continue adding weather data to the historical
and forecast collections. Failing to do so may result in the failure of 
the 'previous prediction' feature for certain dates.

# Tests

TODO

# Contributors

* [David Karapetyan](mailto:dkarapetyan@prescriptivedata.io)
* [James Kelleher](mailto:jkelleher@prescriptivedata.io)
* [Ashish Gagneja](mailto:agagneja@prescriptivedata.io)
* [Ricardo Cid](mailto:agagneja@prescriptivedata.io)

# License

Proprietary
