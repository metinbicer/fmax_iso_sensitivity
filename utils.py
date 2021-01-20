# -*- coding: utf-8 -*-
"""
Created on Wed Jan 20 09:52:02 2021

@author: metin
"""
import opensim as osim
import numpy as np
import os

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
    reactionDict = dict()
    for file in files:
        fileName = os.path.split(file)[1]
        jrDict = stoToNumpy(file)
        for joint, forces in JR_LOADS.items():
            fx = jrDict[forces[0]]
            fy = jrDict[forces[1]]
            fz = jrDict[forces[2]]
            jrDict[joint] = ((fx**2 + fy**2 + fz**2)**0.5)/scaling
        reactionDict[fileName] = jrDict
    return reactionDict

