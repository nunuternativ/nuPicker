# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\dev\core\rf_maya\nuTools\util\nuPicker\ui\cmdDialog.ui'
#
# Created: Fri Jan 04 14:17:33 2019
#      by: pyside2-uic  running on PySide2 2.0.0~alpha0
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_cmd_dialog(object):
    def setupUi(self, cmd_dialog):
        cmd_dialog.setObjectName("cmd_dialog")
        cmd_dialog.resize(450, 200)
        self.gridLayout = QtWidgets.QGridLayout(cmd_dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.cmd_textEdit = QtWidgets.QTextEdit(cmd_dialog)
        self.cmd_textEdit.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.cmd_textEdit.setFrameShape(QtWidgets.QFrame.WinPanel)
        self.cmd_textEdit.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.cmd_textEdit.setObjectName("cmd_textEdit")
        self.gridLayout.addWidget(self.cmd_textEdit, 0, 0, 1, 1)
        self.main_buttonBox = QtWidgets.QDialogButtonBox(cmd_dialog)
        self.main_buttonBox.setOrientation(QtCore.Qt.Vertical)
        self.main_buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.main_buttonBox.setObjectName("main_buttonBox")
        self.gridLayout.addWidget(self.main_buttonBox, 0, 1, 1, 1)
        self.language_horizontalLayout = QtWidgets.QHBoxLayout()
        self.language_horizontalLayout.setSpacing(50)
        self.language_horizontalLayout.setContentsMargins(50, -1, -1, -1)
        self.language_horizontalLayout.setObjectName("language_horizontalLayout")
        self.mel_radioButton = QtWidgets.QRadioButton(cmd_dialog)
        self.mel_radioButton.setChecked(True)
        self.mel_radioButton.setObjectName("mel_radioButton")
        self.language_horizontalLayout.addWidget(self.mel_radioButton)
        self.python_radioButton = QtWidgets.QRadioButton(cmd_dialog)
        self.python_radioButton.setObjectName("python_radioButton")
        self.language_horizontalLayout.addWidget(self.python_radioButton)
        self.gridLayout.addLayout(self.language_horizontalLayout, 1, 0, 1, 1)

        self.retranslateUi(cmd_dialog)
        QtCore.QObject.connect(self.main_buttonBox, QtCore.SIGNAL("accepted()"), cmd_dialog.accept)
        QtCore.QObject.connect(self.main_buttonBox, QtCore.SIGNAL("rejected()"), cmd_dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(cmd_dialog)

    def retranslateUi(self, cmd_dialog):
        cmd_dialog.setWindowTitle(QtWidgets.QApplication.translate("cmd_dialog", "Bind command button", None, -1))
        self.mel_radioButton.setText(QtWidgets.QApplication.translate("cmd_dialog", "MEL", None, -1))
        self.python_radioButton.setText(QtWidgets.QApplication.translate("cmd_dialog", "Python", None, -1))

