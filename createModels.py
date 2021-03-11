# -*- coding: utf-8 -*-
"""
Created on Wed Mar  03 14:30:02 2020

@author: metin
"""
import os
import opensim as osim
from itertools import combinations
import numpy as np


def createModels(modelFileName='Rajagopal2015-scaled.osim', 
                 groupNames={'Hip': ['hip_l'],
                             'Knee': ['walker_knee_l'],
                             'Ankle': ['ankle_l'],
                             'Full': ['hip_l', 'walker_knee_l', 'ankle_l']},
                 changeAmounts=[-40, -30, -20, -10, 0, 10, 20, 30, 40]):
    '''
    creates models with different joint strengths
    
    Parameters
    ----------
    modelFileName: string
        the name of the model whose joint strengths to be changed
    groupNames: dict
        keys are the name of the modified models. Values are the muscle groups
    changeAmounts: list
        amount of percent changes to be applied on the joint strengths
    '''
    print('------------Started creating models------------')
    # where the unmodified models are stored
    modelFold = os.path.join(os.getcwd(), '2_models')
    # its full path
    modelFile = os.path.join(modelFold, modelFileName)
    # load unmodified model
    osimModel = osim.Model(modelFile)
    osimModel.initSystem()
    # get the muscle names
    muscleNames = [osimModel.getMuscles().get(i).getName() for i in range(osimModel.getMuscles().getSize())]
    # find joints spanned by each muscle
    muscleJoints = findJoints(osimModel, muscleNames)
    # % change in the reduction of the maximum isometric forces
    for change in changeAmounts:
        # for each model and its muscle groups
        for modelName, groups in groupNames.items():
            # find muscles to be changed
            musclesChanged = []
            for muscleName, joints in muscleJoints.items():
                 for item in joints:
                    if item in groups:
                 #if any(item in groups for item in joints):
                        musclesChanged.append(muscleName)
            musclesChanged = list(set(musclesChanged))
            # folder for this model group
            modelGroupFold = os.path.join(modelFold, modelName)
            # create a folder for each model group
            if not os.path.isdir(modelGroupFold):
                os.mkdir(modelGroupFold)
            # load unmodified model
            osimModel = osim.Model(modelFile)
            osimModel.initSystem()
            # set the model name depending on the change
            if change == 0:
                osimModel.setName(modelName)
            else:
                osimModel.setName(modelName+["", "+"][change > 0] + str(change))
            # get forcesets to update muscle max isometric forces
            forceset = osimModel.getForceSet()
            rGroupNames = osim.ArrayStr()
            forceset.getGroupNames(rGroupNames)
            # a writable reference to the model muscles
            updMuscles = osimModel.updMuscles()
            for name in musclesChanged:
                muscleAbstract = updMuscles.get(name)
                muscle = osim.Millard2012EquilibriumMuscle().safeDownCast(muscleAbstract)
                # unmodified muscle max isometric force
                previousMaxIsoForce = muscle.getMaxIsometricForce()
                # update the max isometric force
                muscle.setMaxIsometricForce(previousMaxIsoForce*(1+change/100.0))
            # print to a new modelfile
            newModelFile = modelGroupFold + '/' + osimModel.getName()+'.osim'
            osimModel.printToXML(newModelFile)
    print('------------Finished creating models------------')


def findJoints(osimModel, muscleNames):
    # distal body (the last item in the set)
    pairs = findChildParentPairs(osimModel)
    muscleJoints = {}
    for muscleName in muscleNames:
        joints = []
        bodyNames = findBodyNames(osimModel, muscleName)
        bodyPairs = list(combinations(bodyNames, 2))
        for body1, body2 in bodyPairs:
            # first and last bodies in the list
            while body1 != body2:
                try:
                    try:
                        j = pairs.keys()[pairs.values().index([body1, body2])]
                    except:
                        j = pairs.keys()[pairs.values().index([body2, body1])]
                    body2 = body1
                    joints.append(j)
                except:
                    for j, bodies in pairs.items():
                        if body2 == bodies[1]:
                            joints.append(j)
                            body2 = bodies[0]
                            break
        muscleJoints[muscleName] = list(set(joints))
    return muscleJoints


def findChildParentPairs(osimModel):
    pairs = {}
    joints = osimModel.getJointSet()
    for i in range(joints.getSize()):
        thisJoint = joints.get(i)
        pairs[thisJoint.getName()] = [thisJoint.getParentName(),  # parent body
                                      thisJoint.getBody().getName()] # child body
    return pairs


def findBodyNames(osimModel, muscleName):
    thisMuscle = osimModel.getMuscles().get(muscleName)
    ppSet = thisMuscle.getGeometryPath().getPathPointSet()
    bodyNamesSet = np.array([ppSet.get(i).getBody().getName() for i in range(ppSet.getSize())])
    _, idx = np.unique(bodyNamesSet, return_index=True)
    return bodyNamesSet[np.sort(idx)]


if __name__ == "__main__":
    createModels()