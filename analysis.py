# -*- coding: utf-8 -*-
"""
Created on Tue Jan  19 14:30:02 2020

@author: Metin Bicer
"""
import os
import opensim as osim

def runAnalysis(modelFileName='Rajagopal2015-scaled.osim',
                trials=['GC5_ss1', 'GC5_ss3', 'GC5_ss8', 'GC5_ss9', 'GC5_ss11']):
    '''
    runs multiple id, so and jr analyses in OpenSim 3.3
    
    Parameters
    ----------
    modelFileName : string
        Original (scaled) model filename
    trials        : list of strings
        trial names
    '''
    # xml folder
    xmlFold = '0_xml/'
    # data folder
    dataFold = '1_data/'
    # results folder
    resultsFold = 'Results/'
    if not os.path.isdir(resultsFold):
        os.mkdir(resultsFold)
    # model main folder
    modelFold = '2_models/'
    # original model
    originalModelFile = modelFold + modelFileName
    osimModel = osim.Model(originalModelFile)
    # modified model folders
    modelsubFolds = [x[0] for x in os.walk(modelFold)]
    modelFileNames = []
    modelPaths = []
    for fold in modelsubFolds[1:]:
        for model in os.listdir(fold):
            modelFileNames.append(model)
            modelPaths.append(os.path.join(fold, model))

    # appended forceset
    forcesetFile = xmlFold + '/Forceset.xml'

    for trial in trials:
        ikFile = dataFold + trial + '.mot'
        grfFile = dataFold + trial + '_kinetics.mot'
        # read ik and grf
        ik = osim.Storage(ikFile)
        grf = osim.Storage(grfFile)
        trialFold = resultsFold + trial
        if not os.path.isdir(trialFold):
            os.mkdir(trialFold)
        # get the ExternalLoads object to write the exact path of the grfFile
        extLoads = osim.ExternalLoads(osimModel, xmlFold + 'ExternalLoads.xml')
        extLoads.setDataFileName(grfFile)
        extLoads.setExternalLoadsModelKinematicsFileName(ikFile)
        extLoads.setLowpassCutoffFrequencyForLoadKinematics(6)
        externalLoadsFile = 'ExternalLoads.xml'
        # print the external loads under trialFold
        extLoads.printToXML(externalLoadsFile)

        # run ID
        idTool = osim.InverseDynamicsTool(xmlFold+'InverseDynamics.xml')
        idTool.setModelFileName(originalModelFile)
        idTool.setStartTime(grf.getFirstTime())
        idTool.setEndTime(grf.getLastTime())
        idTool.setResultsDir(trialFold)
        idTool.setCoordinatesFileName(ikFile)
        idTool.printToXML('id.xml')
        idTool_run = osim.InverseDynamicsTool('id.xml')
        idTool_run.run()

        # get the SO analysis
        soAnalysis = osim.StaticOptimization()
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
        soTool = osim.AnalyzeTool()
        soTool.getAnalysisSet().adoptAndAppend(soAnalysis)
        soTool.setInitialTime(grf.getFirstTime())
        soTool.setFinalTime(grf.getLastTime())
        forcesetFileStr = osim.ArrayStr()
        forcesetFileStr.append(forcesetFile)
        soTool.setForceSetFiles(forcesetFileStr)
        soTool.setExternalLoadsFileName(externalLoadsFile)
        soTool.setCoordinatesFileName(ikFile)
        soTool.setLowpassCutoffFrequency(6)
        soTool.setResultsDir(soResultFolder)
        soTool.setOutputPrecision(15)
        # create a jr analysis (this will be updated for each analysis)
        jrAnalysis = osim.JointReaction()
        jrAnalysis.setName('JR')
        jrAnalysis.setStartTime(grf.getFirstTime())
        jrAnalysis.setEndTime(grf.getLastTime())
        # joint reactions to be calculated for jointNames exerted on
        # onBodies and expressed in inFrame
        jointNames = osim.ArrayStr()
        jointNames.append('all')
        onBodies = osim.ArrayStr()
        onBodies.append('child')
        inFrame = osim.ArrayStr()
        inFrame.append('child')
        jrAnalysis.setOnBody(onBodies)
        jrAnalysis.setInFrame(inFrame)
        jrAnalysis.setJointNames(jointNames)
        # create a jr tool (this will be updated for each analysis)
        jrTool = osim.AnalyzeTool()
        jrTool.setResultsDir(jrResultFolder)
        jrTool.setInitialTime(grf.getFirstTime())
        jrTool.setFinalTime(grf.getLastTime())
        jrTool.setExternalLoadsFileName(externalLoadsFile)
        jrTool.setCoordinatesFileName(ikFile)
        jrTool.setLowpassCutoffFrequency(6)
        # set the analysis
        jrTool.getAnalysisSet().adoptAndAppend(jrAnalysis)
        jrTool.setOutputPrecision(15)
        jrTool.setForceSetFiles(forcesetFileStr)
        for newModelFile, newModelPath in zip(modelFileNames, modelPaths):
            osimModel = osim.Model(newModelPath)
            toolNames = osimModel.getName() + '_' + trial
            # set soTool attribs depending on this new model
            soTool.setName(toolNames)
            soTool.setModelFilename(newModelPath)
            # print the soTool (prints to the OpenSim installation directory (C:\OpenSim 3.3)
            soTool.printToXML('so.xml')
            # create a new soTool from the printed xml
            soTool_run = osim.AnalyzeTool('so.xml')
            soTool_run.run()

            # jrAnalysis
            jrAnalysis.setForcesFileName(soResultFolder + '/' + toolNames + '_StaticOptimization_force.sto')
            # set jrtool attribs depending on this new model
            jrTool.setModelFilename(newModelPath)
            jrTool.setName(toolNames)
            # print the jrTool (prints to the OpenSim installation directory (C:\OpenSim 3.3)
            jrTool.printToXML('jr.xml')
            # create a new soTool from the printed xml
            jrTool_run = osim.AnalyzeTool('jr.xml')
            jrTool_run.run()

    # remove unnecessary files
    os.remove('id.xml')
    os.remove('so.xml')
    os.remove('jr.xml')
    os.remove('ExternalLoads.xml')


if __name__ == "__main__":
    runAnalysis()