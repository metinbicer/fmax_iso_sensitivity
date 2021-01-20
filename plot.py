# -*- coding: utf-8 -*-
"""
Created on Wed Jan 20 09:41:33 2021

@author: metin
"""
import os
from utils import totalReactionForces, analysisDetails, createFigure

# folder containing the joint reaction results
fold = 'Results\\JRResults'
# read the files in the folder
files = [os.path.join(fold, file) for file in os.listdir(fold)]
# joint reaction forces in a dict whose keys are the filenames (scaling=BW)
reactions = totalReactionForces(files,scaling=75*9.81)

# axs cols (model names)
cols = {'WeakHip': 0, # only the muscles crossing the hip joint are weakened
        'WeakKnee': 1, # only the muscles crossing the knee joint are weakened
        'WeakAnkle': 2, # only the muscles crossing the ankle joint are weakened
        'WeakFull': 3 # all muscles are weakened
        }
# axs rows (joints)
rows = ['Hip', 'Knee', 'Ankle']
# create the figure template
fig, axs = createFigure(len(rows), len(cols.keys()))
# for each jr file and its content
for file, jrf in reactions.items():
    # get the name of the model and the reduction amount
    model, _, reduction = analysisDetails(file)
    # reduction is for the label
    if not reduction:
        # if there is no reduction, label='Nominal'
        reduction = 'Nominal'
    else:
        reduction += '%'
    # get the column of the axs for this model
    axCol = axs[:, cols[model]]
    # set its title
    axCol[0].set_title(model)
    # for each row of this column (plot each joint force)
    for ax, row in zip(axCol, rows):
        ax.plot(jrf[row.lower()], label=reduction)
# get the handles and labels
handles, labels = ax.get_legend_handles_labels()
# order the labels
labelDict = {}
for label, handle in zip(labels, handles):
    labelDict[label] = handle
reductions = [int(l[:-1]) if not 'Nom' in l else 0 for l in labels]
reductions.sort(reverse=True)
labels = [["", "+"][r>0]+str(r)+'%' if r else 'Nominal' for r in reductions]
# order the handles accordingly
handles = [labelDict[label] for label in labels]
# set the figure legend
fig.legend(handles, labels, ncol=len(labels), loc='upper center', 
           prop={'size': 12}, facecolor='white')
# adjust the subplots
fig.subplots_adjust(top=0.92, bottom=0.07, wspace=0.2, hspace=0.2)