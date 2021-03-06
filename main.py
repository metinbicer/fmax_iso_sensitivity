# -*- coding: utf-8 -*-
"""
Created on Fri Mar  6 18:43:09 2021

@author: Metin Bicer
"""
from createModels import createModels
from analysis import runAnalysis
from utils import loadModelJRF, saveModelJRF, loadExpJRF
from plot import plotTrial
from compareResults import compare

# subject's body-weight
BW = 75*9.81
# original, scaled model filename
modelFileName = 'Rajagopal2015-scaled.osim'
# model names given to the modified models depending on the joint whose
# strength has changed
jointModelNames = ['WeakHip', 'WeakKnee', 'WeakAnkle', 'WeakFull']
# each model has changes in different joint strength
groupNames = {jointModelNames[0]: ['hip'], 
              jointModelNames[1]: ['knee'], 
              jointModelNames[2]: ['ankle'],
              jointModelNames[3]: ['hip', 'knee', 'ankle']}
# with the percentages
# 0 is for the nominal model for each joint-model
changeAmounts = [-40, -30, -20, -10, 0, 10, 20, 30, 40]
# trial names
trials = ['GC5_ss1', 'GC5_ss3', 'GC5_ss8', 'GC5_ss9', 'GC5_ss11']

# create models
createModels(modelFileName, groupNames, changeAmounts)
# run all trials
runAnalysis(modelFileName, trials)

# save the valid models
reactions = saveModelJRF(trials, BW)
# read the valid model JRFs
reactions = loadModelJRF()
# read experimental JRFs at the knee
expReactions = loadExpJRF(BW)

# plot all trials
for trial in trials:
    plotTrial(reactions, expReactions, trial)

tWindow = [40, 60] # time window of % gait cycle for comparing models (second peak)
forces = ['hip', 'knee', 'ankle'] # jrfs to be analyzed

# compare to nominal model
compare(reactions, None, trials, jointModelNames,
        changeAmounts, forces, tWindow)

# compare to experimental measurements
forcesExp = ['knee'] # compare the magnitude of the knee JRF
compare(reactions, expReactions,
        trials, jointModelNames,
        changeAmounts, forcesExp, tWindow)