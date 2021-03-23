# -*- coding: utf-8 -*-
"""
Created on Fri Mar  6 18:43:09 2021

@author: Metin Bicer
"""
from createModels import createModels
from analysis import runAnalysis
from utils import loadModelJRF, saveModelJRF, loadExpJRF
from plot import plotTrial, meanPeakDeviationPlot
from compareResults import compare


# subject's body-weight
BW = 75*9.81
# original, scaled model filename
modelFileName = 'Rajagopal2015-scaled.osim'
# model names given to the modified models depending on the joint whose
# strength has changed
jointModelNames = ['Hip', 'Knee', 'Ankle', 'Full']
# each model has changes in different joint strength
groupNames = {jointModelNames[0]: ['hip_l'],
              jointModelNames[1]: ['walker_knee_l'],
              jointModelNames[2]: ['ankle_l'],
              jointModelNames[3]: ['hip_l', 'walker_knee_l', 'ankle_l']}
# with the percentages
# 0 is for the nominal model for each joint-model
changeAmounts = [-40, -30, -20, -10, 0, 10, 20, 30, 40]
# trial names
trials = ['GC5_ss1', 'GC5_ss3', 'GC5_ss8', 'GC5_ss9', 'GC5_ss11']

# create models
createModels(modelFileName, groupNames, changeAmounts)
# run all trials
runAnalysis(modelFileName, trials)

# save the valid model results
JRF, SO, ACT = saveModelJRF(trials, BW)
# read the valid model results
JRF, SO, ACT = loadModelJRF()
# read experimental JRFs at the knee
expJRF = loadExpJRF(BW)

# plot JRFs for trials
for trial in trials:
    plotTrial(JRF, expJRF, trial)

tWindow = [40, 60] # time window of % gait cycle for comparing models (second peak)
forces = ['hip', 'knee', 'ankle'] # jrfs to be analyzed

# compare JRFs to nominal model
compare(JRF, None, trials, jointModelNames,
        changeAmounts, forces, tWindow)

# compare JRFs to experimental measurements
forcesExp = ['knee'] # compare the magnitude of the knee JRF
compare(JRF, expJRF,
        trials, jointModelNames,
        changeAmounts, forcesExp, tWindow)

# muscle names for SO and ACT
forces = ['iliacus_l', 'recfem_l', 'bfsh_l', 'gasmed_l', 'soleus_l']

# compare SO forces to nominal model
compare(SO, None, trials, jointModelNames,
        changeAmounts, forces, tWindow=[40, 60])

# plot SO forces for a trial
plotTrial(SO, None, 'GC5_ss1', forces=forces, ylim=[-0.01, 2.1], compare='SO')
# plot activations of forces for a trial
plotTrial(ACT, None, 'GC5_ss1', forces=forces, ylim=[-0.02, 1.02], compare='ACT')
# compare activations of forces, and plot a chart showing mean changes
meanPeakDeviationPlot(ACT, trials, jointModelNames,
                      changeAmounts, forces, tWindow=[40, 60], ylim=[-0.3, 0.75])
