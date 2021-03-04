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
import matplotlib as mpl
import copy
import pandas as pd
from scipy import signal
plt.style.use('fivethirtyeight')

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
def totalReactionForces(fold, scaling=1):
    # jr results folder
    jrResultsFold = fold+'\\JRResults'
    # read the jr result files in the folder
    files = [os.path.join(jrResultsFold, file) for file in os.listdir(jrResultsFold)]
    # a dict to save all reaction forces from the files
    reactionDict = dict()
    for file in files:
        # filename without the path
        fileName = os.path.split(file)[1]
        # check whether the simulation is valid (reserve actuator moments 
        # not exceeding 5% of the ID moments)
        _ = checkSimulation(fold, fileName)
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
            # if the joint is knee, calculate the lateral and medial loads
            if joint.lower() == 'knee':
                tx = jrDict[forces[3]]
                flateral = -0.997*fz + 0.506*(-fy) - 17.9*tx
                fmedial = 0.997*fz+ 0.494*(-fy) + 17.9*tx
                jrDict['lateral'] = np.where(flateral>0, flateral/scaling, 0)
                jrDict['medial'] = np.where(fmedial>0, fmedial/scaling, 0)
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
def checkSimulation(fold, jrFileName):
    printing = False
    # initialize lists
    soNames = []
    idNames = []
    percents = []
    # get the name of the model and subject and the amount of reduction in max iso
    model, subj, reduction = analysisDetails(jrFileName)
    # so results are saved with this prefix
    analysis = model + '_' + subj + reduction
    soFileName = analysis + '_StaticOptimization_force.sto'
    # full path to the sofile
    soFile = fold + '\\SOResults\\' + soFileName
    # dict containing the so results
    soNumpy = stoToNumpy(soFile)
    # id results filename and dict containing the results
    idFile = fold + '\\4_Inverse_Dynamics\\Results\\id_GenForces.sto'
    idNumpy = stoToNumpy(idFile)

    # check hip, knee and ankle reserve actuators
    joints = list(JR_LOADS.keys())
    for idMomentName, idMoment in idNumpy.items():
        # if idMomentName is related to one of the joints
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
                printing = True
                soNames.append(soKey)
                idNames.append(idMomentName)
                percents.append(max(percent))
    # if there is an invalid simulation
    if printing:
        print('{}, {} and {} % change in max iso:'.format(model, subj, reduction))
        for soname, idname, percent in zip(soNames, idNames, percents):
              print('Invalid simulation {}/{}={}'.format(soname, idname, percent))
        print('\n')
        return False
    else:
        return True


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
def createFigure(nrows, ncols, ylabels):
    # create figure and axes with the given number of rows and cols
    fig, axs = plt.subplots(nrows, ncols, sharex=True, sharey=False)
    fig.patch.set_facecolor('white')
    # set some properties of the axes
    for ax in axs.flatten():
        ax.set_xlim([0, 100])
        ax.set_facecolor('white')
        ax.set_ylim([0, 6])
    # y labels
    for r in range(nrows):
        axs[r, 0].set_ylabel(ylabels[r])
    # x labels
    for ax in axs[-1,:]: ax.set_xlabel('% Gait Cycle')

    return fig, axs

# get the current fig and ax
# order labels depending on the max iso percent change
# adjust the subplots
def arrangeFigure():
    # get current fig and ax
    fig, ax = plt.gcf(), plt.gca()
    # get the handles and labels
    handles, labels = ax.get_legend_handles_labels()
    # order the labels
    labelDict = {}
    for label, handle in zip(labels, handles):
        labelDict[label] = handle
    reductions = [int(l[:-1]) if not 'Nom' in l else 0 for l in labels]
    reductions.sort(reverse=False)
    labels = [["", "+"][r>0]+str(r)+'%' if r else 'Nominal' for r in reductions]
    # order the handles accordingly
    handles = [labelDict[label] for label in labels]
    # set the figure legend
    # copy the handles
    handles = [copy.copy(ha) for ha in handles]
    # set the linewidths to the copies
    [ha.set_linewidth(7) for ha in handles ]
    #fig.legend(handles, labels, ncol=len(labels), loc='lower center',
    #           prop={'size': 15}, facecolor='white', edgecolor='white')
    # adjust the subplots
    fig.subplots_adjust(top=0.95, bottom=0.15, wspace=0.2, hspace=0.2)
    

def generateFigure(reactions, rows, cols, ylabels):
    # create the figure template
    fig, axs = createFigure(len(rows), len(cols.keys()), ylabels)
    n_lines = int((len(reactions.keys()) - len(cols.keys()))/len(cols.keys()))
    # for each jr file and its content
    for file, jrf in reactions.items():
        # get the name of the model and the reduction amount
        model, _, reduction = analysisDetails(file)
        reduction, cmap, r, lw, ls = getPlotProps(reduction, n_lines)
        # get the column of the axs for this model
        axCol = axs[:, cols[model]]
        # set its title
        axCol[0].set_title(model)
        # for each row of this column (plot each joint force)
        for ax, row in zip(axCol, rows):
            ax.plot(jrf[row.lower()], label=reduction, c=cmap.to_rgba(r),
                    linewidth=lw, linestyle=ls)
    # arrange figure, axs, labels, positions etc
    arrangeFigure()
    return fig, axs


def getPlotProps(reduction, n_lines):
    r = int(reduction) if reduction else 0
    lw = 1
    ls = '-'
    if r == 0:
        cmap = mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(vmin=1, vmax=n_lines),
                                     cmap=mpl.cm.Greys_r)
        lw = 2
        ls = '-.'
    elif r > 0:
        cmap = mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(vmin=1, vmax=n_lines),
                                     cmap=mpl.cm.Reds)
        r = (abs(r)+30)/10
    else:
        cmap = mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(vmin=1, vmax=n_lines),
                                     cmap=mpl.cm.Blues)
        r = (abs(r)+30)/10
    # reduction is for the label
    if not reduction:
        # if there is no reduction, label='Nominal'
        reduction = 'Nominal'
    else:
        reduction += '%'
    return reduction, cmap, r, lw, ls
