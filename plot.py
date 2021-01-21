# -*- coding: utf-8 -*-
"""
Created on Wed Jan 20 09:41:33 2021

@author: metin
"""
from utils import totalReactionForces, generateFigure

# folder containing the analysis
fold = 'GC5_ss1'
# joint reaction forces in a dict whose keys are the filenames (scaling=BW)
reactions = totalReactionForces('Results\\'+fold, scaling=75*9.81)

# axs cols (model names)
cols = {'WeakHip': 0, # only the muscles crossing the hip joint are weakened
        'WeakKnee': 1, # only the muscles crossing the knee joint are weakened
        'WeakAnkle': 2, # only the muscles crossing the ankle joint are weakened
        'WeakFull': 3 # all muscles are weakened
        }
# axs rows (joints)
rows = ['Hip', 'Knee', 'Ankle']
generateFigure(reactions, rows, cols, 
               ylabels=['Total Hip JRF [BW]', 'Total Knee JRF [BW]', 'Total Ankle JRF [BW]'])

# plot the lateral and medial loads
# cols is the same, define the rows (medial, lateral and total knee JRF)
rows = ['lateral', 'medial', 'knee']
generateFigure(reactions, rows, cols, 
               ylabels=['Lateral Knee JRF [BW]', 'Medial Knee JRF [BW]', 'Total Knee JRF [BW]'])
