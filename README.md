# Requirements
To reproduce the results,
1. download [OpenSim 3.3](https://simtk.org/projects/opensim)
2. have Python installed, preferably [Anaconda](https://www.anaconda.com/)
3. create and activate a virtual environment with Python 2
	**either**
    ```
    conda create --name osim3 python=2.7
    conda activate osim3
	conda install numpy scipy pandas matplotlib scikit-learn
    ```
    **or**
    ```
	conda env create -f environment.yml
	conda activate osim3
    ```
4. setup OpenSim API (please refer to OpenSim [documentation](https://simtk-confluence.stanford.edu/display/OpenSim/Scripting+in+Python)). In the Anaconda Command Prompt, navigate to OpenSim installation folder and run the python script,
    ```
    cd OPENSIM_INSTALLATION_FOLDER\sdk\python
    python setup.py install
    ```
5. clone the repository using the following command on git and change directory to `fmax_iso_sensitivity` folder,
    ```
    git clone https://github.com/metinbicer/fmax_iso_sensitivity.git
    cd fmax_iso_sensitivity
    ```
Note: To use different Python version, you may need to build the OpenSim API from scratch. Further information can be found from the [documentation](https://simtk-confluence.stanford.edu/display/OpenSim/Scripting+in+Python)
# Scripts
The following scripts are used to reproduce the results
| Script name | Script action | Related item in the manuscript|
| --- | --- | --- |
| `main.py` | reproduces the entire work with the user-defined parameters (subject's BW, unmodified scaled model, modified model names, modified joint names, % changes applied to the joint strengths, names of the gait trials. Imports certain functions from the following scripts | N/A |
| `createModels.py` | creates models with different joint strengths. `createModels()` is imported by `main.py`| N/A |
| `analysis.py` | batch processes using inverse dynamics, static optimization and joint reaction analysis. `runAnalysis()` is imported by `main.py` | N/A |
| `utils.py` | utility functions to process, save and load the results of all simulations.  `saveModelResults()`, `loadModelResults()` and `loadExpJRF()` are imported by `main.py` to save and load all simulation results and in-vivo joint loads | N/A |
| `plot.py` | plots results (joint reactions, muscle forces etc.) obtained from simulations with models having different joint strength. In-vivo joint loads can be included. `plotTrial()` and `meanPeakDeviationPlot()` is imported by `main.py` | Figures |
| `compareResults.py` | calculates metrics to compare simulation results from modified models to those obtained using the nominal model or all simulation results to in-vivo joint loads. `compare()` is imported by `main.py`| Tables |
# Run
* In the command prompt, type `python main.py`,
  1. runs inverse dynamics, static optimization and joint reaction analysis for all the data and models.
  2. saves joint reaction forces, muscle forces and activations to `modelJRF.p`, `modelSO.p` and `modelACT.p` for all valid simulations
  3. loads the files saved in step 2, and `eTibia_data.mat` that contains in-vivo knee reaction loads
  4. plots joint reaction forces for each trial in a separate figure, muscle forces and activations for a trial
  5. creates tables comparing simulation results to in-vio loadings, and modified model outputs to nominal results
* If you only want to analyse the previous analyses (saved to `modelJRF.p`), you need to comment out the following lines.  
  [L33](https://github.com/metinbicer/fmax_iso_sensitivity/blob/master/main.py#L33): `createModels(modelFileName, groupNames, changeAmounts)`  
  [L35](https://github.com/metinbicer/fmax_iso_sensitivity/blob/master/main.py#L35): `runAnalysis(modelFileName, trials)`  
  [L38](https://github.com/metinbicer/fmax_iso_sensitivity/blob/master/main.py#L37): `JRF, SO, ACT = saveModelJRF(trials, BW)`  
Then, type `python main.py` in the command window.

# Example figure
![](https://github.com/metinbicer/fmax_iso_sensitivity/blob/master/Figures/GC5_ss1_JRF.png)
