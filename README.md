# Requirements
To reproduce the results,
1. download [OpenSim 3.3](https://simtk.org/projects/opensim)
2. have Python installed, preferably [Anaconda](https://www.anaconda.com/)
**Either use the steps in 3, 4 and 5 OR continue from 6
3. create and activate a virtual environment using Python 2
    ```
    conda create --name osim3 python=2.7
    conda activate osim3
    ```
4. install the following packages,
    * numpy
    * scipy
    * pandas
    * matplotlib
    * scikit-learn
5. setup OpenSim API (please refer to OpenSim [documentation](https://simtk-confluence.stanford.edu/display/OpenSim/Scripting+in+Python)). In the Anaconda Command Prompt, navigate to OpenSim installation folder and run the python script,
    ```
    cd OPENSIM_INSTALLATION_FOLDER\sdk\python
    python setup.py install
    ```
6. Create a virtual environment using environment.yml
	```
	conda env create -f environment.yml
	conda activate osim3
    ```
6. clone the repository using the following command on git,
    ```
    git clone https://github.com/metinbicer/fmax_iso_sensitivity.git
    ```
Note: To use different Python version, you may need to build the OpenSim API from scratch. Further information can be found from the [documentation](https://simtk-confluence.stanford.edu/display/OpenSim/Scripting+in+Python)
# Scripts
The following scripts are used to reproduce the results
| Script name | Script action | Related item in the manuscript|
| --- | --- | --- |
| `main.py` | reproduces the entire work with the user-defined parameters (subject's BW, unmodified scaled model, modified model names, modified joint names, % changes applied to the joint strengths, names of the gait trials. Imports certain functions from the following scripts | N/A |
| `createModels.py` | creates models with different joint strengths. `createModels()` is imported by `main.py`| N/A |
| `analysis.py` | batch processes using inverse dynamics, static optimization and joint reaction analysis. `runAnalysis()` is imported by `main.py` | N/A |
| `utils.py` | utility functions to process, save and load the results of Joint Reaction Analysis on the entire dataset.  `saveModelJRF()`, `loadModelJRF()` and `loadExpJRF()` are imported by `main.py` to save and load joint reaction forces estimated using models and in-vivo knee joint loadings | N/A |
| `plot.py` | plots the joint reaction forces obtained from simulations with models having different joint strength and in-vivo joint loads, for a trial. `plotTrial()` is imported by `main.py` | Figure? |
| `compareResults.py` | calculates metrics to compare the joint reaction forces obtained using the modified models to those obtained using the nominal models or to in-vivo loadings. `compare()` is imported by `main.py`| Table? |
# Run
* In the command prompt, type `python main.py`,
  1. runs inverse dynamics, static optimization and joint reaction analysis for all the data and models.
  2. saves the results to `modelJRF.p`
  3. loads `modelJRF.p` that contains joint reaction forces from the OpenSim simulation, and `eTibia_data.mat` that contains in-vivo knee reaction loads
  4. plots joint reaction forces for each trial in a separate figure
  5. creates a table for the comparison between the modified and nominal model joint loadings
* If you only want to analyse the previous analyses (saved to `modelJRF.p`), you need to comment out the following lines. Then, type `python main.py` in the command window.  
  [L32](https://github.com/metinbicer/fmax_iso_sensitivity/blob/master/main.py#L32): `createModels(modelFileName, groupNames, changeAmounts)`  
  [L34](https://github.com/metinbicer/fmax_iso_sensitivity/blob/master/main.py#L34): `runAnalysis(modelFileName, trials)`  
  [L37](https://github.com/metinbicer/fmax_iso_sensitivity/blob/master/main.py#L37): `reactions = saveModelJRF(trials, BW)`

# Example figure
![](https://github.com/metinbicer/fmax_iso_sensitivity/blob/master/Figures/GC5_ss1_JRF.png)
