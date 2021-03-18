# -*- coding: utf-8 -*-
"""
Created on Wed Jan 20 09:52:02 2021

@author: metin
"""
import opensim as osim
import numpy as np
import os
from scipy import interpolate
import pandas as pd
from scipy import signal
from scipy.io import loadmat
try:
    import cPickle as pickle
except ImportError:  # Python 3.x
    import pickle

# jr loads
JR_LOADS = {
    'hip' : np.array(['hip_l_on_femur_l_in_femur_l_fx',
                      'hip_l_on_femur_l_in_femur_l_fy',
                      'hip_l_on_femur_l_in_femur_l_fz',
                      'hip_l_on_femur_l_in_femur_l_mx',
                      'hip_l_on_femur_l_in_femur_l_my',
                      'hip_l_on_femur_l_in_femur_l_mz']),
    'knee': np.array(['walker_knee_l_on_tibia_l_in_tibia_l_fx',
                      'walker_knee_l_on_tibia_l_in_tibia_l_fy',
                      'walker_knee_l_on_tibia_l_in_tibia_l_fz',
                      'walker_knee_l_on_tibia_l_in_tibia_l_mx',
                      'walker_knee_l_on_tibia_l_in_tibia_l_my',
                      'walker_knee_l_on_tibia_l_in_tibia_l_mz']),
    'ankle': np.array(['ankle_l_on_talus_l_in_talus_l_fx',
                     'ankle_l_on_talus_l_in_talus_l_fy',
                     'ankle_l_on_talus_l_in_talus_l_fz',
                     'ankle_l_on_talus_l_in_talus_l_mx',
                     'ankle_l_on_talus_l_in_talus_l_my',
                     'ankle_l_on_talus_l_in_talus_l_mz'])
    }

# loads in-vivo JRFs from the saved file (divide it by scaling)
def loadExpJRF(scaling=1):
    # force names in mat file and output dict
    forceNames = {'F_medial': 'medial', 'F_lateral': 'lateral', 'F_total_magnitude': 'knee'}
    try:
        # read the mat file
        mat = loadmat('eTibia_data.mat')
    except:
        print('Exp JRFs are not saved')
    # read the structured mat to dicts
    expJRF = {} # its keys are the trial names in the mat file
    eTibia_data = mat['eTibia_data'] # eTibia_data structure of the mat file
    # for each experiment (e.g. 'GC5'
    for expNo in list(eTibia_data.dtype.names):
        exp = eTibia_data[0,0][expNo][0,0]['ngait_og'][0,0] # mat structure for the experiment (expNo)
        data = exp['data'] # its data
        trial_names = exp['trial_names'][0] # trial names in the exp
        colheaders = exp['colheaders'][0] # column names (forces) in the exp
        # each trial of the exp
        for idx_trial, trial in enumerate(trial_names):
            trial = trial.astype(str)[0] #string
            # find the trial name (e.g. 'ss1')
            s1 = trial.find('_s')
            s2 = trial.find('.')
            trial = trial[s1+1:s2]
            # exp and trial name (e.g. 'GC5_ss1')
            expTrial = expNo + '_' + trial
            # each trial of an experiment is a dict containing the JRFs
            expJRF[expTrial] = {}
            for idx_col, colName in enumerate(colheaders):
                colName = colName[0]
                expJRF[expTrial][forceNames[colName]] = data[:, idx_col, idx_trial]/scaling
    return expJRF


# loads model JRFs from the saved file
# params:
#    saveFile : the name given to the files containing the JRF, SO and ACT
# returns:
#   dicts containing JRF, SO and ACT
def loadModelJRF(loadFile='model'):
    try:
        with open(loadFile + 'JRF.p', 'rb') as fp:
            JRF = pickle.load(fp)
        with open(loadFile + 'SO.p', 'rb') as fp:
            SO = pickle.load(fp)
        with open(loadFile + 'ACT.p', 'rb') as fp:
            ACT = pickle.load(fp)
            return JRF, SO, ACT
    except:
        print('JRFs are not saved')


# reads JRF, SO and ACT of all valid analysis and saves them
# returns JRF, SO and ACT (dict containing trial names as keys, and the values are the all valid analysis)
# params:
#   trials   : list of string (results should be written using folders with the same name as trials)
#   scaling  : the parameter to scale the calculated total reaction forces
#   saveFile : the name given to the files containing the JRF, SO and ACT
def saveModelJRF(trials=['GC5_ss1', 'GC5_ss3', 'GC5_ss8', 'GC5_ss9', 'GC5_ss11'], BW=75*9.81,
                 saveFile='model'):
    # all JRF, SO and ACT are stored in a dict whose keys are the folder names (trials)
    JRF = {}
    SO = {}
    ACT = {}
    for fold in trials:
        # joint reaction forces in a dict whose keys are the filenames (scaling=BW)
        JRF[fold], SO[fold], ACT[fold] = readResultFiles('Results\\'+fold, scaling=BW)
    # store the JRF for each trial
    with open(saveFile + 'JRF.p', 'wb') as fp:
        pickle.dump(JRF, fp, protocol=pickle.HIGHEST_PROTOCOL)
    # store the SO for each trial
    with open(saveFile + 'SO.p', 'wb') as fp:
        pickle.dump(SO, fp, protocol=pickle.HIGHEST_PROTOCOL)
    # store the ACT for each trial
    with open(saveFile + 'ACT.p', 'wb') as fp:
        pickle.dump(ACT, fp, protocol=pickle.HIGHEST_PROTOCOL)
    return JRF, SO, ACT


# calculate the reaction forces from the joint reaction analysis
# JRF, SO, ACT are the dictionaries containing jr analysis, static optimisation
# and activations
# params:
#   fold: contains the JRResults and SOResults subfolders
#   scaling: the parameter to scale the results or calculated variables
def readResultFiles(fold, scaling=1):
    # jr results folder
    jrResultsFold = fold + '\\JRResults'
    # read the jr result files in the folder
    files = [os.path.join(jrResultsFold, file) for file in os.listdir(jrResultsFold)]
    # a dict to save all reaction forces from the files
    JRF = dict()
    SO = dict()
    ACT = dict()
    for file in files:
        # filename without the path
        fileName = os.path.split(file)[1]
        # check whether the simulation is valid (reserve actuator moments 
        # not exceeding 10% of the ID moments)
        check, soDict, soAct = checkSimulation(fold, fileName)
        if check:
            # normalize activations to gait cycle
            for key, data in soAct.items():
                soAct[key] = Normalize2GC(data)
            # normalize so to gait cycle
            for key, data in soDict.items():
                data /= scaling
                soDict[key] = Normalize2GC(data)
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
                    # if the joint is knee, calculate lateral and medial forces
                    tx = jrDict[forces[3]]
                    flateral = -0.997*fz + 0.506*(-fy) - 17.9*tx
                    fmedial = 0.997*fz+ 0.494*(-fy) + 17.9*tx
                    jrDict['lateral'] = np.where(flateral>0, flateral/scaling, 0)
                    jrDict['medial'] = np.where(fmedial>0, fmedial/scaling, 0)
            # save the reaction forces to the dict with the key being the filename
            JRF[fileName] = jrDict
            SO[fileName] = soDict
            ACT[fileName] = soAct
        # if exceeding 10%
        else:
            print('{} not a valid simulation'.format(file))

    return JRF, SO, ACT

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
    analysis = model + reduction + '_' + subj
    soFileName = analysis + '_StaticOptimization_force.sto'
    # full path to the sofile
    soFile = fold + '\\SOResults\\' + soFileName
    # add activations
    soActFile = fold + '\\SOResults\\' + analysis + '_StaticOptimization_activation.sto'
    # dict containing the activations
    soAct = stoToNumpy(soActFile)
    # dict containing the so results
    soNumpy = stoToNumpy(soFile)
    # id results filename and dict containing the results
    idFile = fold + '\id.sto'
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
                # if the percent difference exceeds 10%, except hip_rot, report it
                if max(percent) > 10 and 'hip_rotation' not in soKey:
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
        return False, None, None
    else:
        return True, soNumpy, soAct


# splits the joint reaction result filename to get the name of the model, 
# subject (and/or trial) and the amount of reduction in the maximum isometric 
# forces of the muscles
def analysisDetails(jrFileName):
    # model name
    model = jrFileName[0:jrFileName.find('_')]
    # remove model name from the filename
    jrFileName = jrFileName.replace(model+'_','')
    # find the reduction amount (it can be +)
    s = model.find('+')
    # if not +, try -
    if s == -1: s = model.find('-')
    # if there is no reduction
    if s == -1:
        reduction = ''
    else:
        # get the reduction amount
        reduction = model[s:]
        model = model[:s]
    # subject (and/or trial) name
    subj = jrFileName[0:jrFileName.find('_JR')]
    return model, subj, reduction


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
