# -*- coding: utf-8 -*-
"""
Created on Tue Jan  19 14:30:02 2020

@author: metin
"""
import os
# main folder
mainFold = 'C:/Users/metin/Desktop/PhD/MaxIso_ESB'
# method (WeakHip, WeakKnee, WeakAnkle, WeakFull)
resultsFolder = 'Results'
# define the folder fullpath
analysisFold = mainFold + '/' + resultsFolder
# name of the folder that contains the gait trial
trial = 'GC5_ss1'
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
# model
osimModel = modeling.Model(modelFile)
osimModel.initSystem()
# xml files
forcesetFile = mainFold + '/Forceset.xml'
externalLoadsFile = mainFold + '/ExternalLoads.xml'
extLoads = modeling.ExternalLoads(osimModel, externalLoadsFile)
extLoads.setDataFileName(grfFile)
externalLoadsFile = trialFold + '/ExternalLoads.xml'
extLoads.print(trialFold + '/ExternalLoads.xml')
soAnalysisFile = mainFold + '/SO_Analysis.xml'
soAnalysis = modeling.StaticOptimization()
soAnalysis.setStartTime(grf.getFirstTime())
soAnalysis.setEndTime(grf.getLastTime())
# folders
soResultFolder = analysisFold + '/SOResults'
jrResultFolder = analysisFold + '/JRResults'

# soTool
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

#jranalysis
jrAnalysis = modeling.JointReaction()
jrAnalysis.setName('JR')
# names
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
jrAnalysis.setStartTime(grf.getFirstTime())
jrAnalysis.setEndTime(grf.getLastTime())
jrAnalysis.setOnBody(onBodies)
jrAnalysis.setInFrame(inFrame)
jrAnalysis.setJointNames(jointNames)
# jrtool
jrTool = modeling.AnalyzeTool()
jrTool.setResultsDir(jrResultFolder)
jrTool.setInitialTime(grf.getFirstTime())
jrTool.setFinalTime(grf.getLastTime())
jrTool.setExternalLoadsFileName(externalLoadsFile)
jrTool.setCoordinatesFileName(ikFile)
jrTool.setLowpassCutoffFrequency(6)

groupNames = {'WeakHip': ['hip'],
              'WeakKnee': ['knee'],
              'WeakAnkle': ['ankle'],
              'WeakFull': ['hip', 'knee', 'ankle'],
              'WeakFlexExt': ['flex', 'ext', 'ankle']
              }

for change in [10, 20, 30, 40, 0, -10, -20, -30, -40]:
    for method, groups in groupNames.items():
        osimModel = modeling.Model(modelFile)
        osimModel.initSystem()
        if change == 0:
            osimModel.setName(method+'_'+trial)
        else:
            osimModel.setName(method+'_'+trial+["", "+"][change > 0] + str(change))
        forceset = osimModel.getForceSet()
        rGroupNames = modeling.ArrayStr()
        forceset.getGroupNames(rGroupNames)

        muscleGroupIndex = []
        muscleGroupNames = []
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

        updMuscles = osimModel.updMuscles()
        newForces = []
        for name in muscleNames:
            muscleAbstract = updMuscles.get(name)
            muscle = modeling.Millard2012EquilibriumMuscle().safeDownCast(muscleAbstract)
            
            previousMaxIsoForce = muscle.getMaxIsometricForce()
            newForces.append(previousMaxIsoForce*(1+change/100.0))
            muscle.setMaxIsometricForce(previousMaxIsoForce*(1+change/100.0))
    
        newModelFile = trialFold + '/' + osimModel.getName()+'.osim'
        osimModel.print(newModelFile)
        soTool.setName(osimModel.getName())
        soTool.setModelFilename(newModelFile)
        soTool.print('a.xml')
        soTool_run = modeling.AnalyzeTool('a.xml')
        soTool_run.run()
        
        # jrAnalysis
        jrAnalysis.setForcesFileName(soResultFolder + '/' + osimModel.getName() + '_StaticOptimization_force.sto')
        # jrtool
        jrTool.setModelFilename(newModelFile)
        jrTool.getAnalysisSet().adoptAndAppend(jrAnalysis)
        jrTool.setName(osimModel.getName())
        jrTool.print('b.xml')
        jrTool_run = modeling.AnalyzeTool('b.xml')
        jrTool_run.run()
