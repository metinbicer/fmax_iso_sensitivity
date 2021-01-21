# -*- coding: utf-8 -*-
"""
Created on Tue Jan  19 14:30:02 2020

-runs multiple so and jr analyses from the GUI.
-run this file from the GUI of OpenSim 3.3.

1. update mainFold (the path to the folder containing this script) which includes username etc.
2. change trial (the name of the folder under mainFold/Results)

@author: metin
"""
import os
#########
# main folder
mainFold = 'C:/Users/metin/Desktop/PhD/MaxIso_ESB'
# name of the folder that contains the gait trial
trial = 'GC5_ss1'
#########
resultsFolder = 'Results'
# define the folder fullpath
analysisFold = mainFold + '/' + resultsFolder
trialFold = analysisFold + '/' + trial
# id folder
idFold = trialFold + '/4_Inverse_Dynamics'
# get the model (this is unmodified scaled version of the model)
modelFile = idFold + '/scaled.osim'
ikFile = idFold + '/ik.mot'
grfFile = idFold + '/grf.mot'
# read files
ik = modeling.Storage(ikFile)
grf = modeling.Storage(grfFile)
# read the original (scaled) model
osimModel = modeling.Model(modelFile)
osimModel.initSystem()
# xml files
forcesetFile = mainFold + '/Forceset.xml'
externalLoadsFile = mainFold + '/ExternalLoads.xml'
# get the ExternalLoads object to write the exact path of the grfFile
extLoads = modeling.ExternalLoads(osimModel, externalLoadsFile)
extLoads.setDataFileName(grfFile)
externalLoadsFile = trialFold + '/ExternalLoads.xml'
# print the external loads under trialFold
extLoads.print(trialFold + '/ExternalLoads.xml')
# get the SO analysis
soAnalysisFile = mainFold + '/SO_Analysis.xml'
soAnalysis = modeling.StaticOptimization()
soAnalysis.setStartTime(grf.getFirstTime())
soAnalysis.setEndTime(grf.getLastTime())
# folders
soResultFolder = trialFold + '/SOResults'
jrResultFolder = trialFold + '/JRResults'
# create results folders
if not os.path.isdir(soResultFolder):
    os.mkdir(soResultFolder)
if not os.path.isdir(jrResultFolder):
    os.mkdir(jrResultFolder)
# create a soTool (this will be updated for each analysis)
soTool = modeling.AnalyzeTool()
soTool.getAnalysisSet().adoptAndAppend(soAnalysis)
soTool.setInitialTime(grf.getFirstTime())
soTool.setFinalTime(grf.getLastTime())
forcesetFileStr = modeling.ArrayStr()
forcesetFileStr.append(forcesetFile)
soTool.setForceSetFiles(forcesetFileStr)
soTool.setExternalLoadsFileName(externalLoadsFile)
soTool.setCoordinatesFileName(ikFile)
soTool.setLowpassCutoffFrequency(6)
soTool.setResultsDir(soResultFolder)

# create a jr analysis (this will be updated for each analysis)
jrAnalysis = modeling.JointReaction()
jrAnalysis.setName('JR')
jrAnalysis.setStartTime(grf.getFirstTime())
jrAnalysis.setEndTime(grf.getLastTime())
# joint reactions to be calculated for jointNames exerted on
# onBodies and expressed in inFrame
jointNames = modeling.ArrayStr()
onBodies = modeling.ArrayStr()
inFrame = modeling.ArrayStr()
jrJointNames = ['hip_r', 'knee_r', 'ankle_r', 'hip_l', 'knee_l', 'ankle_l']
jrOnBodies = ['child', 'child', 'child', 'child', 'child', 'child']
jrInFrame = jrOnBodies
for joint, body, frame in zip(jrJointNames, jrOnBodies, jrInFrame):
    jointNames.append(joint)
    onBodies.append(body)
    inFrame.append(frame)
jrAnalysis.setOnBody(onBodies)
jrAnalysis.setInFrame(inFrame)
jrAnalysis.setJointNames(jointNames)
# create a jr tool (this will be updated for each analysis)
jrTool = modeling.AnalyzeTool()
jrTool.setResultsDir(jrResultFolder)
jrTool.setInitialTime(grf.getFirstTime())
jrTool.setFinalTime(grf.getLastTime())
jrTool.setExternalLoadsFileName(externalLoadsFile)
jrTool.setCoordinatesFileName(ikFile)
jrTool.setLowpassCutoffFrequency(6)

# keys are the model names and values are the joint names (that are
# used to obtain muscle groups crossing these joints)
groupNames = {'WeakHip': ['hip'],
              'WeakKnee': ['knee'],
              'WeakAnkle': ['ankle'],
              'WeakFull': ['hip', 'knee', 'ankle']}
# % change in the reduction of the maximum isometric forces
for change in [10, 20, 30, 40, 60, 0, -10, -20, -30, -40, -60]:
    # for each model and its muscle groups
    for modelName, groups in groupNames.items():
        # load unmodified model
        osimModel = modeling.Model(modelFile)
        osimModel.initSystem()
        # set the model name depending on the change
        if change == 0:
            osimModel.setName(modelName+'_'+trial)
        else:
            osimModel.setName(modelName+'_'+trial+["", "+"][change > 0] + str(change))
        # get forcesets to update muscle max isometric forces
        forceset = osimModel.getForceSet()
        rGroupNames = modeling.ArrayStr()
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
            muscle = modeling.Millard2012EquilibriumMuscle().safeDownCast(muscleAbstract)
            # unmodified muscle max isometric force
            previousMaxIsoForce = muscle.getMaxIsometricForce()
            # update the max isometric force
            muscle.setMaxIsometricForce(previousMaxIsoForce*(1+change/100.0))
        # print to a new modelfile
        newModelFile = trialFold + '/' + osimModel.getName()+'.osim'
        osimModel.print(newModelFile)
        # set soTool attribs depending on this new model
        soTool.setName(osimModel.getName())
        soTool.setModelFilename(newModelFile)
        # print the soTool (prints to the OpenSim installation directory (C:\OpenSim 3.3)
        soTool.print('so.xml')
        # create a new soTool from the printed xml
        soTool_run = modeling.AnalyzeTool('so.xml')
        soTool_run.run()
        
        # jrAnalysis
        jrAnalysis.setForcesFileName(soResultFolder + '/' + osimModel.getName() + '_StaticOptimization_force.sto')
        # set jrtool attribs depending on this new model
        jrTool.setModelFilename(newModelFile)
        jrTool.getAnalysisSet().adoptAndAppend(jrAnalysis)
        jrTool.setName(osimModel.getName())
        # print the jrTool (prints to the OpenSim installation directory (C:\OpenSim 3.3)
        jrTool.print('jr.xml')
        # create a new soTool from the printed xml
        jrTool_run = modeling.AnalyzeTool('jr.xml')
        jrTool_run.run()
