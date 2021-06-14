# -*- coding: utf-8 -*-
"""
Created on Wed Jan 20 09:41:33 2021

@author: metin
"""
from utils import analysisDetails
import matplotlib as mpl
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')
import copy
import os
import numpy as np
from compareResults import compare
from fractions import gcd


# defaults
# axs cols (model names)
JOINT_MODEL_NAMES = ['Hip',   # only the Fiso of muscles crossing the hip joint are changed
                     'Knee',  # only the Fiso of muscles crossing the knee joint are changed
                     'Ankle', # only the Fiso of muscles crossing the ankle joint are changed
                     'Full',  # all muscles' Fiso are changed
                    ]
# axs rows (JRFs)
FORCES = ['hip', 'knee', 'ankle']

# labels for muscles
MUSCLE_LABELS = {'recfem_l': 'Rectus Femoris',
                 'iliacus_l': 'Iliacus',
                 'psoas_l': 'Psoas',
                 'bfsh_l': 'Biceps Femoris Short Head',
                 'gaslat_l': 'Gastrocnemius Lateralis',
                 'gasmed_l': 'Gastrocnemius Medialis',
                 'soleus_l': 'Soleus'}


def meanPeakDeviationPlot(reactions,
                          trials=['GC5_ss1', 'GC5_ss8', 'GC5_ss9', 'GC5_ss11'],
                          jointModelNames=['Hip', 'Knee', 'Ankle', 'Full'],
                          changeAmounts=[-40, -30, -20, -10, 0, 10, 20, 30, 40],
                          forces=['hip', 'knee', 'ankle'], tWindow=[40, 60],
                          ylim=[-0.3,0.75], compare='ACT', save=True):
    '''
    plots a chart, showing mean and std changes from the nominal model results

    Parameters
    ----------
    reactions: dict
        contains a key (trial) and corresponding model forces or acts
    trial: list
        trial names
    jointModelNames: list
        axs cols (model names)
    changeAmounts: list
        amount of percent changes to be applied on the jointModel strengths
    forces: list
        axs rows (force headers in reactions[trial])
    tWindow: list
        time window of % gait cycle for comparison (peak deviations)
    ylim: list, tuple
        y axis limits
    compare: string
        specify the type of the variables (ACT or SO or JRF)
    save: bool
        save figure if True
    Return
    ----------
    metrics:        :
    '''
    # cols and rows
    cols = {model:i for i, model in enumerate(jointModelNames)}
    rows = forces
    # lengths
    nrows = len(rows)
    ncols = len(jointModelNames)
    # y-labels (forces)
    ylabels = []
    # if joint reaction forces are plotted
    if compare == 'JRF':
        unit = 'JRF [BW]'
    # if so muscle forces
    elif compare == 'SO':
        unit = '[BW]'
    # if activations
    elif compare == 'ACT':
        unit = ''
    # ylabel = ylabel + unit
    for ylabel in rows:
        if compare == 'SO' or compare == 'ACT':
            try:
                ylabel = MUSCLE_LABELS[ylabel]
            except:
                pass
            ylabel = ylabel.replace(' ', '\n')
        ylabels.append(' '.join([ylabel, unit]))
    # create the figure template
    # create figure and axes with the given number of rows and cols
    fig, axs = plt.subplots(nrows, ncols, figsize=(11, 11))
    if ncols == 1 and nrows == 1:
        axs = np.array([[axs]])
    elif ncols == 1 or nrows == 1:
        axs = axs.reshape(nrows, ncols)
    fig.patch.set_facecolor('white')
    # y labels
    for r in range(nrows):
        if any(force in ylabels[r] for force in FORCES):
            font = 'large'
        else:
            font = 'small'
        axs[r, 0].set_ylabel(ylabels[r], fontsize=font)
    # y labels
    for ax in axs[-1, :]: ax.set_xlabel('% $F_{iso}$ Variation')
    # titles
    for ax, jointModel in zip(axs[0,:], jointModelNames): ax.set_title(jointModel)
    for (axRowID, axRow), force in zip(enumerate(axs), forces):
        # for each model type
        for (axColID, ax), jointModel in zip(enumerate(axRow), jointModelNames):
            barValues = []
            barValues_mean = []
            barValues_std = []
            x_pos = np.linspace(ylim[0], ylim[1], len(changeAmounts))
            # get each peak
            for iChange, change in enumerate(changeAmounts):
                # each trial
                metricTrials = []
                for trial in trials:
                    fileName = getJRFileName(jointModel, change, trial)
                    try:
                        peak = max(reactions[trial][fileName][force][tWindow[0]:tWindow[1]])
                        metricTrials.append(peak)
                    except:
                        pass
                # trials
                barValues.append(metricTrials)
                # mean and std of the trilas
                barValues_mean.append(np.mean(metricTrials))
                barValues_std.append(np.std(metricTrials))
                #ax.boxplot(metricTrials,positions=[x_pos[iChange]])
            #x_pos = np.arange(len(changeAmounts))
            ax.errorbar(x_pos, barValues_mean, barValues_std,
                        fmt='-o', color='gray', linewidth=0.5,
                        ecolor='black', elinewidth=2, markersize=1,
                        capsize=2, capthick=2)
            bar_width = 0.1
            opacity = 0.4
            #ax.bar(x_pos, barValues_mean, bar_width,
            #       yerr=barValues_std, align='center',
            #       ecolor='black', alpha=opacity)
            #ax.plot(x_pos, barValues_mean, ls='--', lw=0.5)
            #ax.axhline(y=0, color='gray', ls='-', lw=0.2)
            #ax.axhline(y=1, color='gray', ls='-', lw=0.2)

            ax.set_xticks(x_pos)

            labels = [str(c) for c in changeAmounts]
            ax.set_xticklabels(changeAmounts, rotation=45)
            ax.yaxis.grid(False)
            ax.xaxis.grid(False)
            #ax.axis('equal')
            ax.set_ylim(ylim)
            gc = gcd(100*abs(ylim[0]), 100*abs(ylim[1]))
            yticks = np.arange(ylim[0], ylim[1]+0.01, 0.2)
            if 0 not in yticks:
                yticks = np.append(yticks,0)
            ax.set_yticks(yticks)
            ax.set_facecolor('white')
            for tick in ax.xaxis.get_major_ticks():
                tick.label.set_fontsize(10)
            for tick in ax.yaxis.get_major_ticks():
                tick.label.set_fontsize(10)
    #fig.subplots_adjust(top=0.95, bottom=0.15, wspace=0.3, hspace=0.3)
    mng = plt.get_current_fig_manager()
    mng.window.showMaximized()
    plt.tight_layout()
    if save: saveCurrrentFig(fig, figname=compare+'_ErrorBar_Values', fold='Figures')
    plt.show()



def getJRFileName(model, change, trial):
    fileName = model
    if change > 0:
        fileName += '+' + str(change)
    elif change < 0:
       fileName += str(change)
    fileName += '_' + trial + '_JR_ReactionLoads.sto'
    return fileName


def plotTrial(reactions, expReactions, trial='GC5_ss1',
              jointModelNames=JOINT_MODEL_NAMES, forces=FORCES,
              ylim=[0,6], compare='JRF', save=True):
    '''
    plots model and in-vivo JRFs for a trial

    Parameters
    ----------
    reactions: dict
        contains a key (trial) and corresponding model JRFs
    expReactions: dict
        contains a key (trial) and corresponding in-vivo JRFs
    trial: string
        trial name
    jointModelNames: list
        axs cols (model names)
    forces: list
        axs rows (force headers in reactions[trial])
    '''
    # cols and rows
    cols = {model:i for i, model in enumerate(jointModelNames)}
    rows = forces
    # joint reaction forces in a dict whose keys are the the trials
    trialReactions = reactions[trial]
    if expReactions is not None:
        trialExpReactions = expReactions[trial]
    else:
        trialExpReactions = {None:None}
    # y-labels (forces)
    ylabels = []
    # if joint reaction forces are plotted
    if compare == 'JRF':
        unit = 'JRF [BW]'
    # if so muscle forces
    elif compare == 'SO':
        unit = '[BW]'
    # if activations
    elif compare == 'ACT':
        unit = ''
    # ylabel = ylabel + unit
    for ylabel in rows:
        if compare == 'SO' or compare == 'ACT':
            try:
                ylabel = MUSCLE_LABELS[ylabel]
            except:
                pass
            ylabel = ylabel.replace(' ', '\n')
        ylabels.append(' '.join([ylabel, unit]))
    # figure saving name
    if save:
        saveName = compare
    else:
        saveName = None
    # generate the figure
    generateFigure(trialReactions, trialExpReactions, trial,
                   rows, cols, ylabels, ylim, saveName)


# save the figure with given figname and format in a fold
def saveCurrrentFig(fig=None, fold='', figname='', format='svg'):
    # create fold if not exist
    if not os.path.isdir(fold):
        os.mkdir(fold)
    # save the fig
    fig.savefig(os.path.join(fold, figname + '.' + format),
                dpi=500,
                facecolor=fig.get_facecolor())


# creates figure and returns the handles for the figure and the axes
# to plot the total reaction forces on the hip, knee and ankle
def createFigure(nrows, ncols, ylabels, ylim):
    # create figure and axes with the given number of rows and cols
    fig, axs = plt.subplots(nrows, ncols, sharex=False, sharey=False, figsize=(16, 9))
    if ncols == 1 or nrows == 1:
        axs = axs.reshape(nrows, ncols)
    fig.patch.set_facecolor('white')
    # set some properties of the axes
    ticks = np.linspace(round(ylim[0]), round(ylim[1]), round(ylim[1])+1).tolist()
    if ylim[1]-ticks[-1] >= 0.05:
        ticks = ticks[:-1] + [ylim[1]]
    for ax in axs.flatten():
        ax.yaxis.grid(False)
        ax.xaxis.grid(False)
        ax.set_xlim([0, 100])
        ax.set_facecolor('white')
        ax.set_ylim(ylim)
        ax.set_yticks(ticks)
    # y labels
    for r in range(nrows):
        if any(force in ylabels[r] for force in FORCES):
            font = 'large'
        else:
            font = 'small'
        axs[r, 0].set_ylabel(ylabels[r], fontsize=font)
    # x labels
    for ax in axs[-1,:]: ax.set_xlabel('% Gait Cycle')

    return fig, axs

# get the current fig and ax
# order labels depending on the max iso percent change
# adjust the subplots
def arrangeFigure():
    # get current fig and ax
    fig, ax = plt.gcf(), plt.gca()
    # get the handles and labels
    handles, labels = ax.get_legend_handles_labels()
    # order the labels
    labelDict = {}
    for label, handle in zip(labels, handles):
        labelDict[label] = handle
    changes = [int(l[:-1]) if not 'Nom' in l else 0 for l in labels]
    changes.sort(reverse=False)
    labels = [["", "+"][r>0]+str(r)+'%' if r else 'Nominal' for r in changes]
    # order the handles accordingly
    handles = [labelDict[label] for label in labels]
    # set the figure legend
    # copy the handles
    handles = [copy.copy(ha) for ha in handles]
    # set the linewidths to the copies
    [ha.set_linewidth(7) for ha in handles ]
    fig.legend(handles, labels, ncol=len(labels), loc='lower center',
               prop={'size': 15}, facecolor='white', edgecolor='white')
    # adjust the subplots
    fig.subplots_adjust(top=0.95, bottom=0.15, wspace=0.15, hspace=0.3)


# generate figure for the given trial JRFs
# saves a png image of the figure
def generateFigure(trialReactions, trialExpReactions, trial, rows, cols, ylabels, ylim, saveName):
    # create the figure template
    fig, axs = createFigure(len(rows), len(cols.keys()), ylabels, ylim)
    n_lines = int((len(trialReactions.keys()) - len(cols.keys()))/len(cols.keys()))
    # for each jr file and its content
    for file, jrf in trialReactions.items():
        # get the name of the model and the change amount
        model, _, change = analysisDetails(file)
        change, cmap, r, lw, ls = getPlotProps(change, n_lines)
        if model in cols.keys():
            # get the column of the axs for this model
            axCol = axs[:, cols[model]]
            # set its title
            axCol[0].set_title(model)
            # for each row of this column (plot each joint force)
            for ax, row in zip(axCol, rows):
                ax.plot(jrf[row], label=change, c=cmap.to_rgba(r),
                        linewidth=lw, linestyle=ls)
                if row in list(trialExpReactions.keys()):
                    ax.plot(trialExpReactions[row], linewidth=3, linestyle='-',
                            color='Green',label='Experimental')
    # add suptitle (trial name)
    fig.suptitle(trial)
    # arrange figure, axs, labels, positions etc
    arrangeFigure()
    # save the figure
    if saveName: saveCurrrentFig(fig=fig, figname=trial+'_'+saveName, fold='Figures')
    # show the figure
    plt.show()
    return fig, axs


# returns a label, color and line properties depending on the % change in the model
def getPlotProps(change, n_lines):
    r = int(change) if change else 0
    lw = 1
    ls = '-'
    if r == 0:
        cmap = mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(vmin=1, vmax=n_lines),
                                     cmap=mpl.cm.Greys_r)
        lw = 2
        ls = '-.'
    elif r > 0:
        cmap = mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(vmin=1, vmax=n_lines),
                                     cmap=mpl.cm.Reds)
        r = (abs(r)+30)/10
    else:
        cmap = mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(vmin=1, vmax=n_lines),
                                     cmap=mpl.cm.Blues)
        r = (abs(r)+30)/10
    # change is for the label
    if not change:
        # if there is no change, label='Nominal'
        change = 'Nominal'
    else:
        change += '%'
    return change, cmap, r, lw, ls
