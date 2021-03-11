# -*- coding: utf-8 -*-
"""
Created on Thu Feb 25 11:20:40 2021

@author: Metin Bicer
"""
import numpy as np
from sklearn.metrics import r2_score
from utils import analysisDetails
import collections

FORCE_LABELS = ['hip', 'ankle', 'knee', 'lateral', 'medial']


def compare(reactions, expReactions=None, 
            trials=['GC5_ss1', 'GC5_ss8', 'GC5_ss9', 'GC5_ss11'],
            jointModelNames=['Hip', 'Knee', 'Ankle', 'Full'],
            changeAmounts=[-40, -30, -20, -10, 0, 10, 20, 30, 40],
            forces=['hip', 'knee', 'ankle'], tWindow=[40, 60]):
    '''
    compare the model JRFs to
        nominal model JRFs if expReactions==None
    OR 
        in-vivo JRFs if expReactions!=None
    
    Parameters
    ----------
    reactions       : JRFS are stored in a dict whose keys are the trials
    expReactions    : in-vivo JRFs
    trials          : trial names 
    jointModelNames : names of the models (keys of groupNames)
    changeAmounts   : amount of percent changes to be applied on the jointModel strengths
    forces          : JRF names
    tWindow         : time window of % gait cycle for comparing JRFs (peak deviations)
    '''
    # dict contains different metrics 
    fullMetrics = {'rmse': {},
                   'PeakPercent': {}, # percent variation at the peak
                   'PeakVal': {}, # value of the difference at the peak
                   'r2': {}}

    # if expReactions isnt given, compare the modified models against nominal
    # and expReactions for each trial should be None
    if expReactions == None:
        diff = 'nominal model'
        expReactions = {trial:None for trial in trials}
    else:
        diff = 'in-vivo' # string to be printed if expReactions!=None

    # each model (e.g. jointModel='Hip' --> Fisos of muscles crossing the hip are changed)
    for jointModel in jointModelNames:
        # for this model, instantiate a dict (to store each force) for each metric
        for metricName, met in fullMetrics.items():
            fullMetrics[metricName][jointModel] = {r:{f:[] for f in forces} for r in changeAmounts}
        # compute the metrics for each trial
        for trial in trials:
            jointModel_trial_metrics = getMetrics(reactions[trial], expReactions[trial],
                                                  jointModel, forces, tWindow)
            # append each metric 
            for change, changeMetric in jointModel_trial_metrics.items():
                for metricName, met in fullMetrics.items():
                    for force, val in changeMetric[metricName].items():
                        fullMetrics[metricName][jointModel][change][force].append(val)
    # print a table for each metric
    for metricName, metric in fullMetrics.items():
        text = '\t\t\t\t{} (Differences from the {} across trials)\n'.format(metricName, diff)
        text += '\t\t\t{} (mean-std)\t\t\t'.format(forces[0])
        if len(forces)>1:
            for force in forces[1:]:
                text += '{} (mean-std)\t\t\t'.format(force)
        text += '\n'
        # mean and std of each metric
        for jointModel in jointModelNames:
            for change in changeAmounts:
                text += '{:3} {}:\t'.format(change, jointModel)
                for force in forces:
                    metricTrials = np.array(metric[jointModel][change][force])
                    text += '\t{:.2f}\t{:.2f}\t|\t'.format(np.mean(metricTrials),
                                                           np.std(metricTrials))
                text += '\n'
        print(text)


def getMetrics(reactions, expReactions=None,
               jointModel='knee', forces=FORCE_LABELS, tWindow=[40, 60]):
    '''
    creates a dict containing the metrics to compare the model JRFs to
        nominal model JRFs if expReactions==None
    OR 
        in-vivo JRFs if expReactions!=None
    
    Parameters
    ----------
    reactions       : model JRFS
    expReactions    : in-vivo JRFs
    jointModel      : name of the joints whose strength has changed
    forces          : jointModel reaction forces
    tWindow         : time window of % gait cycle for comparing JRFs (peak deviations)
    
    Return
    ----------
    metrics:        :
    '''
    model = {}
    # for each result
    for file, aResult in reactions.items():
        modelName, subj, red = analysisDetails(file)
        if jointModel.lower() in modelName.lower():
            if not red:
                # nominal model JRFs
                model[0] = aResult
            else:
                model[int(red)] = aResult
    od = collections.OrderedDict(sorted(model.items()))
    if expReactions == None:
        # if model comparison, nominal is the nominal model JRFs
        nominal = od[0]
    else:
        # if in-vivo comparison, nominal is the experimental JRFs
        nominal = expReactions
    metrics = {}
    for red, modified in od.items():
        # calculate metrics
        peakVal, peakPer = getPeakError(modified, nominal, forces, tWindow)
        metrics[red] = {'rmse': getRMSE(modified, nominal, forces),
                        'r2'  : getR2(modified, nominal, forces),
                        'PeakVal': peakVal,
                        'PeakPercent': peakPer,
                        }
    # return the resultant dicts containing the metrics
    return metrics


# calculate R^2 (coefficient of determination) between two dicts
# for each force in the dicts
def getR2(modified, nominal, forces=FORCE_LABELS):
    R2Dict = dict()
    for force in forces:
        R2Dict[force] = r2_score(nominal[force], modified[force])
    
    return R2Dict

# calculate peak differences between two dicts
# for each force in the dicts at the given time window
def getPeakError(modified, nominal, forces=FORCE_LABELS, tWindow=[40, 60]):
    peakVal = dict() # peak value difference
    peakPercent = dict() # percent peak difference
    for force in forces:
        m1 = np.max(np.abs(modified[force][tWindow[0]:tWindow[1]])) # peak value-1 (modified)
        m2 = np.max(np.abs(nominal[force][tWindow[0]:tWindow[1]])) # peak value-2 (nominal)
        peakVal[force] = m1-m2 # positive if increase 
        peakPercent[force] = 100*(m1-m2)/m2 # wrt nominal
    return peakVal, peakPercent

# calculate RMSE (root-mean square error) between two dicts
# for each force in the dicts
def getRMSE(modified, nominal, forces=FORCE_LABELS):
    rmseDict = dict()
    for force in forces:
        rmseDict[force] = np.sqrt(np.mean((modified[force]-nominal[force])**2))
        
    return rmseDict