# v.1.0.0  - Legacy version, moved to PySide2
# v.1.1.0  - Embed image data to saved layout
#          - Update text, change logo
#          - Update code for Python 3
# v.1.1.1  - Remove unused UI code
#          - Set DEFAULT_FILE_DIR to P:/Library/GeneralLibrary/picker
# v.1.2.0  - Add move action for moving button (Ctrl+Arrow)
#          - Change align shortcut to Ctrl+Shift+Arrow

VERSION = 'v.1.2.0'

# utility modules
import os
import pickle
import re
from functools import partial
from importlib import *

# Maya modules
import pymel.core as pm
import maya.OpenMaya as om
import maya.mel as mel
import maya.cmds as mc

# QT modules
from PySide2 import QtCore, QtWidgets, QtGui

# UI modules
import ui
reload(ui)

# global vars
FONT_NAME = 'Fixedsys'
DEFAULT_FILE_DIR = 'P:/Library/GeneralLibrary/picker'

### color vars
yellow = QtGui.QColor(225, 225, 0)
red = QtGui.QColor(225, 0, 0)
blue = QtGui.QColor(0, 0, 255)
lightBlue = QtGui.QColor(0, 225, 255)
green = QtGui.QColor(0, 225, 0)
purple = QtGui.QColor(177, 0, 255)
orange = QtGui.QColor(255, 87, 0)
brown = QtGui.QColor(80, 50, 0)
pink = QtGui.QColor(236, 177, 177)
gray = QtGui.QColor(87, 87, 87)
black = QtGui.QColor(0, 0, 0)
white = QtGui.QColor(255, 255, 255)

HIGHLIGHT_COLOR = QtGui.QColor(225, 225, 225)
DEFAULT_COLOR = yellow
DEFAULT_SIZE = 15

#### ui vars
WINDOW_NAME = 'nuPicker'
UI_WIN_NAME = 'nuPicker_MainWindow'
DEFAULT_TAB_NAME = 'tab'
MULTIPLE_VALUE_DISPLAY = '<multiple>'
ZOOM_STEP = 0.05
UNDO_LIMIT = 100
MAX_TOOLTIP_OBJ_NUM = 10

##################################################
#### undo classes
class CommandMoveButton(QtWidgets.QUndoCommand):
    '''
    Undo class for moving button.
    '''
    def __init__(self, buttons, oldPos, newPos):
        super(CommandMoveButton, self).__init__()
        self.buttons = buttons
        self.oldPos = oldPos
        self.newPos = newPos

    def redo(self):
        for i in xrange(len(self.buttons)):
            self.buttons[i].setPos(self.newPos[i])

    def undo(self):
        for i in xrange(len(self.buttons)):
            self.buttons[i].setPos(self.oldPos[i])

class CommandRenameButton(QtWidgets.QUndoCommand):
    '''
    Undo class for labeling button.
    '''
    def __init__(self, buttons, oldName, newName):
        super(CommandRenameButton, self).__init__()
        self.buttons = buttons
        self.oldName = oldName
        self.newName = newName

    def redo(self):
        for i in xrange(len(self.buttons)):
            self.buttons[i].setText(self.newName)

    def undo(self):
        for i in xrange(len(self.buttons)):
            self.buttons[i].setText(self.oldName[i])

class CommandColorButton(QtWidgets.QUndoCommand):
    '''
    Undo class for changing button color.
    '''
    def __init__(self, buttons, oldColors, newColor):
        super(CommandColorButton, self).__init__()
        self.buttons = buttons
        self.oldColors = oldColors
        self.newColor = newColor

    def redo(self):
        for i in xrange(len(self.buttons)):
            self.buttons[i].setColor(self.newColor, update=True)

    def undo(self):
        for i in xrange(len(self.buttons)):
            self.buttons[i].setColor(self.oldColors[i], update=True)

class CommandScaleButton(QtWidgets.QUndoCommand):
    '''
    Undo class for resizing button.
    '''
    def __init__(self, buttons, oldScales, newScale):
        super(CommandScaleButton, self).__init__()
        self.buttons = buttons
        self.oldScales = oldScales
        self.newScale = newScale

    def redo(self):
        for i in xrange(len(self.buttons)):
            self.buttons[i].resize(self.newScale)

    def undo(self):
        for i in xrange(len(self.buttons)):
            self.buttons[i].resize(self.oldScales[i])

class CommandOpacityButton(QtWidgets.QUndoCommand):
    '''
    Undo class for setting button opacity.
    '''
    def __init__(self, buttons, oldOpacities, newOpacity):
        super(CommandOpacityButton, self).__init__()
        self.buttons = buttons
        self.oldOpacities = oldOpacities
        self.newOpacity = newOpacity

    def redo(self):
        for i in xrange(len(self.buttons)):
            self.buttons[i].setButtonOpacity(self.newOpacity)

    def undo(self):
        for i in xrange(len(self.buttons)):
            self.buttons[i].setButtonOpacity(self.oldOpacities[i])

class CommandDeleteButton(QtWidgets.QUndoCommand):
    '''
    Undo class for deleting button.
    '''
    def __init__(self, parent, buttons):
        super(CommandDeleteButton, self).__init__()
        self.parent = parent
        self.buttons = buttons

    def redo(self):
        for button in self.buttons:
            self.parent.buttons.remove(button)
            self.parent.scene.removeItem(button)

    def undo(self):
        for button in self.buttons:
            self.parent.buttons.append(button)
            self.parent.scene.addItem(button)

class CommandCreateCmdButton(QtWidgets.QUndoCommand):
    '''
    Undo class for creating cmd button.
    '''
    def __init__(self, parent, label, size, opacity, color):
        super(CommandCreateCmdButton, self).__init__()
        self.parent = parent
        self.label = label
        self.size = size
        self.opacity = opacity
        self.color = color
        self.button = NuPickerCommandButton()
        self.cmd = ''

    def redo(self):
        self.parent.buttons.append(self.button)
        self.parent.scene.addItem(self.button)

        self.cmd = self.button.cmd
        self.button.setText(self.label)
        self.button.resize(self.size)
        self.button.setButtonOpacity(self.opacity)
        self.button.setColor(self.color, update=True)

    def undo(self):
        self.parent.buttons.remove(self.button) 
        self.parent.scene.removeItem(self.button)

class CommandCreateCmdButtonAt(QtWidgets.QUndoCommand):
    '''
    Undo class for creating button at position.
    '''
    def __init__(self, parent, pos, label, size, opacity, color):
        super(CommandCreateCmdButtonAt, self).__init__()
        self.parent = parent
        self.pos = pos
        self.label = label
        self.size = size
        self.opacity = opacity
        self.color = color
        self.button = NuPickerCommandButton()
        self.cmd = ''

    def redo(self):
        self.parent.buttons.append(self.button)
        self.parent.scene.addItem(self.button)

        self.cmd = self.button.cmd
        self.button.setText(self.label)
        self.button.resize(self.size)
        self.button.setButtonOpacity(self.opacity)
        self.button.setColor(self.color, update=True)
        self.button.setPos(self.pos)

    def undo(self):
        self.parent.buttons.remove(self.button) 
        self.parent.scene.removeItem(self.button)

class CommandCreateButton(QtWidgets.QUndoCommand):
    '''
    Undo class for creating button.
    '''
    def __init__(self, parent, label, size, opacity, color):
        super(CommandCreateButton, self).__init__()
        self.parent = parent
        self.label = label
        self.size = size
        self.opacity = opacity
        self.color = color
        self.button = NuPickerButton()
        self.objs = []

    def redo(self):
        self.parent.buttons.append(self.button)
        self.parent.scene.addItem(self.button)

        self.objs = self.button.objs
        self.button.setText(self.label)
        self.button.resize(self.size)
        self.button.setButtonOpacity(self.opacity)
        self.button.setColor(self.color, update=True)

    def undo(self):
        self.parent.buttons.remove(self.button) 
        self.parent.scene.removeItem(self.button)

class CommandCreateButtonAt(QtWidgets.QUndoCommand):
    '''
    Undo class for creating button at position.
    '''
    def __init__(self, parent, pos, label, size, opacity, color):
        super(CommandCreateButtonAt, self).__init__()
        self.parent = parent
        self.pos = pos
        self.label = label
        self.size = size
        self.opacity = opacity
        self.color = color

        self.button = NuPickerButton()
        self.objs = []

    def redo(self):
        self.parent.buttons.append(self.button)
        self.parent.scene.addItem(self.button)

        self.objs = self.button.objs
        self.button.setText(self.label)
        self.button.resize(self.size)
        self.button.setButtonOpacity(self.opacity)
        self.button.setColor(self.color, update=True)
        self.button.setPos(self.pos)

    def undo(self):
        self.parent.buttons.remove(self.button) 
        self.parent.scene.removeItem(self.button)

#### button class
class NuPickerButton(QtWidgets.QGraphicsRectItem):
    '''
    Button class.
    '''
    def __init__(self):
        super(NuPickerButton, self).__init__()
        # initial vars
        self.objs = []
        self.color = DEFAULT_COLOR
        self.scaleX = 1.0
        self.scaleY = 1.0

        self.text = QtWidgets.QGraphicsTextItem(parent=self)
        # self.text.setScale(0.65223)
        self.text.setTransform(QtGui.QTransform.fromTranslate(-1, -5.4))
        self.text.setDefaultTextColor(black)
        self.text.setFont(QtGui.QFont(FONT_NAME))

        # init default appearance
        # rect
        rect = QtCore.QRectF(0, 0, DEFAULT_SIZE, DEFAULT_SIZE)
        self.setRect(rect)

        # pen and brush
        self.setPen(QtGui.QPen(self.color))
        self.setBrush(QtGui.QBrush(self.color))

        # flags - not movable, selectable, send geometry change signal
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
        self.setCacheMode(QtWidgets.QGraphicsItem.DeviceCoordinateCache)

        # set not selected
        self.setSelected(False)

        # bind to what user is currently selecting
        self.bind()

    def setText(self, text):
        # set the text
        self.text.setPlainText(text)
        currRect = self.boundingRect()
        # currSRect = self.sceneBoundingRect()

        # if text is not empty string, set button bounding rect to match the text
        if text:
            textRect = self.text.boundingRect()
            self.setRect(currRect.x(), currRect.y(), textRect.width(), DEFAULT_SIZE)
        else:
            self.setRect(currRect.x(), currRect.y(), DEFAULT_SIZE, DEFAULT_SIZE)

    def resize(self, value):
        vx, vy = float('%.1f' %value[0]), float('%.1f' %value[1])
        fx, fy = 1.0, 1.0
        fx = vx/self.scaleX
        fy = vy/self.scaleY

        self.scaleX = float('%.1f' %vx)
        self.scaleY = float('%.1f' %vy)
        # self.scale(fx, fy)
        currRect = self.boundingRect()
        self.setTransform(QtGui.QTransform.fromScale(fx, fy), True)
        # x = currRect.width()*0.5
        # y = currRect.height()*0.5
        # self.setTransform(QtGui.QTransform().translate(x, y).scale(fx, fy).translate(-x, -y), True)

    def setButtonOpacity(self, value):
        self.setOpacity(value)

    def bind(self):
        self.objs = []
        sels = pm.selected()
        for sel in sels:
            fp = sel.fullPath()[1:]  # remove | at the beginning
            if sel.isReferenced() == True:
                ns = sel.namespace()
                fpRef = '|'.join([p for p in fp.split('|') if p.startswith(ns)])
                fpNs = fpRef.replace(ns, '')
                self.objs.append(fpNs)
            else:
                self.objs.append(fp)

        # set the tool tip to objects the button is bounded to      
        self.setButtonToolTip()

    def setButtonToolTip(self):
        tooltip = ''
        if self.objs:
            allObjsSn = [obj.split('|')[-1] for obj in self.objs]
            num_obj = len(allObjsSn)
            if num_obj > MAX_TOOLTIP_OBJ_NUM:
                allObjsSn = allObjsSn[:9]
                allObjsSn.append('and {} more...'.format(num_obj-MAX_TOOLTIP_OBJ_NUM))

            tooltip = '\n'.join(allObjsSn)
        self.setToolTip(tooltip)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemSelectedHasChanged:
            self.highlight()
        return QtWidgets.QGraphicsItem.itemChange(self, change, value)

    def setColor(self, color, update=False):
        self.color = color
        if update == True:
            self.setBrush(QtGui.QBrush(self.color))
            self.setPen(QtGui.QPen(self.color))
            v = self.color.value()
            if v <= 80:  # the button is dark, use white letters
                self.text.setDefaultTextColor(white)
            else:  # the button is light, use black letters
                self.text.setDefaultTextColor(black)


    def highlight(self):
        if self.isSelected() == True:
            self.setBrush(QtGui.QBrush(HIGHLIGHT_COLOR))
            self.setPen(QtGui.QPen(HIGHLIGHT_COLOR))
        else:
            self.setBrush(QtGui.QBrush(self.color))
            self.setPen(QtGui.QPen(self.color))

class NuPickerCommandButton(QtWidgets.QGraphicsEllipseItem):
    '''
    Command Button class.
    '''
    def __init__(self):
        super(NuPickerCommandButton, self).__init__()
        # initial vars
        self.cmd = ''
        self.language = 'mel'
        self.color = DEFAULT_COLOR
        self.scaleX = 1.0
        self.scaleY = 1.0

        self.text = QtWidgets.QGraphicsTextItem(parent=self)
        self.text.setScale(0.65223)
        self.text.setDefaultTextColor(black)
        self.text.setFont(QtGui.QFont(FONT_NAME))

        # init default appearance
        # rect
        rect = QtCore.QRectF(0, 0, DEFAULT_SIZE, DEFAULT_SIZE)
        self.setRect(rect)

        # pen and brush
        self.setPen(QtGui.QPen(self.color))
        self.setBrush(QtGui.QBrush(self.color))

        # flags - not movable, selectable, send geometry change signal
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
        self.setCacheMode(QtWidgets.QGraphicsItem.DeviceCoordinateCache)

        # set not selected
        self.setSelected(False)

    def setText(self, text):
        # set the text
        self.text.setPlainText(text)
        currRect = self.boundingRect()
        # if text is not empty string, set button bounding rect to match the text
        if text:
            textRect = self.text.boundingRect()
            self.setRect(currRect.x(), currRect.y(), textRect.width()*0.65223, textRect.height()*0.65223)
        else:
            self.setRect(currRect.x(), currRect.y(), DEFAULT_SIZE, DEFAULT_SIZE)

    def resize(self, value):
        vx, vy = float('%.1f' %value[0]), float('%.1f' %value[1])
        fx, fy = 1.0, 1.0
        fx = vx/self.scaleX
        fy = vy/self.scaleY

        self.scaleX = float('%.1f' %vx)
        self.scaleY = float('%.1f' %vy)
        # self.scale(fx, fy)
        self.setTransform(QtGui.QTransform.fromScale(fx, fy), True)

    def setButtonOpacity(self, value):
        self.setOpacity(value)

    def showCmdDialog(self):
        # create the dialog
        cmdDialog = cmdDialogUi()

        # set cmd and language to current button cmd and language
        cmdDialog.cmd_textEdit.setText(self.cmd)
        if self.language == 'python':
            cmdDialog.python_radioButton.setChecked(True)

        # if user press enter
        result = cmdDialog.exec_()

        if result == True:  # user pressed ok, get cmd and language
            return cmdDialog.getCmd()
        else:  # user pressed cancel
            return None

    def bind(self):
        ret = self.showCmdDialog()
        if not ret:
            return

        cmd = ret[0]
        self.language = ret[1]
        cmds = []
        noNsCmd = ''
        if self.language == 'mel':
            # cmd = cmd.replace('\n', '')
            for line in cmd.split('\n'):
                if line == '':
                    continue
                line = line.replace('\"', '')
                line = line.replace('\'', '')
                parts = []
                for part in line.split(' '):
                    # hasQoutes = False
                    # searchQ = re.search(r'(".*")', part)
                    # if searchQ:
                    #   part = searchQ.group()[1:-1]
                    #   hasQoutes = True

                    fpName = ''
                    lns = []
                    for p in part.split('|'):
                        nssplit = p.split(':')
                        if len(nssplit) > 1:
                            lnPart = '<ns>{}'.format(nssplit[-1])
                        else:
                            lnPart = nssplit[-1]
                        lns.append(lnPart)
                    fpName = '|'.join(lns)
                    parts.append(fpName)
                cmdPart = ' '.join(parts)
                cmds.append(cmdPart)
            self.cmd = '\n'.join(cmds)
        else:  # its in python
            strInQoutes = re.findall(r'(\'.*\')', cmd)
            strInDoubleQoutes = re.findall(r'(".*")', cmd)
            strInQoutes.extend(strInDoubleQoutes)
            for string in strInQoutes:
                q = string[0]
                strNoQ = string[1:-1]

                nssplit = strNoQ.split(':')
                if len(nssplit) > 1:
                    strNoQ = '<ns>{}'.format(nssplit[-1])
                newStr = '{}{}{}'.format(q, strNoQ, q)
                cmd = cmd.replace(string, newStr)
            self.cmd = cmd
        self.setToolTip(self.cmd)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemSelectedHasChanged:
            self.highlight()
        return QtWidgets.QGraphicsItem.itemChange(self, change, value)

    def setColor(self, color, update=False):
        self.color = color
        if update == True:
            self.setBrush(QtGui.QBrush(self.color))
            self.setPen(QtGui.QPen(self.color))
            v = self.color.value()
            if v <= 128:  # the button is dark
                self.text.setDefaultTextColor(white)
            else:
                self.text.setDefaultTextColor(black)

    def highlight(self):
        if self.isSelected() == True:
            self.setBrush(QtGui.QBrush(HIGHLIGHT_COLOR))
            self.setPen(QtGui.QPen(HIGHLIGHT_COLOR))
        else:
            self.setBrush(QtGui.QBrush(self.color))
            self.setPen(QtGui.QPen(self.color))

# tab layout class
class NuPickerLayout(QtWidgets.QGraphicsView):
    '''
    Layout class. 
    '''
    def __init__(self, app, parent, labelUi, sizeUi, opacityUi, parentUi):
        super(NuPickerLayout, self).__init__(parent)
        # parent ui vars
        self.app = app
        self.labelUi = labelUi
        self.sizeUi = sizeUi
        self.opacityUi = opacityUi
        self.parentUi = parentUi

        # interal vars
        self.loadedFrom = ''
        self.zooming = False
        self.displayOnly = False

        # viewport vars
        self.clickPos = QtCore.QPoint(0, 0)
        self.clickScenePos = QtCore.QPointF(0.0, 0.0)
        self.viewCenter = QtCore.QPointF(0.0, 0.0)

        # vars
        self.namespace = ''
        self.buttons = []
        
        #### qt object vars
        # the undo stack object
        self.undoStack = QtWidgets.QUndoStack(self)
        self.undoStack.setUndoLimit(UNDO_LIMIT)

        # graphic scene object
        self.scene = QtWidgets.QGraphicsScene()

        # setting up pixmap item for background image
        self.pixmapItem = QtWidgets.QGraphicsPixmapItem()
        self.pixmapItem.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, False)
        self.pixmapItem.setZValue(-1.0)

        # add pixmap item to scene
        self.scene.addItem(self.pixmapItem)

        # rubber band object
        self.rubberband = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        
        # setup
        self.setMouseTracking(True)
        self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setScene(self.scene)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # right click menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.rightClicked)
        self.rightClickMenu = QtWidgets.QMenu(self)

        # connect
        # self.scene.selectionChanged.connect(self.buttonSelectionChanged)

    def closeEvent(self, event):
        self.app.killJob()

    def undoIt(self):
        self.undoStack.undo()
            
    def redoIt(self):
        self.undoStack.redo()

    def rightClicked(self, pos):
        if self.zooming == True:
            self.zooming = False
            return

        self.rightClickMenu.clear()

        newButtonMenu = QtWidgets.QAction('add button', self)
        newCmdButtonMenu = QtWidgets.QAction('add command button', self)
        deleteButtonMenu = QtWidgets.QAction('delete button', self)
        bindSelectedMenu = QtWidgets.QAction('bind to...', self)
        setBgMenu = QtWidgets.QAction('set background', self)

        newButtonMenu.triggered.connect(lambda: self.newButtonAt(pos))
        newCmdButtonMenu.triggered.connect(lambda: self.newCmdButtonAt(pos))
        deleteButtonMenu.triggered.connect(lambda: self.deleteButtonAt(pos))
        bindSelectedMenu.triggered.connect(lambda: self.bindButton(pos))
        setBgMenu.triggered.connect(self.browseSetBackground)
        
        self.rightClickMenu.addAction(newButtonMenu)
        self.rightClickMenu.addAction(newCmdButtonMenu)

        self.rightClickMenu.addSeparator()

        self.rightClickMenu.addAction(deleteButtonMenu)
        self.rightClickMenu.addAction(bindSelectedMenu)
        self.rightClickMenu.addAction(setBgMenu)
        
        self.rightClickMenu.exec_(self.mapToGlobal(pos))

    def mouseDoubleClickEvent(self, event):
        pass

    def mousePressEvent(self, event):
        self.clickPos = event.pos()
        self.clickScenePos = self.mapToScene(self.clickPos)

        if event.buttons() & QtCore.Qt.LeftButton:
            # left clicked NO alt holded
            if not QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.AltModifier:
                self.rubberband.setGeometry(QtCore.QRect(event.pos(), QtCore.QSize()))
                self.rubberband.show()

            else:  # left clicked with alt holded - move button
                QtWidgets.QGraphicsView.mousePressEvent(self, event)
                selButtons = self.scene.selectedItems()
                for button in selButtons:
                    button.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)

    def mouseMoveEvent(self, event):

        # rubber band is visible (left clicked from anywhere within the scene)
        if self.rubberband.isVisible():
            self.rubberband.setGeometry(QtCore.QRect(self.clickPos, event.pos()).normalized())
        else:
            mods = QtWidgets.QApplication.keyboardModifiers()
            buttons = event.buttons()
            # middle mouse + alt - pan the frame
            if buttons & QtCore.Qt.MiddleButton and mods & QtCore.Qt.AltModifier:
                # set mouse cursor to drag(hand)
                self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
                currPos = self.mapToScene(event.pos())
                diff = currPos - self.clickScenePos
                self.translate(diff.x(), diff.y())
                self.clickScenePos = self.mapToScene(event.pos())
                self.viewCenter -= diff
            # right mouse + alt - zoom
            elif buttons & QtCore.Qt.RightButton and mods & QtCore.Qt.AltModifier:
                self.zooming = True
                currPos = event.pos()
                diff = currPos - self.clickPos
                factor = 1.0 + ZOOM_STEP

                if diff.y() + diff.x() < 0.0:  # zooming out
                    factor = 1.0/factor
                zoomed = self.transform().m11() * factor

                if zoomed > 0.168261435398:
                    self.scale(factor, factor)          
                else:
                    self.viewCenter = self.scene.sceneRect().center()

                self.centerOn(self.viewCenter)
                self.clickPos = event.pos()
        QtWidgets.QGraphicsView.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event): 
        self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        if self.rubberband.isVisible():
            self.rubberband.hide()

        if self.zooming == True:  # if zooming, do not modify selection
            return
        if event.button() == QtCore.Qt.LeftButton:
            mods = QtWidgets.QApplication.keyboardModifiers()
            if not mods & QtCore.Qt.AltModifier:
                # its a single click 
                if self.clickPos == event.pos():
                    item = self.itemAt(self.clickPos)
                    if item:
                        button = None
                        if item in self.buttons:  # selection is the button geometry itself(QGraphicsRectItem)
                            button = item
                        elif item.parentItem() in self.buttons:  # selection is the label(QGraphicsTextItem)
                            button = item.parentItem()

                        if button:
                            if mods & QtCore.Qt.ControlModifier:  # if user pressed ctrl, subtract selection
                                button.setSelected(False)
                            elif mods & QtCore.Qt.ShiftModifier:  # if user pressed shift, add selection
                                button.setSelected(True)
                            elif not mods:  # no modifier key pressed
                                self.scene.clearSelection()
                                button.setSelected(True)
                                
                        else:
                            self.scene.clearSelection()
                    else:
                        self.scene.clearSelection()

                    self.buttonSelectionChanged()
                else:  # its a rubber band drag
                    croppedItems = self.scene.items(self.mapToScene(self.rubberband.geometry()))
                    painterPath = QtGui.QPainterPath()
                    rect = self.mapToScene(self.rubberband.geometry())
                    croppedItems = [c for c in croppedItems if c in self.buttons]
                    if croppedItems:
                        if mods & QtCore.Qt.ControlModifier:  # if user pressed ctrl, subtract selection
                            painterPath = QtGui.QPainterPath()
                            oldPainterPath = QtGui.QPainterPath()

                            selButtons = self.scene.selectedItems()
                            if selButtons:
                                for button in selButtons:
                                    rect = button.sceneBoundingRect()
                                    oldPainterPath.addRect(rect)
                            else:
                                oldPainterPath.addRect(self.sceneRect())

                            for button in croppedItems:
                                rect = button.sceneBoundingRect()
                                painterPath.addRect(rect)
                            painterPath = oldPainterPath.subtracted(painterPath)

                        elif mods & QtCore.Qt.ShiftModifier:  # if user pressed shift, add selection
                            selButtons = self.scene.selectedItems()
                            croppedItems.extend(selButtons)
                            for button in croppedItems:
                                rect = button.sceneBoundingRect()
                                painterPath.addRect(rect)
                        elif not mods:  # no modifier key pressed
                            painterPath.addRect(rect.boundingRect())
                        self.scene.setSelectionArea(painterPath)
                    else:
                        self.scene.clearSelection()

                    self.buttonSelectionChanged()

            else:  # alt pressed, done moving button
                selButtons = self.scene.selectedItems()
                oldPos, newPos = [], []
                for button in selButtons:
                    # calculate old and new position for undo
                    newP = button.scenePos()
                    offset = (self.mapToScene(event.pos()) - self.clickScenePos)
                    oldP = newP - offset
                    oldPos.append(oldP)
                    newPos.append(newP)
                    
                    # set button not movable
                    button.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)

                # add to undostack
                command = CommandMoveButton(selButtons, oldPos, newPos)
                self.undoStack.push(command)
    
        QtWidgets.QGraphicsView.mouseReleaseEvent(self, event)

    def wheelEvent(self, event):
        scrollFactor = event.delta()/120.0  # -1.0 or 1.0  - only directions
        factor = 1.0 + ZOOM_STEP

        if scrollFactor < 0:  # zooming out
            factor = 1.0/factor
        
        zoomed = self.transform().m11() * factor
        if zoomed > 0.168261435398:
            self.scale(factor, factor)
        else:
            self.viewCenter = self.scene.sceneRect().center()

        self.centerOn(self.viewCenter)
        event.accept() 

    def browseSetBackground(self):
        imgPath, ext = QtWidgets.QFileDialog.getOpenFileName(parent=self, 
                                                    caption='Background image',
                                                    directory=self.parentUi.app.default_file_dir,
                                                    filter='Images (*.jpg *.png)')
        if imgPath:
            self.setBackground(path=imgPath)

    def bindButton(self, pos):
        item = self.itemAt(pos)
        button = None
        if item in self.buttons:
            button = item
        elif item.parentItem() in self.buttons:
            button = item.parentItem()

        if button:
            button.bind()
            self.app.createScriptJob(self)

    def renameButton(self, text=''):
        selButtons = self.scene.selectedItems()
        if selButtons:
            oldNames = []
            for button in selButtons:
                oldNames.append(str(button.text.toPlainText()))
            # add to undostack
            command = CommandRenameButton(selButtons, oldNames, text)
            self.undoStack.push(command)

    def setButtonColor(self, color):
        selButtons = self.scene.selectedItems()
        if selButtons:
            oldColors = []
            for button in selButtons:
                oldColors.append(button.color)
            # add to undostack
            command = CommandColorButton(selButtons, oldColors, color)
            self.undoStack.push(command)

    def scaleButton(self, value):
        selButtons = self.scene.selectedItems()
        if selButtons:
            oldScales = []
            for button in selButtons:
                oldScales.append([button.scaleX, button.scaleY])
            # add to undostack
            command = CommandScaleButton(selButtons, oldScales, value)
            self.undoStack.push(command)

    def opacityButton(self, value):
        selButtons = self.scene.selectedItems()
        if selButtons:
            oldOpacities = []
            for button in selButtons:
                oldOpacities.append(value)
            # add to undostack
            command = CommandOpacityButton(selButtons, oldOpacities, value)
            self.undoStack.push(command)

    def selectButtons(self, buttons, add=False):
        painterPath = QtGui.QPainterPath()

        if add == True:
            selButtons = self.scene.selectedItems()
            buttons.extend(selButtons)

        for button in buttons:
            rect = button.sceneBoundingRect()
            painterPath.addRect(rect)
        self.scene.setSelectionArea(painterPath)

    def deselectButtons(self, buttons):
        painterPath = QtGui.QPainterPath()
        oldPainterPath = QtGui.QPainterPath()

        selButtons = self.scene.selectedItems()
        if selButtons:
            for button in selButtons:
                rect = button.sceneBoundingRect()
                oldPainterPath.addRect(rect)
        else:
            oldPainterPath.addRect(self.sceneRect())

        for button in buttons:
            rect = button.sceneBoundingRect()
            painterPath.addRect(rect)

        resultPainterPath = oldPainterPath.subtracted(painterPath)
        self.scene.setSelectionArea(resultPainterPath)

    def newButton(self):
        # get configuration from the ui
        label, size, opacity, color = self.getButtonConfigs()

        # add to undostack
        command = CommandCreateButton(self, label, size, opacity, color)
        self.undoStack.push(command)    

        button = command.button
        button.setPos(self.scene.sceneRect().center())

        # clear selection and select the new button
        self.scene.clearSelection()
        button.setSelected(True)

        return button

    def newCmdButton(self):
        # get configuration from the ui
        label, size, opacity, color = self.getButtonConfigs()

        # add to undostack
        command = CommandCreateCmdButton(self, label, size, opacity, color)
        self.undoStack.push(command)    

        button = command.button
        button.setPos(self.scene.sceneRect().center())

        # clear selection and select the new button
        self.scene.clearSelection()
        button.setSelected(True)
        command.button.bind()

        return button

    def newButtonAt(self, pos):
        label, size, opacity, color = self.getButtonConfigs()
        
        # move the button to mouse position
        scenePos = self.mapToScene(pos)
        x = scenePos.x() - (size[0]*DEFAULT_SIZE*0.5)
        y = scenePos.y() - (size[1]*DEFAULT_SIZE*0.5)
        newPos = QtCore.QPointF(x, y)

        # add to undostack
        command = CommandCreateButtonAt(self, newPos, label, size, opacity, color)
        self.undoStack.push(command)
        
        # clear selection and select the new button
        self.scene.clearSelection()
        command.button.setSelected(True)

        self.app.createScriptJob(self)

    def newCmdButtonAt(self, pos):
        label, size, opacity, color = self.getButtonConfigs()
        
        # move the button to mouse position
        scenePos = self.mapToScene(pos)
        x = scenePos.x() - (size[0]*DEFAULT_SIZE*0.5)
        y = scenePos.y() - (size[1]*DEFAULT_SIZE*0.5)
        newPos = QtCore.QPointF(x, y)

        # add to undostack
        command = CommandCreateCmdButtonAt(self, newPos, label, size, opacity, color)
        self.undoStack.push(command)
        
        # clear selection and select the new button
        self.scene.clearSelection()
        command.button.setSelected(True)
        command.button.bind()

    def deleteButton(self):
        selButtons = self.scene.selectedItems()
        if selButtons:
            # add to undostack
            command = CommandDeleteButton(self, selButtons)
            self.undoStack.push(command)

    def deleteButtonAt(self, pos):
        item = self.itemAt(pos)
        button = None
        if item in self.buttons:
            button = item
        elif item.parentItem() in self.buttons:
            button = item.parentItem()

        if button:
            selButtons = self.scene.selectedItems()
            selButtons.append(button)
            selButtons = list(set(selButtons))
            # add to undostack
            command = CommandDeleteButton(self, selButtons)
            self.undoStack.push(command)

    def getButtonConfigs(self):
        # set button appearence at creation
        label = str(self.labelUi[0].text())
        if label == MULTIPLE_VALUE_DISPLAY:
            label = ''
        sizeX = self.sizeUi[0].value()
        sizeY = self.sizeUi[1].value()
        size = [sizeX, sizeY]
        opacity = self.opacityUi.value()
        color = self.parentUi.defaultButtonColor
        return label, size, opacity, color

    def setBackground(self, path=None, data=None):
        pixmap = None
        # create new pixmap item with image from the path
        if path:
            if not os.path.exists(path): 
                return
            pixmap = QtGui.QPixmap(path)
        # new pixmap from byte data
        elif data:
            ba = QtCore.QByteArray(data)
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(ba, "PNG")

        if not pixmap:
            return

        # scale to 1024
        pixmap = pixmap.scaled(1024, 1024, QtCore.Qt.KeepAspectRatio)

        # set scene rect to 3 times the image size
        self.scene.setSceneRect(0, 0, pixmap.width()*3, pixmap.height()*3)

        # try to remove the old pixmap item
        try:
            self.scene.removeItem(self.pixmapItem)
            del self.pixmapItem
        except:
            pass

        # create new pixmap item and add to the graphic scene
        self.pixmapItem = QtWidgets.QGraphicsPixmapItem()
        self.scene.addItem(self.pixmapItem)

        # placing background image
        # get the scene center
        sceneCenter = self.sceneRect().center()
        # move the background image to the center
        self.pixmapItem.setPos(sceneCenter)
        # the image moving point is at the upper left, have to offset it back up
        self.pixmapItem.setOffset(pixmap.width()*-0.5, pixmap.height()*-0.5)

        # setup pixmap item
        self.pixmapItem.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, False)
        self.pixmapItem.setZValue(-1.0)
        self.pixmapItem.setPixmap(pixmap)
        
        # frame image to center of the view
        self.fitInView(self.pixmapItem, QtCore.Qt.KeepAspectRatio)
        self.viewCenter = sceneCenter

    def createButtonFromData(self, data):
        # unpack the data
        label = data[0]
        sizeX, sizeY = data[1][0], data[1][1]
        opacity = data[2]
        color = data[3]
        qcolor = QtGui.QColor(color[0], color[1], color[2])
        exe = data[4]
        pos = data[5]

        # see if its a normal button or a cmd button
        if isinstance(exe, list):  # its normal button
            button = NuPickerButton()
            button.objs = exe
            button.setButtonToolTip()
            # button.setToolTip('\n'.join([obj.split('|')[-1] for obj in exe]))
        else:
            button = NuPickerCommandButton()
            # split out language
            lang = '<mel>'
            if not exe.startswith(lang):
                lang = '<python>'
                button.language = 'python'

            exe = exe.split(lang)[-1]

            button.cmd = exe
            button.setToolTip(exe)

        self.buttons.append(button)
        self.scene.addItem(button)

        # setup the new button
        button.setText(text=label)
        button.resize(value=[sizeX, sizeY])
        button.setButtonOpacity(value=opacity)
        button.setColor(color=qcolor, update=True)

        button.setPos(pos[0], pos[1])

        return button

    def buttonSelectionChanged(self):
        text, scaleTxt, opacityTxt = '', '', ''
        
        if self.displayOnly == False:
            texts, scales, opacities = set(), set(), set()
            selButtons = self.scene.selectedItems()

            cmd = ''
            btnMelCmd = ''
            btnPyCmd = ''
            objNames = set()
            cmdButtons = []
            if selButtons:
                for button in selButtons:
                    texts.add(str(button.text.toPlainText()))  # add label to the set
                    scales.add((button.scaleX, button.scaleY))
                    opacities.add(button.opacity())
                    ns = '|{}'.format(self.namespace)
                    if isinstance(button, NuPickerButton):  # it's a button
                        setSel = False
                        if button.objs:
                            for obj in button.objs:
                                name = '{}{}'.format(self.namespace, obj.replace('|', ns))
                                shortName = name.split('|')[-1]
                                if pm.objExists(name) == True:
                                    objNames.add(name)
                                    setSel = True
                                elif len(mc.ls(shortName)) == 1:
                                    objNames.add(shortName)
                                    setSel = True
                        self.displayOnly = True
                        button.setSelected(setSel)
                        self.displayOnly = False
                    elif isinstance(button, NuPickerCommandButton):  # it's a command button
                        cmdButtons.append(button)
                        if button.cmd:
                            nsCmd = button.cmd.replace('<ns>', self.namespace)
                            if button.language == 'mel':
                                btnMelCmd += nsCmd
                            else:
                                btnPyCmd  += nsCmd

                if len(texts) > 1:
                    text = MULTIPLE_VALUE_DISPLAY
                elif texts:
                    text = str(list(texts)[0])

                if len(scales) > 1:
                    scaleTxt = MULTIPLE_VALUE_DISPLAY
                elif scales:
                    sc = list(scales)[0]
                    scaleTxt = '{}, {}'.format(sc[0], sc[1])

                if len(opacities) > 1:
                    opacityTxt = MULTIPLE_VALUE_DISPLAY
                elif opacities:
                    opacityTxt = str(list(opacities)[0])

            

            # then execute selection
            if objNames:
                objs = list(objNames)
                cmd = 'select -r {};'.format(' '.join(objs))
            else:
                cmd = 'select -cl;'
                text, scaleTxt, opacityTxt = '', '', ''

        
            # execute command button command
            # MEL
            if btnMelCmd or btnPyCmd:
                if btnMelCmd:
                    try:
                        mel.eval(btnMelCmd)
                    except Exception as e:
                        pass
                # Python
                if btnPyCmd:
                    try:
                        pm.python(btnPyCmd)
                    except Exception as e:
                        print(e)

            else:
                # execute the select command
                mel.eval(cmd)

            self.displayOnly = True
            for b in cmdButtons:
                b.setSelected(False)
            self.displayOnly = False

        # update ui
        self.labelUi[0].setText(text)
        self.labelUi[1].setText(scaleTxt)
        self.labelUi[2].setText(opacityTxt)
        

#### the ui class
# create command button dialog
class cmdDialogUi(QtWidgets.QDialog, ui.Ui_cmd_dialog) :
    def __init__(self, parent=None):        
        super(cmdDialogUi, self).__init__(parent)
        self.setupUi(self)
    def getCmd( self ) :
        cmd = str(self.cmd_textEdit.toPlainText())
        language = 'mel'
        if self.python_radioButton.isChecked() == True:
            language = 'python'
        return [cmd, language]

# the main dialog
class NuPickerUi(QtWidgets.QMainWindow, ui.Ui_nuPicker_MainWindow):
    '''
    UI class. Modify the UI class converted from .ui file.
    '''
    def __init__(self, parent, app) :
        super(NuPickerUi, self ).__init__(parent)
        self.setupUi(self)

        self.app = app  # application that owns the ui

        # set up nameSpace comboBox to do auto completion in a pop-up widget
        completer = self.namespace_comboBox.completer()
        completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        self.namespace_comboBox.setCompleter(completer)

        # default color var for button
        self.defaultButtonColor = DEFAULT_COLOR

        # color dialog
        self.colorDialog = QtWidgets.QColorDialog(self)
        self.colorDialog.setOption(QtWidgets.QColorDialog.ShowAlphaChannel, False)
        self.colorDialog.setOption(QtWidgets.QColorDialog.DontUseNativeDialog, True)
        self.colorDialog.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        # set current color to the global var DEFAULT_COLOR
        self.colorDialog.setCurrentColor(DEFAULT_COLOR)

        # custom colors
        self.colorDialog.setCustomColor(0, yellow)
        self.colorDialog.setCustomColor(1, red)
        self.colorDialog.setCustomColor(2, blue)
        self.colorDialog.setCustomColor(3, lightBlue)
        self.colorDialog.setCustomColor(4, green)
        self.colorDialog.setCustomColor(5, purple)
        self.colorDialog.setCustomColor(6, orange)
        self.colorDialog.setCustomColor(7, brown)
        self.colorDialog.setCustomColor(8, pink)
        self.colorDialog.setCustomColor(9, gray)
    
    def quit(self):
        self.close()

    def closeEvent(self, event):
        self.app.killJob()

        
#### application class
class NuPicker(object):
    '''
    The main application class.
    '''
    # def __init__(self, parent=None, dock=None):
    def __init__(self, parent=None):
        # class vars
        self.__defaultScrollRollVis = QtCore.Qt.ScrollBarAlwaysOff
        self.__package_dir = os.path.dirname(__file__).replace('\\', '/')
            
        # icon and image paths
        self.__default_bg_dir = '{}/ui/img/default_bg.jpg'.format(self.__package_dir)
        self.__app_icon_dir = '{}/ui/img/app_icon.png'.format(self.__package_dir)
        self.__refresh_icon_dir = '{}/ui/img/refresh_icon.png'.format(self.__package_dir)

        self.__jobID = 0
        self.__createScriptJob = True

        # directory var
        self.default_file_dir = DEFAULT_FILE_DIR
        if not os.path.exists(DEFAULT_FILE_DIR):
            # if DEFAULT_FILE_DIR doesn't exist use my doc instead
            self.default_file_dir = os.path.expanduser('~')

        # instance the main UI
        self.ui = NuPickerUi(parent, self)
        
        # modify the UI
        # window icon
        self.ui.setObjectName(UI_WIN_NAME)
        self.ui.setWindowIcon(QtGui.QIcon(self.__app_icon_dir))
        self.ui.refresh_toolButton.setIcon(QtGui.QIcon(self.__refresh_icon_dir))
        # override main window's title
        self.ui.setWindowTitle(QtWidgets.QApplication.translate(str(self.ui.objectName()), 
                                                    "{} {}".format(WINDOW_NAME, VERSION), None))

        ## connect UI
        # tabs
        self.ui.main_tabWidget.tabCloseRequested.connect(self.closeTab)

        # namespace
        self.ui.refresh_toolButton.clicked.connect(self.refreshNamespace)
        self.ui.namespace_comboBox.activated.connect(self.setNamespace)
        # self.ui.namespace_comboBox.lineEdit().returnPressed.connect(self.setNamespace)
        self.ui.namespace_comboBox.lineEdit().editingFinished.connect(self.setNamespace) 

        ### menu
        # file
        self.ui.open_action.triggered.connect(self.open)
        self.ui.save_action.triggered.connect(self.save)
        self.ui.saveAs_action.triggered.connect(self.saveAs)
        self.ui.setDirectory_action.triggered.connect(self.setDirectory)
        self.ui.quit_action.triggered.connect(self.quit)

        # edit
        self.ui.undo_action.triggered.connect(self.undoIt)
        self.ui.redo_action.triggered.connect(self.redoIt)

        self.ui.newButton_action.triggered.connect(lambda: self.newButton('button'))
        self.ui.newCmdButton_action.triggered.connect(lambda: self.newButton('cmd'))
        self.ui.deleteButton_action.triggered.connect(self.deleteButton)

        self.ui.alignLeft_action.triggered.connect(lambda: self.alignVertical(True, False))
        self.ui.alignRight_action.triggered.connect(lambda: self.alignVertical(False, False))
        self.ui.alignTop_action.triggered.connect(lambda: self.alignHorizontal(True, False))
        self.ui.alignBottom_action.triggered.connect(lambda: self.alignHorizontal(False, False))

        self.ui.moveLeft_action.triggered.connect(lambda: self.alignVertical(True, True))
        self.ui.moveRight_action.triggered.connect(lambda: self.alignVertical(False, True))
        self.ui.moveUp_action.triggered.connect(lambda: self.alignHorizontal(True, True))
        self.ui.moveDown_action.triggered.connect(lambda: self.alignHorizontal(False, True))

        self.ui.newTab_action.triggered.connect(lambda: self.newTab(DEFAULT_TAB_NAME))
        self.ui.browseBackground_action.triggered.connect(self.setBackground)
        self.ui.setDefaultBackground_action.triggered.connect(self.setDeaultBackground)

        # settings
        self.ui.enableScrollRoll_action.triggered.connect(self.toggleScrollRoll)
    
        # view
        self.ui.frameSelected_action.triggered.connect(self.frameSelected)

        # tool button and spinboxes
        self.ui.label_lineEdit.returnPressed.connect(self.renameButton)
        self.ui.sizeX_doubleSpinBox.valueChanged.connect(lambda: self.scaleButton('x'))
        self.ui.sizeY_doubleSpinBox.valueChanged.connect(lambda: self.scaleButton('y'))
        self.ui.opacity_doubleSpinBox.valueChanged.connect(self.opacityButton)

        # color pushbutton and color dialog
        self.ui.color_pushButton.pressed.connect(self.colorButtonPressed)
        self.ui.color_pushButton.released.connect(self.colorButtonReleased)
        self.ui.colorDialog.colorSelected.connect(self.setDefaultButtonColor)

        # set timer for color button hold-click
        self.timer = QtCore.QTimer()
        self.timer.setInterval(200)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.setDefaultButtonColor)
        
        # tab widget
        self.ui.main_tabWidget.currentChanged.connect(self.tabChanged)
        # right clicked menu
        self.ui.main_tabWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.main_tabWidget.customContextMenuRequested.connect(self.tabRightClicked) 

        # show all ui
        self.ui.show()

        # init default state
        self.initDefault()
        self.refreshNamespace()
        self.setDefaultButtonColor()

    def setDirectory(self):
        text, result = QtWidgets.QInputDialog.getText(self.ui, 
                                            'File directory', 
                                            'Path:', 
                                            QtWidgets.QLineEdit.Normal,
                                            self.default_file_dir,
                                            True 
                                            )
        if result and text:
            path = str(text)
            if os.path.exists(os.path.normpath(path)):
                self.default_file_dir = path
                print('Directory set: {}'.format(path))
            else:
                om.MGlobal.displayError('Path does not exist: {}'.format(path))

    def colorButtonPressed(self):
        self.timer.start()

    def colorButtonReleased(self):
        if self.timer.isActive():  # it's a clicked
            self.ui.colorDialog.open(QtCore.QObject(), '')

        self.timer.stop()
        
    def setDefaultButtonColor(self):
        # get the selected color from the color dialog
        color = self.ui.colorDialog.currentColor()

        # set color for color button
        iconPixmap = QtGui.QPixmap(DEFAULT_SIZE, DEFAULT_SIZE)
        iconPixmap.fill(color)
        colorIcon = QtGui.QIcon()   
        colorIcon.addPixmap(iconPixmap)
        # self.ui.color_pushButton
        self.ui.color_pushButton.setIcon(colorIcon)

        # set default color var
        self.ui.defaultButtonColor = color

        # change button color
        self.setButtonColor(color)

    def undoIt(self):
        currLayout = self.ui.main_tabWidget.currentWidget()
        if currLayout:
            currLayout.undoIt()

    def redoIt(self):
        currLayout = self.ui.main_tabWidget.currentWidget()
        if currLayout:
            currLayout.redoIt()

    def initDefault(self):
        # add a default tab
        self.ui.main_tabWidget.clear()
        self.__createScriptJob = False
        layout, index = self.newTab(name='default')
        global activeTab
        activeTab = layout
        self.__createScriptJob = True

    def dockUi(self, area):
        self.ui.dock(area=area)

    def frameSelected(self):
        currLayout = self.ui.main_tabWidget.currentWidget()
        if currLayout:
            sels = currLayout.scene.selectedItems()
            scaleFactor = 1.0
            if not sels:
                rect = currLayout.pixmapItem.sceneBoundingRect()
            else:
                rect = QtCore.QRectF(0.0, 0.0, 0.0, 0.0)
                for sel in sels:
                    rect = rect.united(sel.sceneBoundingRect())
                scaleFactor =  0.5

            currLayout.fitInView(rect, QtCore.Qt.KeepAspectRatio)
            currLayout.scale(scaleFactor, scaleFactor)
            currLayout.viewCenter = rect.center()
            currLayout.centerOn(currLayout.viewCenter)

    def toggleScrollRoll(self):
        setting = QtCore.Qt.ScrollBarAlwaysOff
        if self.ui.enableScrollRoll_action.isChecked() == True:
            setting = QtCore.Qt.ScrollBarAlwaysOn

        self.__defaultScrollRollVis = setting

        tabWidget = self.ui.main_tabWidget
        for i in xrange(tabWidget.count()):
            layout = tabWidget.widget(i)
            layout.setVerticalScrollBarPolicy(setting)
            layout.setHorizontalScrollBarPolicy(setting)

    def setNamespace(self):
        currLayout = self.ui.main_tabWidget.currentWidget()
        if currLayout:
            ns = str(self.ui.namespace_comboBox.currentText())
            currLayout.namespace = ns
            currLayout.setFocus()
            if self.__createScriptJob == True:
                self.createScriptJob(currLayout)
                currLayout.buttonSelectionChanged()


    def tabChanged(self):
        currLayout = self.ui.main_tabWidget.currentWidget()
        if currLayout:
            
            self.setNamespaceFromLayout(layout=currLayout)
            currLayout.buttonSelectionChanged()
            currLayout.setFocus()
            self.toggleScrollRoll()
            if self.__createScriptJob == True:
                self.createScriptJob(currLayout)

    def setNamespaceFromLayout(self, layout=None):
        if not layout:
            layout = self.ui.main_tabWidget.currentWidget()

        comboBox = self.ui.namespace_comboBox
        for i in xrange(self.ui.namespace_comboBox.count()):
            if comboBox.itemText(i) == layout.namespace:
                comboBox.setCurrentIndex(i)
                break

    def createScriptJob(self, currLayout):
        self.killJob()
        ns = str(self.ui.namespace_comboBox.currentText())
        global watchButtons
        watchButtons = {}
        for b in [i for i in currLayout.buttons if isinstance(i, NuPickerButton)]:
            watchButtons[b] = ['|'.join('{}{}'.format(ns, s) for s in o.split('|')) for o in b.objs]

        global activeTab
        activeTab = self.ui.main_tabWidget.currentWidget()

        self.__jobID = pm.scriptJob(e=["SelectionChanged", pm.Callback(scriptJobWatch)], kws=True, cu=False)

    def quit(self):
        self.ui.quit()

    def refreshNamespace(self):
        self.ui.namespace_comboBox.clear()
        self.ui.namespace_comboBox.addItem('')
        currLayout = self.ui.main_tabWidget.currentWidget()
        allNs = [ns for ns in pm.namespaceInfo(lon=True, r=True) if ns not in ['UI', 'shared']]
        if allNs:
            for ns in allNs:
                self.ui.namespace_comboBox.addItem('{}:'.format(ns))

        self.setNamespaceFromLayout(layout=currLayout)
        self.createScriptJob(currLayout)

    def newTab(self, name=DEFAULT_TAB_NAME):
        layout = NuPickerLayout(app=self, 
            parent=self.ui.main_tabWidget, 
            labelUi=[self.ui.label_lineEdit, self.ui.scale_label, self.ui.opacity_label],
            sizeUi=[self.ui.sizeX_doubleSpinBox, self.ui.sizeY_doubleSpinBox],
            opacityUi=self.ui.opacity_doubleSpinBox,
            parentUi=self.ui)

        self.ui.main_tabWidget.addTab(layout, name)
        index = self.ui.main_tabWidget.indexOf(layout)
        self.__createScriptJob = False
        self.ui.main_tabWidget.setCurrentWidget(layout)
        self.__createScriptJob = True
        layout.setBackground(path=self.__default_bg_dir)
        # layout.destroyed.connect(self.killJob)
        return layout, index

    def killJob(self):
        try:
            if pm.scriptJob(ex=self.__jobID):
                pm.scriptJob(kill=self.__jobID, force=True)
        except:
            pass
        

    def tabRightClicked(self, pos):
        tabWidget = self.ui.main_tabWidget
        tabIndex = tabWidget.tabBar().tabAt(pos)
        tab = tabWidget.widget(tabIndex)
        tabRenameRightClickMenu = QtWidgets.QMenu(tabWidget.tabBar())
        
        if tab:
            tabRenameRightClickMenu.addAction(QtWidgets.QAction('rename', tabRenameRightClickMenu))     
        else:
            tabRenameRightClickMenu.addAction(QtWidgets.QAction('new tab..', tabRenameRightClickMenu))

        action = tabRenameRightClickMenu.exec_(self.ui.main_tabWidget.mapToGlobal(pos))
        if action:
            if str(action.text()) == 'rename':
                # create line edit
                inputWidget = QtWidgets.QLineEdit()
                inputWidget.setWindowFlags(QtCore.Qt.FramelessWindowHint)
                inputWidget.setFixedWidth(70)
                inputWidget.move(QtGui.QCursor.pos())
                inputWidget.setWindowModality(QtCore.Qt.ApplicationModal)
                inputWidget.returnPressed.connect(lambda: self.renameTab(inputWidget, tabIndex))
                # show line edit
                inputWidget.show()
                inputWidget.setFocus()      
                inputWidget.raise_()
            elif str(action.text()) == 'new tab..':
                self.newTab()

    def renameTab(self, inputWidget, tabIndex):
        new_name = str(inputWidget.text())
        inputWidget.close()
        if new_name != '':
            self.ui.main_tabWidget.setTabText(tabIndex, new_name)

    def closeTab(self):
        currIndex = self.ui.main_tabWidget.currentIndex()
        self.ui.main_tabWidget.removeTab(currIndex)

    def newButton(self, typ):
        # get current layout
        currLayout = self.ui.main_tabWidget.currentWidget()
        if currLayout:
            if typ == 'button':
                currLayout.newButton()
            elif typ == 'cmd':
                currLayout.newCmdButton()

            self.createScriptJob(currLayout)

    def deleteButton(self):
        currLayout = self.ui.main_tabWidget.currentWidget()
        if currLayout:
            currLayout.deleteButton()
            self.createScriptJob(currLayout)

    def setButtonColor(self, color):
        currLayout = self.ui.main_tabWidget.currentWidget()
        if currLayout:
            currLayout.setButtonColor(color=color)

    def renameButton(self):
        currLayout = self.ui.main_tabWidget.currentWidget()
        if currLayout:
            text = str(self.ui.label_lineEdit.text())
            currLayout.renameButton(text=text)
            currLayout.setFocus()

    def scaleButton(self, axis):
        currLayout = self.ui.main_tabWidget.currentWidget()
        if currLayout:
            # disconnect signal first
            self.ui.sizeX_doubleSpinBox.valueChanged.disconnect()
            self.ui.sizeY_doubleSpinBox.valueChanged.disconnect()

            # current values
            x = self.ui.sizeX_doubleSpinBox.value()
            y = self.ui.sizeY_doubleSpinBox.value()
            constage = self.ui.constrainProportions_aciton.isChecked()
            if constage == True:
                if axis == 'x':
                    y = x
                    self.ui.sizeY_doubleSpinBox.setValue(x)
                else:
                    x = y
                    self.ui.sizeX_doubleSpinBox.setValue(y)

            # do the scaling
            currLayout.scaleButton(value=[x, y])

            # connect signal back in
            self.ui.sizeX_doubleSpinBox.valueChanged.connect(lambda: self.scaleButton('x'))
            self.ui.sizeY_doubleSpinBox.valueChanged.connect(lambda: self.scaleButton('y'))

    def opacityButton(self):
        currLayout = self.ui.main_tabWidget.currentWidget()
        if currLayout:
            value = self.ui.opacity_doubleSpinBox.value()
            currLayout.opacityButton(value=value)

    def setBackground(self):
        currLayout = self.ui.main_tabWidget.currentWidget()
        if currLayout:
            currLayout.browseSetBackground()

    def setDeaultBackground(self):
        currLayout = self.ui.main_tabWidget.currentWidget()
        if currLayout:
            currLayout.setBackground(path=self.__default_bg_dir)

    def alignVertical(self, left=True, move=True):
        currLayout = self.ui.main_tabWidget.currentWidget()
        if currLayout:
            selButtons = currLayout.scene.selectedItems()
            if not selButtons:
                return

            oldPos, newPos = [], []
            if move:  # move
                for button in selButtons:
                    sceneRect = button.mapRectToScene(button.rect())
                    tenthWidth = sceneRect.width() * 0.1
                    x = button.x()
                    if left:
                        x -= tenthWidth
                    else:
                        x += tenthWidth
                    oldPos.append(button.scenePos())
                    newPos.append(QtCore.QPointF(x, button.y()))
            else:  # align
                centers = []
                for button in selButtons:
                    sceneRect = button.mapRectToScene(button.rect())
                    baseX = sceneRect.x()
                    halfWidth = sceneRect.width() * 0.5
                    centers.append(baseX + halfWidth)
                baseCenter = 0.0
                if left == True:
                    baseCenter = min(centers)
                else:
                    baseCenter = max(centers)

                
                for button in selButtons:
                    sceneRect = button.mapRectToScene(button.rect())
                    halfWidth = sceneRect.width() * 0.5
                    x = baseCenter - halfWidth
                    y = button.y()
                    oldPos.append(button.scenePos())
                    newPos.append(QtCore.QPointF(x, y))

            command = CommandMoveButton(selButtons, oldPos, newPos)
            currLayout.undoStack.push(command)

    def alignHorizontal(self, top=True, move=True):
        currLayout = self.ui.main_tabWidget.currentWidget()
        if currLayout:
            selButtons = currLayout.scene.selectedItems()
            if not selButtons:
                return

            oldPos, newPos = [], []
            if move:  # move
                for button in selButtons:
                    sceneRect = button.mapRectToScene(button.rect())
                    tenthWidth = sceneRect.width() * 0.1
                    y = button.y()
                    if top:
                        y -= tenthWidth
                    else:
                        y += tenthWidth
                    oldPos.append(button.scenePos())
                    newPos.append(QtCore.QPointF(button.x(), y))
            else:  # align
                centers = []
                for button in selButtons:
                    sceneRect = button.mapRectToScene(button.rect())
                    baseY= sceneRect.y()
                    halfHeight = sceneRect.height() * 0.5
                    centers.append(baseY + halfHeight)
                baseCenter = 0.0
                if top == True:
                    baseCenter = min(centers)
                else:
                    baseCenter = max(centers)

                for button in selButtons:
                    sceneRect = button.mapRectToScene(button.rect())
                    halfHeight = sceneRect.height() * 0.5
                    x = button.x()
                    y = baseCenter - halfHeight
                    oldPos.append(button.scenePos())
                    newPos.append(QtCore.QPointF(x, y))

            command = CommandMoveButton(selButtons, oldPos, newPos)
            currLayout.undoStack.push(command)

    def open(self):
        dialog = QtWidgets.QFileDialog(self.ui)
        dialog.setWindowTitle('Open')
        dialog.setNameFilter('*.npk')
        dialog.setDefaultSuffix('npk')
        dialog.setDirectory(self.default_file_dir)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        pklPath = None
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            pklPath = dialog.selectedFiles()[0]

        if pklPath:
            self.load(path=str(pklPath))


    def save(self):
        currLayout = self.ui.main_tabWidget.currentWidget()
        if currLayout:
            if not currLayout.loadedFrom:
                self.saveAs()
            else:
                doSave = False
                if os.path.exists(currLayout.loadedFrom):
                    reply = QtWidgets.QMessageBox.question(self.ui,
                        'Confirm file save',
                        'File already exists. Overwrite?\n{}'.format(currLayout.loadedFrom),
                        QtWidgets.QMessageBox.Yes,
                        QtWidgets.QMessageBox.No)
                    if reply == QtWidgets.QMessageBox.Yes:
                        doSave = True
                else:
                    doSave = True

                if doSave == True:
                    self.write(layout=currLayout, path=currLayout.loadedFrom)

    def saveAs(self):
        currLayout = self.ui.main_tabWidget.currentWidget()
        if currLayout:
            dialog = QtWidgets.QFileDialog(currLayout)
            dialog.setWindowTitle('Save as')
            dialog.setNameFilter('*.npk')
            dialog.setDefaultSuffix('npk')
            dialog.setDirectory(self.default_file_dir)
            dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                pklPath = dialog.selectedFiles()[0]
                if pklPath:
                    pklPath = str(pklPath)
                    self.write(layout=currLayout, path=pklPath)
                    currLayout.loadedFrom = pklPath

    def write(self, layout, path):
        path = os.path.normpath(path)
        if not os.path.exists(os.path.dirname(path)):
            om.MGlobal.displayError('Path does not exist: {}'.format(path))
            return

        data = {}  # {'bg': path, 'name': name  
                   #  pos(x, y): [label, size, opacity, color, objs]}

        currIndex = self.ui.main_tabWidget.indexOf(layout)
        currTabText = self.ui.main_tabWidget.tabText(currIndex)

        # set name
        data['name'] = currTabText

        # set bg data
        pixmap = layout.pixmapItem.pixmap()
        ba = QtCore.QByteArray()
        buff = QtCore.QBuffer(ba)
        buff.open(QtCore.QIODevice.WriteOnly) 
        pixmap.save(buff, "PNG")
        pixmap_bytes = ba.data()
        data['bg'] = pixmap_bytes

        for button in layout.buttons:
            scenePos = button.scenePos()
            x = scenePos.x()
            y = scenePos.y()
            label = str(button.text.toPlainText())
            rect = button.rect()
            size = [button.scaleX, button.scaleY]
            opacity = button.opacity()
            color = [button.color.red(), button.color.green(), button.color.blue()]
            if isinstance(button, NuPickerButton):
                exe = button.objs
            else:
                exe = '<{}>{}'.format(button.language, button.cmd)
            data[(x, y)] = [label, size, opacity, color, exe]

        with open(path, 'wb') as handle:
            pickle.dump(data, handle)

        # set tool tip
        layout.loadedFrom = path
        tabBar = self.ui.main_tabWidget.tabBar()
        indx = tabBar.currentIndex()
        tabBar.setTabToolTip(indx, layout.loadedFrom)

        print('Saved: {}'.format(path))

    def load(self, path):
        path = os.path.normpath(path)
        if not os.path.exists(path):
            om.MGlobal.displayError('Path does not exist: {}'.format(path))
            return

        # new tab
        layout, index = self.newTab()
        layout.loadedFrom = path

        # set tool tip
        tabBar = self.ui.main_tabWidget.tabBar()
        indx = tabBar.currentIndex()
        tabBar.setTabToolTip(indx, layout.loadedFrom)

        # read data from pickle file
        data = None
        with open(path, 'rb') as handle:
            data = pickle.load(handle)

        if not data:
            return

        # set tab name
        if 'name' in data:
            tabName = data['name']
        else:
            tabName = os.path.splitext(os.path.basename(path))[0]
        self.ui.main_tabWidget.setTabText(index, tabName)

        # clear the layout
        layout.scene.clear()
        layout.buttons = []

        # try to set background
        if 'bg' in data:
            layout.setBackground(data=data['bg'])
        del data['name']
        del data['bg']
        for key, value in data.iteritems():
            value.append(key)
            layout.createButtonFromData(data=value)

        self.createScriptJob(layout)
        self.default_file_dir = os.path.dirname(path)
        print('Loaded: {}'.format(path))

def scriptJobWatch():
    pm.undoInfo(stateWithoutFlush=False)
    
    sels = mc.ls(sl=True, l=True, type='transform')
    global watchButtons
    global activeTab
    activeTab.displayOnly = True
    for b in watchButtons:
        b.setSelected(False)

    lenSels = len(sels)

    for b, objs in watchButtons.iteritems():
        lenObjs = len(objs)
        if lenObjs > lenSels:
            continue

        f = 0
        for s in sels:
            for obj in objs:
                if s.endswith(obj) or obj.endswith(s.split('|')[-1]):
                    f += 1
                    break

        if f == lenObjs:
            b.setSelected(True)

    activeTab.displayOnly = False
    pm.undoInfo(stateWithoutFlush=True)

