import sys
import os
import time
import pickle
import csv
from datetime import datetime

try:
    import PySide2
except ImportError:
    sys.exit("Please install PySide!")

try:
    import matplotlib
except ImportError:
    sys.exit("Please install matplotlib!")

# Ordner 'common' zur Pfadvariable hinzufuegen
# Logging
import logging
logging.basicConfig(format="[%(levelname)s] [%(asctime)s] %(message)s", level=logging.INFO)


from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
matplotlib.use('tkagg')

class Window(QDialog):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        #INIT parameter
        self.__ic = None
        self.__pklFile = "icGUI.pkl"
        self.__defaultIp = "192.168.1.101"
        self.__demoMode = True
        self.__refresh_interval_s = 0.01
        self.__isConnected = False
        self.__isScanningStarted = False
        self.__isMultiScanStarted = False
        self.__timer = QTimer()
        self.__timer.timeout.connect(self.__update)
        self.__x = []
        self.__y = []
        self.__xPlot = []
        self.__code = []
        self.__coordinates = []
        self.__scanRemote = None
        self.__plotScanCount = 0
        self.__scanCount = 0
        self.__configuration = None
        self.__isInitialized = False
        self.__saveWhenFinished = True
        self.__isScanRoutineStarted = False
        self.__isAlreadySaved = False
        self.__locationSingleScan = "unknown"
        self.__plotUpdate = False
        self.__plotUpdaterCounter = 0
        self.__livePlot = True

        #CONFIG parameter
        self.__filename = "scanDataExport_"
        self.simScanner = 'Disable'
        self.simSetData = 'Enable'
        self.speedAutosampler = '100'
        self.__plotTimeout = 1
        self.__resourceExtensionSwitch = "AutosamplerExtensionSwitch"
        self.__resourceAutosampler = "Autosampler"

        self.__traycode = [165, 70]
        self.__rack4code = [20.2, 110]
        self.__rack3code = [20.2, 200]
        self.__rack2code = [20.2, 303]
        self.__rack1code = [20.2, 389]

        self.__location = [
            "TrayCode",
            "Rack4Code",
            "Rack3Code",
            "Rack2Code",
            "Rack1Code"
        ]

        minimumHeight = 900
        widgetLeftHeight = 380
        labelPaneMinimumWidth = 220
        controlPaneMinimumWidth = 300
        controlPane2MinimumWidth = 100
        widthLabelSmall = 100
        buttonMinimumWidth = 150
        buttonMinimumHeight = 30

        self.setMinimumHeight(minimumHeight)

        # a figure instance to plot on
        self.__figure = Figure()

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.__canvas = FigureCanvas(self.__figure)
        self.__canvas.setMinimumHeight(300)

        # Logo
        self.__logo = QLabel()
        self.__logo.setMinimumHeight(40)
        self.__logo.setMaximumHeight(40)
        # noinspection PyArgumentList
        self.__logo.setPixmap(QPixmap("Logo_Metrohm_small.png"))

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.__toolbar = NavigationToolbar(self.__canvas, self)

        # textbox status text
        self.__statusTextEdit = QTextEdit()
        self.__statusTextEdit.setReadOnly(True)
        self.__statusTextEdit.setMaximumHeight(25)

        # label scan
        self.__scanLabel = QLabel()
        self.__scanLabel.setMaximumHeight(25)
        self.__scanLabel.setMinimumWidth(labelPaneMinimumWidth)
        self.__scanLabel.setText("Scanned Devices")

        # combobox scan
        self.__scanCombobox = QComboBox()
        self.__scanCombobox.setMaximumHeight(25)
        self.__scanCombobox.setMaximumWidth(300)
        self.__scanCombobox.setMinimumWidth(controlPaneMinimumWidth)
        self.__scanCombobox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.__scanCombobox.currentIndexChanged.connect(self.__deviceChanged)

        # label ip
        self.__ipLabel = QLabel()
        self.__ipLabel.setMaximumHeight(25)
        self.__ipLabel.setMinimumWidth(labelPaneMinimumWidth)
        self.__ipLabel.setText("IP-Adress")

        # textbox ip
        self.__ipTextEdit = QTextEdit()
        self.__ipTextEdit.setReadOnly(False)
        self.__ipTextEdit.setMaximumHeight(25)
        self.__ipTextEdit.setMaximumWidth(300)
        self.__ipTextEdit.setMinimumWidth(controlPaneMinimumWidth)

        # label TargetPositionX
        self.__targetPosXLabel = QLabel()
        self.__targetPosXLabel.setMaximumHeight(25)
        self.__targetPosXLabel.setMinimumWidth(labelPaneMinimumWidth)
        self.__targetPosXLabel.setText("Target Position X")

        # textbox TargetPositionX
        self.__targetPosXTextEdit = QTextEdit()
        self.__targetPosXTextEdit.setReadOnly(False)
        self.__targetPosXTextEdit.setMaximumHeight(25)
        self.__targetPosXTextEdit.setMaximumWidth(300)
        self.__targetPosXTextEdit.setMinimumWidth(controlPaneMinimumWidth)

        # label TargetPositionY
        self.__targetPosYLabel = QLabel()
        self.__targetPosYLabel.setMaximumHeight(25)
        self.__targetPosYLabel.setMinimumWidth(labelPaneMinimumWidth)
        self.__targetPosYLabel.setText("Target Position Y")

        # textbox TargetPositionY
        self.__targetPosYTextEdit = QTextEdit()
        self.__targetPosYTextEdit.setReadOnly(False)
        self.__targetPosYTextEdit.setMaximumHeight(25)
        self.__targetPosYTextEdit.setMaximumWidth(300)
        self.__targetPosYTextEdit.setMinimumWidth(controlPaneMinimumWidth)

        # label TargetLocation
        self.__targetLocationLabel = QLabel()
        self.__targetLocationLabel.setMaximumHeight(25)
        self.__targetLocationLabel.setMinimumWidth(labelPaneMinimumWidth)
        self.__targetLocationLabel.setText("Target Location")

        # combobox TargetLocation
        self.__targetLocationCombobox = QComboBox()
        self.__targetLocationCombobox.setMaximumHeight(25)
        self.__targetLocationCombobox.setMaximumWidth(300)
        self.__targetLocationCombobox.setMinimumWidth(controlPaneMinimumWidth)
        self.__targetLocationCombobox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        for item in self.__location:
            self.__targetLocationCombobox.addItem(item)
        self.__targetLocationCombobox.currentIndexChanged.connect(self.__locationChanged)

        # label settings light
        self.__lightSettingLabel = QLabel()
        self.__lightSettingLabel.setMaximumHeight(25)
        self.__lightSettingLabel.setMinimumWidth(labelPaneMinimumWidth)
        self.__lightSettingLabel.setText("Settings Light")

        # combobox Illumination
        self.__illuminationCombobox = QComboBox()
        self.__illuminationCombobox.setMaximumHeight(25)
        self.__illuminationCombobox.setMaximumWidth(300)
        self.__illuminationCombobox.setMinimumWidth(controlPane2MinimumWidth)
        self.__illuminationCombobox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.__illuminationCombobox.addItem("LightOn")
        self.__illuminationCombobox.addItem("LightOff")
        self.__illuminationCombobox.currentIndexChanged.connect(self.__illuminationChanged)

        # combobox ScannerLight
        self.__scannerLightCombobox = QComboBox()
        self.__scannerLightCombobox.setMaximumHeight(25)
        self.__scannerLightCombobox.setMaximumWidth(300)
        self.__scannerLightCombobox.setMinimumWidth(controlPane2MinimumWidth)
        self.__scannerLightCombobox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.__scannerLightCombobox.addItem("ScanlightNoReflexion")
        self.__scannerLightCombobox.addItem("ScanlightOn")
        self.__scannerLightCombobox.addItem("ScanlightOff")
        self.__scannerLightCombobox.currentIndexChanged.connect(self.__scannerLightChanged)

        # label settings data
        self.__dataSettingLabel = QLabel()
        self.__dataSettingLabel.setMaximumHeight(25)
        self.__dataSettingLabel.setMinimumWidth(labelPaneMinimumWidth)
        self.__dataSettingLabel.setText("Settings Data")

        # checkbox savewhenfinished
        self.__checkBoxSave = QCheckBox('Save Data')
        self.__checkBoxSave.stateChanged.connect(self.__checkBoxSaveChanged)
        self.__checkBoxSave.setChecked(True)

        # checkbox savewhenfinished
        self.__livePlotCheckBox = QCheckBox('Live Plot')
        self.__livePlotCheckBox.stateChanged.connect(self.__livePlotCheckBoxChanged)
        self.__livePlotCheckBox.setChecked(True)

        # textbox PlotTimeout
        self.__plotTimeoutTextEdit = QTextEdit()
        self.__plotTimeoutTextEdit.setReadOnly(False)
        self.__plotTimeoutTextEdit.setMaximumHeight(25)
        self.__plotTimeoutTextEdit.setMaximumWidth(widthLabelSmall)
        self.__plotTimeoutTextEdit.setMinimumWidth(widthLabelSmall)
        self.__plotTimeoutTextEdit.setText(str(self.__plotTimeout))

        # label ScanCount
        self.__scanCountLabel = QLabel()
        self.__scanCountLabel.setMaximumHeight(25)
        self.__scanCountLabel.setMinimumWidth(labelPaneMinimumWidth)
        self.__scanCountLabel.setText("ScanCount")

        # textbox ScanCount
        self.__scanCountTextEdit = QTextEdit()
        self.__scanCountTextEdit.setReadOnly(False)
        self.__scanCountTextEdit.setMaximumHeight(25)
        self.__scanCountTextEdit.setMaximumWidth(300)
        self.__scanCountTextEdit.setMinimumWidth(controlPaneMinimumWidth)

        # label Code
        self.__codeLabel = QLabel()
        self.__codeLabel.setMaximumHeight(25)
        self.__codeLabel.setMinimumWidth(labelPaneMinimumWidth)
        self.__codeLabel.setText("Scanned Code")

        # textbox Scanned Code
        self.__codeTextEdit = QTextEdit()
        self.__codeTextEdit.setReadOnly(True)
        self.__codeTextEdit.setMaximumHeight(25)
        self.__codeTextEdit.setMaximumWidth(300)
        self.__codeTextEdit.setMinimumWidth(controlPaneMinimumWidth)

        # label Scantime
        self.__timeLabel = QLabel()
        self.__timeLabel.setMaximumHeight(25)
        self.__timeLabel.setMinimumWidth(labelPaneMinimumWidth)
        self.__timeLabel.setText("ScanTime[ms]")

        # textbox Scantime
        self.__timeTextEdit = QTextEdit()
        self.__timeTextEdit.setReadOnly(True)
        self.__timeTextEdit.setMaximumHeight(25)
        self.__timeTextEdit.setMaximumWidth(300)
        self.__timeTextEdit.setMinimumWidth(controlPaneMinimumWidth)

        # label Coordinates
        self.__coordinatesLabel = QLabel()
        self.__coordinatesLabel.setMaximumHeight(25)
        self.__coordinatesLabel.setMinimumWidth(labelPaneMinimumWidth)
        self.__coordinatesLabel.setText("Scanned Coordinates")

        # textbox Thermostat Control
        self.__coordinatesTextEdit = QTextEdit()
        self.__coordinatesTextEdit.setReadOnly(True)
        self.__coordinatesTextEdit.setMaximumHeight(25)
        self.__coordinatesTextEdit.setMaximumWidth(300)
        self.__coordinatesTextEdit.setMinimumWidth(controlPaneMinimumWidth)

        # label Autosampler State
        self.__autosamplerStateLabel = QLabel()
        self.__autosamplerStateLabel.setMaximumHeight(25)
        self.__autosamplerStateLabel.setMinimumWidth(labelPaneMinimumWidth)
        self.__autosamplerStateLabel.setText("Autosampler State: Substate")

        # textbox Autosampler State
        self.__autosamplerStateTextEdit = QTextEdit()
        self.__autosamplerStateTextEdit.setReadOnly(True)
        self.__autosamplerStateTextEdit.setMaximumHeight(25)
        self.__autosamplerStateTextEdit.setMaximumWidth(300)
        self.__autosamplerStateTextEdit.setMinimumWidth(controlPaneMinimumWidth)

        # label Autosampler Error
        self.__autosamplerErrorLabel = QLabel()
        self.__autosamplerErrorLabel.setMaximumHeight(25)
        self.__autosamplerErrorLabel.setMinimumWidth(labelPaneMinimumWidth)
        self.__autosamplerErrorLabel.setText("Autosampler Error")

        # textbox Autosampler Error
        self.__autosamplerErrorTextEdit = QTextEdit()
        self.__autosamplerErrorTextEdit.setReadOnly(True)
        self.__autosamplerErrorTextEdit.setMaximumHeight(25)
        self.__autosamplerErrorTextEdit.setMaximumWidth(300)
        self.__autosamplerErrorTextEdit.setMinimumWidth(controlPaneMinimumWidth)

        # button scan
        self.__buttonScan = QPushButton('Scan')
        self.__buttonScan.clicked.connect(self.__scanClick)
        self.__buttonScan.setMinimumWidth(buttonMinimumWidth)
        self.__buttonScan.setMinimumHeight(buttonMinimumHeight)

        # button connect
        self.__buttonConnect = QPushButton('Connect')
        self.__buttonConnect.clicked.connect(self.__connectClick)
        self.__buttonConnect.setMinimumWidth(buttonMinimumWidth)
        self.__buttonConnect.setMinimumHeight(buttonMinimumHeight)

        # button disconnect
        self.__buttonDisconnect = QPushButton('Disconnect')
        self.__buttonDisconnect.clicked.connect(self.__disconnectClick)
        self.__buttonDisconnect.setMinimumWidth(buttonMinimumWidth)
        self.__buttonDisconnect.setMinimumHeight(buttonMinimumHeight)

        # button initialize
        self.__buttonInitialize = QPushButton('Initialize')
        self.__buttonInitialize.clicked.connect(self.__initializeClick)
        self.__buttonInitialize.setMinimumWidth(buttonMinimumWidth)
        self.__buttonInitialize.setMinimumHeight(buttonMinimumHeight)

        # button moveXY
        self.__buttonMoveXY = QPushButton('MoveXY')
        self.__buttonMoveXY.clicked.connect(self.__moveXYClick)
        self.__buttonMoveXY.setMinimumWidth(buttonMinimumWidth)
        self.__buttonMoveXY.setMinimumHeight(buttonMinimumHeight)

        # button scanShot
        self.__buttonScanShot = QPushButton('ScanShot')
        self.__buttonScanShot.clicked.connect(self.__scanShotClick)
        self.__buttonScanShot.setMinimumWidth(buttonMinimumWidth)
        self.__buttonScanShot.setMinimumHeight(buttonMinimumHeight)

        # button start
        self.__buttonStart = QPushButton('Start')
        self.__buttonStart.clicked.connect(self.__startClick)
        self.__buttonStart.setMinimumWidth(buttonMinimumWidth)
        self.__buttonStart.setMinimumHeight(buttonMinimumHeight)

        # button stop
        self.__buttonStop = QPushButton('Stop')
        self.__buttonStop.clicked.connect(self.__stopClick)
        self.__buttonStop.setMinimumWidth(buttonMinimumWidth)
        self.__buttonStop.setMinimumHeight(buttonMinimumHeight)

        # button clear
        self.__buttonClear = QPushButton('Clear graph')
        self.__buttonClear.clicked.connect(self.__clearClick)
        self.__buttonClear.setMinimumWidth(buttonMinimumWidth)
        self.__buttonClear.setMinimumHeight(buttonMinimumHeight)

        hlayoutSettingsScan = QHBoxLayout()
        hlayoutSettingsScan.addWidget(self.__scanLabel)
        hlayoutSettingsScan.addWidget(self.__scanCombobox, 1, Qt.AlignLeft)

        hlayoutSettingsIP = QHBoxLayout()
        hlayoutSettingsIP.addWidget(self.__ipLabel)
        hlayoutSettingsIP.addWidget(self.__ipTextEdit, 1, Qt.AlignLeft)

        hlayoutSettingsTargetPosX = QHBoxLayout()
        hlayoutSettingsTargetPosX.addWidget(self.__targetPosXLabel)
        hlayoutSettingsTargetPosX.addWidget(self.__targetPosXTextEdit, 1, Qt.AlignLeft)

        hlayoutSettingsTargetPosY = QHBoxLayout()
        hlayoutSettingsTargetPosY.addWidget(self.__targetPosYLabel)
        hlayoutSettingsTargetPosY.addWidget(self.__targetPosYTextEdit, 1, Qt.AlignLeft)

        hlayoutSettingsTargetLocation = QHBoxLayout()
        hlayoutSettingsTargetLocation.addWidget(self.__targetLocationLabel)
        hlayoutSettingsTargetLocation.addWidget(self.__targetLocationCombobox, 1, Qt.AlignLeft)

        hlayoutLightSettings = QHBoxLayout()
        hlayoutLightSettings.addWidget(self.__lightSettingLabel)
        hlayoutLightSettings.addWidget(self.__illuminationCombobox, 1, Qt.AlignLeft)
        hlayoutLightSettings.addWidget(self.__scannerLightCombobox, 1, Qt.AlignLeft)

        hlayoutDataSettings = QHBoxLayout()
        hlayoutDataSettings.addWidget(self.__dataSettingLabel)
        hlayoutDataSettings.addWidget(self.__checkBoxSave, 1, Qt.AlignLeft)
        hlayoutDataSettings.addWidget(self.__livePlotCheckBox, 1, Qt.AlignLeft)
        hlayoutDataSettings.addWidget(self.__plotTimeoutTextEdit, 1, Qt.AlignLeft)


        hlayoutSettingScanCount = QHBoxLayout()
        hlayoutSettingScanCount.addWidget(self.__scanCountLabel)
        hlayoutSettingScanCount.addWidget(self.__scanCountTextEdit, 1, Qt.AlignLeft)

        hlayoutSettingScanCode = QHBoxLayout()
        hlayoutSettingScanCode.addWidget(self.__codeLabel)
        hlayoutSettingScanCode.addWidget(self.__codeTextEdit, 1, Qt.AlignLeft)

        hlayoutSettingScanTime = QHBoxLayout()
        hlayoutSettingScanTime.addWidget(self.__timeLabel)
        hlayoutSettingScanTime.addWidget(self.__timeTextEdit, 1, Qt.AlignLeft)

        hlayoutSettingScanCoordiantes = QHBoxLayout()
        hlayoutSettingScanCoordiantes.addWidget(self.__coordinatesLabel)
        hlayoutSettingScanCoordiantes.addWidget(self.__coordinatesTextEdit, 1, Qt.AlignLeft)

        hlayoutSettingsAutosamplerState = QHBoxLayout()
        hlayoutSettingsAutosamplerState.addWidget(self.__autosamplerStateLabel)
        hlayoutSettingsAutosamplerState.addWidget(self.__autosamplerStateTextEdit, 1, Qt.AlignLeft)

        hlayoutSettingsAutosamplerError = QHBoxLayout()
        hlayoutSettingsAutosamplerError.addWidget(self.__autosamplerErrorLabel)
        hlayoutSettingsAutosamplerError.addWidget(self.__autosamplerErrorTextEdit, 1, Qt.AlignLeft)

        vlayoutLeft = QVBoxLayout()
        vlayoutLeft.addLayout(hlayoutSettingsScan)
        vlayoutLeft.addLayout(hlayoutSettingsIP)
        vlayoutLeft.addLayout(hlayoutSettingsTargetPosX)
        vlayoutLeft.addLayout(hlayoutSettingsTargetPosY)
        vlayoutLeft.addLayout(hlayoutSettingsTargetLocation)
        vlayoutLeft.addLayout(hlayoutLightSettings)
        vlayoutLeft.addLayout(hlayoutDataSettings)
        vlayoutLeft.addLayout(hlayoutSettingScanCount)
        vlayoutLeft.addLayout(hlayoutSettingScanCode)
        vlayoutLeft.addLayout(hlayoutSettingScanTime)
        vlayoutLeft.addLayout(hlayoutSettingScanCoordiantes)
        vlayoutLeft.addLayout(hlayoutSettingsAutosamplerState)
        vlayoutLeft.addLayout(hlayoutSettingsAutosamplerError)
        vwidgetLeft = QWidget()  # Hack to control size of vLayoutLef
        vwidgetLeft.setLayout(vlayoutLeft)
        vwidgetLeft.setFixedHeight(widgetLeftHeight)

        vlayoutRight = QVBoxLayout()
        vlayoutRight.addWidget(self.__buttonScan)
        vlayoutRight.addWidget(self.__buttonConnect)
        vlayoutRight.addWidget(self.__buttonDisconnect)
        vlayoutRight.addWidget(self.__buttonInitialize)
        vlayoutRight.addWidget(self.__buttonMoveXY)
        vlayoutRight.addWidget(self.__buttonScanShot)
        vlayoutRight.addWidget(self.__buttonStart)
        vlayoutRight.addWidget(self.__buttonStop)
        vlayoutRight.addWidget(self.__buttonClear)

        hlayoutControl = QHBoxLayout()
        hlayoutControl.addWidget(vwidgetLeft)
        hlayoutControl.addLayout(vlayoutRight)

        # set the vertical layout
        vlayout = QVBoxLayout()
        # vlayout.addWidget(self.__logo)
        vlayout.addWidget(self.__toolbar)
        vlayout.addWidget(self.__canvas)
        vlayout.addWidget(self.__statusTextEdit)
        vlayout.addLayout(hlayoutControl)

        self.setLayout(vlayout)

        # create an axis
        self.__figure.subplots_adjust(bottom=0.25)
        self.__axis = self.__figure.add_subplot(111)
        self.__axis.tick_params(axis='x', labelsize=8, rotation=90)
        self.__axis.tick_params(axis='y', labelsize=8)


        # discards the old graph
        self.__clearPlotData()
        self.__counter = 0
        self.__setStatusConnected(False)
        self.__loadIp()

    def closeEvent(self, event):   # override closeEvent
        if self.__ic is not None:
            self.__ic.disconnect()

    def __scanClick(self):
        self.__scanForDevices()

    def __connectClick(self):
        self.__connect()

    def __disconnectClick(self):
        self.__disconnect(False)

    def __initializeClick(self):
        self.__initializeDevice()

    def __moveXYClick(self):
        self.__moveXY(float(self.__targetPosXTextEdit.toPlainText()), float(self.__targetPosYTextEdit.toPlainText()))
        pass

    def __scanShotClick(self):
        self.__isAlreadySaved = False
        self.__getPlotTimeout()
        self.__makeSingleScans(self.__scanCountTextEdit.toPlainText())
        pass

    def __startClick(self):
        self.__isAlreadySaved = False
        self.__getPlotTimeout()
        scanCount = self.__scanCountTextEdit.toPlainText()
        if(scanCount!="" and int(scanCount)>0 and scanCount!=None):
            self.__scanCount = int(scanCount)
        self.__isScanRoutineStarted = True
        self.__startScan()

    def __stopClick(self):
        self.__getPlotTimeout()
        self.__stopScan()

    def __clearClick(self):
        self.__clear()

    def __deviceChanged(self, index):
        text = self.__scanCombobox.currentText()
        devices = text.split(" | ")
        for keys in devices:
            if keys in self.__devices:
                ip = self.__devices[keys]
                self.__ipTextEdit.setText(ip)
                print("set ip: " + str(ip))

    def __locationChanged(self, index):
        text = self.__targetLocationCombobox.currentText()
        coordinates = self.__translateLocationToCoordinates(text)
        self.__targetPosXTextEdit.setText(str(coordinates[0]))
        self.__targetPosYTextEdit.setText(str(coordinates[1]))

    def __illuminationChanged(self, index):
        text = self.__illuminationCombobox.currentText()
        if 'on' in text.lower():
            self.__ic.get_node(self.__resourceExtensionSwitch).resources['Illumination']['0'].setData('ON')
        else:
            self.__ic.get_node(self.__resourceExtensionSwitch).resources['Illumination']['0'].setData('OFF')

    def __scannerLightChanged(self, index):
        text = self.__scannerLightCombobox.currentText()
        if 'lighton' in text.lower():
            self.__ic.get_node(self.__resourceAutosampler).resources['TrayRackDeveloper']['0'].setScanLight('ENABLE')
        elif 'noreflexion' in text.lower():
            self.__ic.get_node(self.__resourceAutosampler).resources['TrayRackDeveloper']['0'].setScanLight('NOREFLEXION')
        else:
            self.__ic.get_node(self.__resourceAutosampler).resources['TrayRackDeveloper']['0'].setScanLight('DISABLE')

    def __checkBoxSaveChanged(self):
        if(self.__checkBoxSave.isChecked()):
            self.__saveWhenFinished = True
        else:
            self.__saveWhenFinished = False

    def __livePlotCheckBoxChanged(self):
        if(self.__livePlotCheckBox.isChecked()):
            self.__livePlot = True
        else:
            self.__livePlot = False

    def __translateLocationToCoordinates(self, text):
        text = text.lower()
        if 'traycode' in text:
            return self.__traycode
        if 'rack4code' in text:
            return self.__rack4code
        if 'rack3code' in text:
            return self.__rack3code
        if 'rack2code' in text:
            return self.__rack2code
        if 'rack1code' in text:
            return self.__rack1code
        else:
            return [0,0]

    def __scanForDevices(self):
        self.__scanCombobox.clear()
        self.__devices = {}
        devices = self.__scanRemote.makeScan(device_type='')
        for dev in devices:
            #print(dev)
            text = str(dev['name']) + " | " + dev['ip']
            self.__devices[dev['name']] = dev['ip']
            print(text)
            self.__scanCombobox.addItem(text)

    def __connect(self):
        self.__scanCombobox.clear()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.__ip = self.__ipTextEdit.toPlainText()

        try:
            self.__ic = Ic(ip=self.__ip)
            self.__ic.set_configuration(self.__configuration.nodeConfiguration)
            self.__isConnected = True
            self.__updateSetting()
            self.__timer.start(self.__refresh_interval_s * 1000)

        except Exception as e:
            self.__showStatusMsg(str(e))
            self.__disconnect(True)
            QApplication.restoreOverrideCursor()
            return

        self.__showStatusMsg("Connection to device succeeded")
        self.__setStatusConnected(True)
        self.__saveIp()
        QApplication.restoreOverrideCursor()

    def __disconnect(self, silent=False):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.__isConnected = False
        if(not self.__isAlreadySaved):
            self.__saveDataCsv(self.__filename)
        if self.__ic is not None:
            self.__ic.disconnect()
            self.__ic = None

        self.__setStatusConnected(False)
        if not silent:
            self.__clear()
            self.__showStatusMsg("Device disconnected")
        QApplication.restoreOverrideCursor()

    def __clear(self):
        self.__clearPlotData()
        self.__canvas.draw()
        self.__clearStatusMsg()

    def __initializeDevice(self):
        self.__showStatusMsg("Initialize started")
        self.__isInitialized = True
        self.__ic.get_node(self.__resourceAutosampler).resources['AxesControl']['0'].initialize()
        self.__ic.get_node(self.__resourceAutosampler).resources['TrayRackControl']['0'].initialize()
        self.__ic.get_node(self.__resourceAutosampler).setSimScanner_TrayRackDeveloper(self.simScanner)
        self.__ic.get_node(self.__resourceAutosampler).setSimSetData_TrayRackDeveloper(self.simSetData)

    def __startScan(self):
        #start(self, targetTemperature='10', dataInterval='1', measPointIntervalMode='ON', measPointInterval='2'):
        self.__ic.get_node('Autosampler').start_TrayRackControl()
        if(self.__scanCount>0):
            self.__scanCount = self.__scanCount - 1
        self.__showStatusMsg("Scan started")

    def __stopScan(self):
        if(self.__isScanRoutineStarted or self.__isMultiScanStarted):
            self.__ic.get_node('Autosampler').resources['TrayRackControl']['0'].stop()
        if(self.__isMultiScanStarted):
            self.__stopMultiScan()
        else:
            self.__plotUpdateData()
            if (self.__saveWhenFinished and not self.__isAlreadySaved):
                self.__saveDataCsv(self.__filename)
        self.__isScanRoutineStarted = False
        self.__scanCount = 0
        self.__showStatusMsg("Scan stopped")

    def __makeSingleScans(self, scanCount = None):
        if(scanCount!="" and scanCount!=0 and scanCount!=None):
            self.__startMultiScan(int(scanCount))
        else:
            #make single scan shot
            self.__ic.get_node('Autosampler').resources['TrayRackDeveloper']['0'].scanSingle()

    def __startMultiScan(self, scanCount):
        self.__isMultiScanStarted = True
        self.__scanCount = scanCount
        self.__showStatusMsg("MultiScan Started: Scans " + str(scanCount))
        self.__makeScanShot() #trigger frist scan


    def __stopMultiScan(self):
        self.__plotUpdateData()
        if(self.__isMultiScanStarted):
            self.__showStatusMsg("MultiScan finished")
            self.__isMultiScanStarted = False
        self.__plotScanCount = 0
        self.__scanCount = 0
        if(self.__saveWhenFinished):
            self.__saveDataCsv(self.__filename)

    def __finishScanRoutine(self):
        self.__isScanRoutineStarted = False
        self.__plotScanCount = 0
        if(self.__saveWhenFinished):
            self.__saveDataCsv(self.__filename)


    def __makeScanShot(self):
        time.sleep(0.01)
        self.__ic.get_node('Autosampler').resources['TrayRackDeveloper']['0'].scanSingle()
        self.__scanCount = self.__scanCount-1
        self.__showStatusMsg("MultiScan Running: Scan " + str(self.__scanCount))


    def __moveXY(self, targetPosX, targetPosY):
        self.__ic.get_node('Autosampler').resources['AxesControl']['0'].moveXY(targetPosX, targetPosY, self.speedAutosampler, self.speedAutosampler)
        self.__setLocationDeveloper(targetPosX, targetPosY)

    def __setLocationDeveloper(self,targetPosX, targetPosY):
        self.__locationSingleScan = self.__targetLocationCombobox.currentText()+" X:"+str(targetPosX)+" Y:"+str(targetPosY)
        print(self.__locationSingleScan)

    def __getPlotTimeout(self):
        plotTimeout = self.__plotTimeoutTextEdit.toPlainText()
        if(plotTimeout!="" and float(plotTimeout)>0 and plotTimeout!=None):
            self.__plotTimeout = float(plotTimeout)

    def __is_number(self, s):
        if(s.replace('.', '', 1).isdigit()):
            return True
        else:
            return False

    def __clearPlotData(self):
        self.__x = []
        self.__xPlot = []
        self.__y = []
        self.__code = []
        self.__coordinates = []
        self.__location = []
        self.__clearPlot()
        self.__plotScanCount = 0
        self.__canvas.draw()      # refresh canvas

    def __clearPlot(self):
        self.__axis.clear()
        self.__axis.set_title("ScanTime")
        self.__axis.set_xlabel(xlabel = "ScanCount")
        self.__axis.set_ylabel(ylabel = "Time [ms]")
        self.__axis.tick_params(axis='x', labelsize=8, rotation=75)
        self.__axis.tick_params(axis='y', labelsize=8)

    def __plotScannedData(self, data, location):
        code = data['Code']
        scantime = data['ScanTime']
        self.__x.append(self.__plotScanCount)
        if(code != "NOCODE" and code != "ERROR"):
            self.__y.append(int(scantime))
        else:
            self.__y.append(3999)
        self.__xPlot.append(str(self.__plotScanCount)+" "+location)
        self.__location.append(location)
        self.__code.append(code)
        self.__coordinates.append("X:"+data['CodeCoordinateX']+ " Y:"+data['CodeCoordinateY'])
        self.__plotScanCount = self.__plotScanCount+1
        if(self.__plotUpdate and self.__livePlot):
            self.__clearPlot()
            self.__axis.bar(self.__xPlot,self.__y)
            self.__axis.plot()    # plot data
            self.__canvas.draw()      # refresh canvas
            self.__plotUpdate = False

    def __plotUpdateData(self):
        if(self.__livePlot):
            self.__clearPlot()
            self.__axis.bar(self.__xPlot, self.__y)
            self.__axis.plot()  # plot data
            self.__canvas.draw()  # refresh canvas

    def __setData_EventDataCode(self, data):
        self.__codeTextEdit.setText(data['Code'])
        self.__timeTextEdit.setText(data['ScanTime'])
        self.__coordinatesTextEdit.setText("X: "+data['CodeCoordinateX']+" / Y: "+data['CodeCoordinateY'])

    def __setData_EventState(self, data):
        self.__autosamplerStateTextEdit.setText(data['State'] + ": " + data['SubState'])

    def __setData_EventWarning(self, data):
        self.__thermostatWarningTextEdit.setText(data['Warning'])

    def __setData_EventComplete(self, data):
        if(data['Error'] != 'None'):
            self.__showStatusMsg("Complete Error: "+data['Error'])
        self.__autosamplerErrorTextEdit.setText(data['Error'])

    def __saveDataCsv(self, fileName):
        fileName = fileName+datetime.now().strftime('%Y%m%d_%H%M%S')
        if(fileName[:4].lower() != ".csv"):
            fileName = fileName+".csv"
        self.__showStatusMsg("Save Scandata: "+fileName)
        self.__isAlreadySaved = True
        folderpath = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(folderpath,fileName), mode='w', newline='') as scanData_file:
            #scanData_writer = csv.writer(sys.stderr)
            scanData_writer = csv.writer(scanData_file, dialect='excel', delimiter=';')
            header = ['ScanCount', 'Location', 'ScanTime [ms]', 'ScannedCode', 'ScanCoordinates']
            scanData_writer.writerow(header)
            for index, value in enumerate(self.__x, start=0):
                writerDict = [self.__x[index], self.__location[index],self.__y[index], self.__code[index], self.__coordinates[index]]
                scanData_writer.writerow(writerDict)

    def __updateSetting(self):
        self.__illuminationChanged(0)
        self.__locationChanged(0)
        self.__scannerLightChanged(0)

    def __showStatusMsg(self, message):
        self.__statusTextEdit.setText(time.strftime("%H:%M:%S") + "  " + message)

    def __clearStatusMsg(self):
        self.__statusTextEdit.setText("")

    def __setStatusConnected(self, connected):
        if connected:
            self.__ipTextEdit.setEnabled(False)
            self.__buttonConnect.setHidden(True)
            self.__buttonDisconnect.setHidden(False)
            self.__buttonInitialize.setEnabled(True)
            self.__buttonMoveXY.setEnabled(True)
            self.__buttonScanShot.setEnabled(True)
            self.__buttonStart.setEnabled(True)
            self.__buttonStop.setEnabled(True)
            self.__buttonClear.setEnabled(True)

            self.__targetPosXTextEdit.setEnabled(True)
            self.__targetPosYTextEdit.setEnabled(True)
            self.__targetLocationCombobox.setEnabled(True)
            self.__illuminationCombobox.setEnabled(True)
            self.__scannerLightCombobox.setEnabled(True)
            self.__checkBoxSave.setEnabled(True)
            self.__livePlotCheckBox.setEnabled(True)
            self.__scanCountTextEdit.setEnabled(True)
            self.__plotTimeoutTextEdit.setEnabled(True)
            self.__codeTextEdit.setEnabled(True)
            self.__timeTextEdit.setEnabled(True)
            self.__coordinatesTextEdit.setEnabled(True)
            self.__autosamplerStateTextEdit.setEnabled(True)
            self.__autosamplerErrorTextEdit.setEnabled(True)
        else:
            self.__ipTextEdit.setEnabled(True)
            self.__buttonConnect.setHidden(False)
            self.__buttonDisconnect.setHidden(True)
            self.__buttonInitialize.setEnabled(False)
            self.__buttonMoveXY.setEnabled(False)
            self.__buttonScanShot.setEnabled(False)
            self.__buttonStart.setEnabled(False)
            self.__buttonStop.setEnabled(False)
            self.__buttonClear.setEnabled(False)

            self.__targetPosXTextEdit.setEnabled(False)
            self.__targetPosYTextEdit.setEnabled(False)
            self.__targetLocationCombobox.setEnabled(False)
            self.__illuminationCombobox.setEnabled(False)
            self.__scannerLightCombobox.setEnabled(False)
            self.__checkBoxSave.setEnabled(False)
            self.__livePlotCheckBox.setEnabled(False)
            self.__scanCountTextEdit.setEnabled(False)
            self.__plotTimeoutTextEdit.setEnabled(False)
            self.__codeTextEdit.setEnabled(False)
            self.__timeTextEdit.setEnabled(False)
            self.__coordinatesTextEdit.setEnabled(False)
            self.__autosamplerStateTextEdit.setEnabled(False)
            self.__autosamplerErrorTextEdit.setEnabled(False)

    def __loadIp(self):
        # noinspection PyBroadException
        try:
            f = open(self.__pklFile, 'rb')
            ip = pickle.load(f)
            f.close()
            self.__ipTextEdit.setText(ip)
        except Exception:
            self.__ipTextEdit.setText(self.__defaultIp)
        return

    def __saveIp(self):
        f = open(self.__pklFile, "wb")
        ip = self.__ipTextEdit.toPlainText()
        pickle.dump(ip, f)
        f.close()

    def __update(self):
        self.__plotUpdaterCounter = self.__plotUpdaterCounter + 1
        if(self.__plotUpdaterCounter>self.__plotTimeout/self.__refresh_interval_s):
            self.__plotUpdate = True
            self.__plotUpdaterCounter = 0
        while True:
                if(self.__isConnected):
                    event_data_autosampler = self.__ic.get_node(self.__resourceAutosampler).resources['AxesControl']['0'].receive_next_event(self, wait=False)
                    event_data_trayRackDeveloper = self.__ic.get_node(self.__resourceAutosampler).resources['TrayRackDeveloper']['0'].receive_next_event(self, wait=False)
                    # event_data_trayRack = None
                    # if(self.__isInitialized or self.__isScanRoutineStarted):
                    event_data_trayRack = self.__ic.get_node(self.__resourceAutosampler).resources['TrayRackControl']['0'].receive_next_event(self, wait=False)
                    if(self.__isMultiScanStarted):
                        event_data_trayRack = None
                    if(event_data_autosampler):
                        if event_data_autosampler['EventName'] == 'State':
                            data = event_data_autosampler['Data']
                            print("STATE_EVENT AUTOSAMPLER: "+str(data))
                            self.__setData_EventState(data)
                        if event_data_autosampler['EventName'] == 'Warning':
                            data = event_data_autosampler['Data']
                            print("WARNING_EVENT AUTOSAMPLER: "+str(data))
                            #self.__setData_EventWarning(data)
                        if event_data_autosampler['EventName'] == 'Complete':
                            data = event_data_autosampler['Data']
                            print("COMPLETE_EVENT AUTOSAMPLER: "+str(data))
                            self.__setData_EventComplete(data)
                    elif(event_data_trayRack):
                        if event_data_trayRack['EventName'] == 'Complete':
                            data = event_data_trayRack['Data']
                            self.__setData_EventComplete(data)
                            self.__isInitialized = False
                            print("COMPLETE_EVENT TRAYRACK: " + str(data))
                            if(self.__isScanRoutineStarted and self.__scanCount>0):
                                self.__startScan()
                            elif(self.__isScanRoutineStarted):
                                self.__finishScanRoutine()
                            #self.__setData_EventComplete(data)
                    elif(event_data_trayRackDeveloper):
                        if event_data_trayRackDeveloper['EventName'] == 'BarcodeScanned':
                            data = event_data_trayRackDeveloper['Data']
                            print("DEV_BARCODESCANNED_EVENT: " + str(data))
                            self.__setData_EventDataCode(data)
                            if(data['Code'].lower() == 'error'):
                                self.__plotScannedData(data, data['Location'])
                                self.__stopScan()  #stop if scanCount = 0
                            else:
                                if(self.__scanCount>0 and self.__isMultiScanStarted):
                                    self.__plotScannedData(data, self.__locationSingleScan)
                                    self.__makeScanShot()   #trigger next scanShot
                                elif(self.__isMultiScanStarted):
                                    self.__plotScannedData(data, self.__locationSingleScan)
                                    self.__stopMultiScan()  #stop if scanCount = 0
                                else:
                                    self.__plotScannedData(data, data['Location'])

                    else:
                        break
                else:
                    self.__timer.stop()
                    break;

if __name__ == '__main__':
    # Update aufsetzen
    app = QApplication(sys.argv)
    main = Window()
    main.setWindowTitle('Autosampler TestGui')
    main.setWindowFlags(Qt.Window)  # http://doc.qt.io/qt-5/qtwidgets-widgets-windowflags-example.html
    main.show()
    sys.exit(app.exec_())
