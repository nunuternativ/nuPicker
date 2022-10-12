import sys
from importlib import *

from PySide2 import QtCore, QtWidgets
from shiboken2 import wrapInstance

import maya.cmds as mc

import app
reload(app)



def mayaRun(debug=False):
    '''
        Run the app in Maya
    '''
    import maya.OpenMayaUI as omui

    if mc.window(app.UI_WIN_NAME, q=True, ex=True):
        mc.deleteUI(app.UI_WIN_NAME, window=True)
    
    ptr = omui.MQtUtil.mainWindow()
    NuPickerApp = app.NuPicker(parent=wrapInstance(long(ptr), QtWidgets.QWidget))

    return NuPickerApp

'''
from nuTools.util.nuPicker import run as nuPicker_run
reload(nuPicker_run)
nuPicker_run.mayaRun()
'''