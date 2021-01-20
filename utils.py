# -*- coding: utf-8 -*-
"""
Created on Wed Jan 20 09:52:02 2021

@author: metin
"""
import opensim as osim
import numpy as np
import os
from scipy import interpolate
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')
num_plots = 30
colormap = plt.cm.gist_ncar

# jr loads
JR_LOADS = {
    'hip' : np.array(['hip_l_on_femur_l_in_femur_l_fx',
                      'hip_l_on_femur_l_in_femur_l_fy',
                      'hip_l_on_femur_l_in_femur_l_fz',
                      'hip_l_on_femur_l_in_femur_l_mx',
                      'hip_l_on_femur_l_in_femur_l_my',
                      'hip_l_on_femur_l_in_femur_l_mz']),
    'knee': np.array(['knee_l_on_tibia_l_in_tibia_l_fx',
                      'knee_l_on_tibia_l_in_tibia_l_fy',
                      'knee_l_on_tibia_l_in_tibia_l_fz',
                      'knee_l_on_tibia_l_in_tibia_l_mx',
                      'knee_l_on_tibia_l_in_tibia_l_my',
                      'knee_l_on_tibia_l_in_tibia_l_mz']),
    'ankle': np.array(['ankle_l_on_talus_l_in_talus_l_fx',
                     'ankle_l_on_talus_l_in_talus_l_fy',
                     'ankle_l_on_talus_l_in_talus_l_fz',
                     'ankle_l_on_talus_l_in_talus_l_mx',
                     'ankle_l_on_talus_l_in_talus_l_my',
                     'ankle_l_on_talus_l_in_talus_l_mz'])
    }

# converts osim.Storage file into dict of numpy arrays
def stoToNumpy(file):
    storage = osim.Storage(file)
    # number of columns and rows in storage
    numCol = storage.getColumnLabels().getSize()
    numRow = storage.getSize()

    # storage will be saved to dict
    dictStorage = dict()

    # loop through columns
    for col in range(numCol):
        colName = storage.getColumnLabels().get(col)
        # arraydouble to collect the data column from storage
        arr = osim.ArrayDouble()
        # save the column to arr_c
        storage.getDataColumn(colName, arr)
        # loop through rows to save the column
        dictStorage[colName] = np.array([arr.get(row) for row in range(numRow)])

    # return the dictionary containing the numpy arrays
    return dictStorage


# calculate the contact forces from the joint reaction analysis
# jrfileContent is the dictionary containing jr analysis results
# scaling is the scale parameter for the calculated total contact forces
def totalReactionForces(files, scaling=1):
    # a dict to save all reaction forces from the files
    reactionDict = dict()
    for file in files:
        # filename without the path
        fileName = os.path.split(file)[1]
        # check whether the simulation is valid (reserve actuator moments 
        # not exceeding 5% of the ID moments)
        checkSimulation(fileName)
        # forces of a file
        jrDict = stoToNumpy(file)
        for key, data in jrDict.items():
            # normalize to the gait cycle
            jrDict[key] = Normalize2GC(data)
        for joint, forces in JR_LOADS.items():
            # forces in x, y and z
            fx = jrDict[forces[0]]
            fy = jrDict[forces[1]]
            fz = jrDict[forces[2]]
            # the total joint reaction force of the joint
            jrDict[joint] = ((fx**2 + fy**2 + fz**2)**0.5)/scaling
        # save the reaction forces to the dict with the key being the filename
        reactionDict[fileName] = jrDict
    return reactionDict

# normalizes the given data into 0-100 (gaitcycle)
def Normalize2GC(data):
    # normalize data to gait cycle 0-100% (101 points)
    tck = interpolate.splrep(np.linspace(0, 100, len(data)),
                             data,
                             s=0)
    gc = interpolate.splev(np.linspace(0, 100, num=101),
                           tck,
                           der=0)

    return gc


# check whether the SO simulation is valid (compare the reserve forces between
# id and so)
def checkSimulation(jrFileName):
    # get the name of the model and subject and the amount of reduction in max iso
    model, subj, reduction = analysisDetails(jrFileName)
    # so results are saved with this prefix
    analysis = model + '_' + subj + reduction
    soFileName = analysis + '_StaticOptimization_force.sto'
    # full path to the sofile
    soFile = 'Results\\SOResults\\' + soFileName
    # dict containing the so results
    soNumpy = stoToNumpy(soFile)
    # id results filename and dict containing the results
    idFile = 'Results\\' + subj + '\\' + '4_Inverse_Dynamics\\Results\\id_GenForces.sto'
    idNumpy = stoToNumpy(idFile)

    # check hip, knee and ankle reserve actuators
    joints = list(JR_LOADS.keys())
    for idMomentName, idMoment in idNumpy.items():
        # if      is related to one of the joints
        if any(x in idMomentName for x in joints):
            # define the reserve actuator name in so results
            soKey = idMomentName[0:idMomentName.find('_moment')] + '_reserve'
            # if the defined soKey exists
            if soKey in list(soNumpy.keys()):
                # get its value
                soForce = soNumpy[soKey]
                # get the corresponding id force
                maxID = max(np.abs(idMoment))
                # percent difference
                percent = 100*np.abs(soForce)/maxID
            # if the percent difference exceeds 5%, report it
            if max(percent) > 5:
                print(f'{model}, {subj} and {reduction} % reduction: \n',
                      f'Invalid simulation reserve/maxID={max(percent)}')


# splits the joint reaction result filename to get the name of the model, 
# subject (and/or trial) and the amount of reduction in the maximum isometric 
# forces of the muscles
def analysisDetails(jrFileName):
    # model name
    model = jrFileName[0:jrFileName.find('_')]
    # remove model name from the filename
    jrFileName = jrFileName.replace(model+'_','')
    # find the reduction amount (it can be +)
    s = jrFileName.find('+')
    # if not +, try -
    if s == -1: s = jrFileName.find('-')
    # if there is no reduction
    if s == -1:
        reduction = ''
    else:
        # get the reduction amount
        e = jrFileName.find('_', s)
        reduction = jrFileName[s:e]
        jrFileName = jrFileName.replace(reduction,'')
    # subject (and/or trial) name
    subj = jrFileName[0:jrFileName.find('_JR')]
    return model, subj, reduction


# creates figure and returns the handles for the figure and the axes
# to plot the total reaction forces on the hip, knee and ankle
def createFigure(nrows, ncols):
    # create figure and axes with the given number of rows and cols
    fig, axs = plt.subplots(nrows, ncols, sharex=True, sharey=True)
    fig.patch.set_facecolor('white')
    # color cycle for consistent and smooth variation of colors on each axis
    colorCycle = plt.cycler('color', [[0.96345811, 0.0442992 , 0., 1.],
                                      [0.8030303, 0., 0., 1.],
                                      [0.6426025, 0., 0., 1.],
                                      [0.5, 0., 0., 1.],
                                      [1., 0.30573711, 0., 1.],
                                      [1., 0.42193174, 0., 1.],
                                      [1., 0.55265069, 0., 1.],
                                      [1., 0.68336964, 0., 1.],
                                      [1., 0.17501816, 0., 1.]])
    # set some properties of the axes
    for ax in axs.flatten():
        ax.set_prop_cycle(colorCycle)
        ax.set_xlim([0, 100])
        ax.set_facecolor('white')
        ax.set_ylim([0, 6])
    # y labels
    axs[0, 0].set_ylabel('Total Hip JRF [BW]')
    axs[1, 0].set_ylabel('Total Knee JRF [BW]')
    axs[2, 0].set_ylabel('Total Ankle JRF [BW]')
    # x labels
    for ax in axs[-1,:]: ax.set_xlabel('% Gait Cycle')

    return fig, axs