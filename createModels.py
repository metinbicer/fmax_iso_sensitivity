# -*- coding: utf-8 -*-
"""
Created on Wed Mar  03 14:30:02 2020

@author: metin
"""
import os
import opensim as osim


def createModels(modelFileName='Rajagopal2015-scaled.osim', 
                 groupNames={'WeakHip': ['hip'], 
                             'WeakKnee': ['knee'], 
                             'WeakAnkle': ['ankle'],
                             'WeakFull': ['hip', 'knee', 'ankle']}, 
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
    # get the forceset and its group names
    forceset = osimModel.getForceSet()
    rGroupNames = osim.ArrayStr()
    forceset.getGroupNames(rGroupNames)
    # store the muscle names in each group
    muscleGroups = {}
    for i in range(rGroupNames.getSize()):
        gname = rGroupNames.get(i)
        # no need to store group names for each legs
        if 'leg' not in gname:
            muscleGroup = forceset.getGroup(gname)
            groupMembers = muscleGroup.getPropertyByIndex(0)
            groupMembersStr = groupMembers.toString()
            groupMembersStr = groupMembersStr.split()
            groupMembersStr[0] = groupMembersStr[0][1:]
            groupMembersStr[-1] = groupMembersStr[-1][:-1]
            muscleGroups[gname] = groupMembersStr

    # % change in the reduction of the maximum isometric forces
    for change in changeAmounts:
        # for each model and its muscle groups
        for modelName, groups in groupNames.items():
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
            muscleGroupIndex = []
            muscleGroupNames = []
            # list of muscle names (to be used for changing the max isometric forces)
            muscleNames = []
            for i in range(rGroupNames.getSize()):
                gname = rGroupNames.get(i)
                if any(g in gname.lower() for g in groups):
                    muscleGroup = forceset.getGroup(gname)
                    groupMembers = muscleGroup.getPropertyByIndex(0)
                    groupMembersStr = groupMembers.toString()
                    groupMembersStr = groupMembersStr.split()
                    groupMembersStr[0] = groupMembersStr[0][1:]
                    groupMembersStr[-1] = groupMembersStr[-1][:-1]
                    for name in groupMembersStr:
                        if name not in muscleNames:
                            muscleNames.append(name)
            # a writable reference to the model muscles
            updMuscles = osimModel.updMuscles()
            for name in muscleNames:
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


if __name__ == "__main__":
    createModels()