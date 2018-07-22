#!/home/pi/.virtualenvs/cv2/bin/python3
# -*- coding: utf-8 -*-

'''
PiCameraApp.py
Copyright (C) 2015 - Bill Williams

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
'''

'''
	1.)	LED control no longer works on RPI 3 Model B
		The camera LED cannot currently be controlled when the module is
		attached to a Raspberry Pi 3 Model B as the GPIO that controls the
		LED has moved to a GPIO expander not directly accessible to the
		ARM processor.
	2.)
'''

########### TODO: Standardize variable, class, member cases

import time
import datetime
import webbrowser		# display the Picamera documentation
import io
import time
import os
from time import time, sleep
from Tooltip	import *
from	AnnotationOverlay	import *

#~ try:
import RPi.GPIO
#~ except ImportError:
	#~ RPiGPIO = False
'''
From PiCamera ver 1.3 documentation
https://picamera.readthedocs.io/en/release-1.13/recipes1.html
Be aware when you first use the LED property it will set the GPIO
library to Broadcom (BCM) mode with GPIO.setmode(GPIO.BCM) and disable
warnings with GPIO.setwarnings(False). The LED cannot be controlled when
the library is in BOARD mode.
'''

try:
	import 	picamera
	from 		picamera import *
	import 	picamera.array
except ImportError:
	raise ImportError("You do not seem to have picamera installed")

try:
	from Tkinter import *	# Python 2.X
except ImportError:
	from tkinter import *	# Python 3.X
try:
	from 		tkColorChooser import askcolor
except ImportError:
	from		tkinter.colorchooser import askcolor
try:
	import 	tkFileDialog as FileDialog
except ImportError:
	import	tkinter.filedialog as FileDialog
try:
	import 	tkMessageBox as MessageBox
except ImportError:
	import	tkinter.messagebox as MessageBox
try:
	import 	ttk
	from 		ttk import *
except ImportError:
	from		tkinter import ttk
	from 		tkinter.ttk import *
try:
	import 	tkFont
except ImportError:
	import	tkinter.font

# sudo apt-get install python3-pil.imagetk
import PIL
from PIL import Image, ExifTags
try:
	from PIL import ImageTk
except ImportError:
	raise ("ImageTk not installed. If running Python 3.x\n" \
			 "Use: sudo apt-get install python3-pil.imagetk")

from 	AboutDialog import *
from 	PreferencesDialog import *
from	AnnotationOverlay import *
from	KeyboardShortcuts import *
from	Mapping import *
from	NotePage import *
from	CameraUtils import *
from	BasicControls import *
from	FinerControl import *
from	Exposure import *
from	Timelapse import *
from	Utils import *
from    camera_processing import VideoHandler
#from    double_scrollbar_frame import DoubleScrollbarFrame

import tkinter as tk
from tkinter import ttk


class DoubleScrollbarFrame(ttk.Frame):

    def __init__(self, master, **kwargs):
        '''
        Initialisation. The DoubleScrollbarFrame consist of :
          - an horizontal scrollbar
          - a  vertical   scrollbar
          - a canvas in which the user can place sub-elements
        '''

        ttk.Frame.__init__(self,  master, **kwargs)
        
        # Canvas creation with double scrollbar
        self.hscrollbar = ttk.Scrollbar(self, orient = tk.HORIZONTAL)
        self.vscrollbar = ttk.Scrollbar(self, orient = tk.VERTICAL)
        self.sizegrip = ttk.Sizegrip(self)
        self.canvas = tk.Canvas(self, bd=0, highlightthickness=0,
                                yscrollcommand = self.vscrollbar.set,
                                xscrollcommand = self.hscrollbar.set)
        self.vscrollbar.config(command = self.canvas.yview)
        self.hscrollbar.config(command = self.canvas.xview)

    def pack(self, **kwargs):
        '''
        Pack the scrollbar and canvas correctly in order to recreate the same look as MFC's windows. 
        '''

        self.hscrollbar.pack(side=tk.BOTTOM, fill=tk.X, expand=tk.FALSE)
        self.vscrollbar.pack(side=tk.RIGHT, fill=tk.Y,  expand=tk.FALSE)
        self.sizegrip.pack(in_ = self.hscrollbar, side = tk.BOTTOM, anchor = "se")
        self.canvas.pack(side=tk.LEFT, padx=5, pady=5,
                         fill=tk.BOTH, expand=tk.TRUE)
        ttk.Frame.pack(self, **kwargs)

    def get_frame(self):
        '''
        Return the "frame" useful to place inner controls.
        '''
        return self.canvas


class PiCameraApp(Frame):
    ExposureModeText = None
    def __init__(self, root, camera, title):
        Frame.__init__(self, root)
        
        #self.grid(padx=5,pady=5)
        self.root = root
        master = DoubleScrollbarFrame(root, relief="sunken", width=10, height=10)        
        self.ControlMapping = ControlMapping()
        
        self.camera = camera
        self.camera.color_effects = (128, 128)
        self.camera.start_preview(fullscreen=False,window=(0,0,10,10))
        
        self.title = title
        self.root.title(title)
        
        # Add controls here
        ToolTip.LoadToolTips()
        
        #----------- Icons for Menu and Buttons ------------------------
        self.iconClose = GetPhotoImage("Assets/window-close.png")
        #self.iconClose = ImageTk.PhotoImage(PIL.Image.open("Assets/window-close.png"))
        self.iconPrefs = GetPhotoImage('Assets/prefs1_16x16.png')
        self.iconWeb = GetPhotoImage('Assets/web_16x16.png')
        image = PIL.Image.open('Assets/camera-icon.png')
        self.iconCameraBig = GetPhotoImage(image.resize((22,22)))
        self.iconCamera = GetPhotoImage(image.resize((16,16)))
        image = PIL.Image.open('Assets/video-icon-b.png')
        self.iconVideoBig = GetPhotoImage(image.resize((22,22)))
        self.iconVideo = GetPhotoImage(image.resize((16,16)))
        
        #------------ Notebook with all camera control pages -----------
        # frame1 = ttk.Frame(master.get_frame(), padding=(5, 5, 5, 5))
        # frame1.grid(row=0, column=0, sticky='NSEW')
        # frame1.rowconfigure(2, weight=1)
        # frame1.columnconfigure(0, weight=1)
        # txt = ttk.Label(frame1, text="Add things here !")
        
        # self.AlwaysPreview = False
        
        n = Notebook(master.get_frame(),padding=(5,5,5,5), height=500, width=500)
        #n.grid(row=1,column=0,rowspan=2,sticky=(N,E,W,S))
        #n.columnconfigure(0,weight=1)
        n.enable_traversal()
        
        self.BasicControlsFrame = BasicControls(n,camera)
        self.ExposureFrame = Exposure(n,camera)
        self.FinerControlFrame = FinerControl(n,camera)
        #self.TimelapseFrame = Timelapse(n,camera)
        
        n.add(self.BasicControlsFrame ,text='Basic',underline=0)
        n.add(self.ExposureFrame,text='Exposure',underline=0)
        n.add(self.FinerControlFrame,text='Advanced',underline=0)
        #n.add(self.TimelapseFrame,text='Time lapse',underline=0)
        
        self.FinerControlFrame.PassControlFrame(self.BasicControlsFrame)

        #Packing everything
        #txt.pack(anchor='center', fill=tk.Y, expand=tk.Y)
        #frame1.pack(padx=15, pady=15, fill=tk.BOTH, expand=tk.TRUE)
        n.pack(padx=20, pady=20, fill=tk.BOTH, expand=tk.FALSE)
        master.pack(padx=20, pady=20, expand=True, fill=tk.BOTH)
        
        
if __name__ == '__main__':

      # Top-level frame
      root = tk.Tk()
      root.title( "Double scrollbar with tkinter" )
      root.minsize(width=20, height=20)
      #frame = DoubleScrollbarFrame(root, relief="sunken")

      camera = picamera.PiCamera(sensor_mode=1)
      camera.sensor_mode = 0
      app = PiCameraApp(root, camera, title="PiCamera")
      # # Add controls here
      # subframe = ttk.Frame( frame.get_frame() )
      # txt = ttk.Label(subframe, text="Add things here !")

      # #Packing everything
      # txt.pack(anchor = 'center', fill = tk.Y, expand = tk.Y)
      # subframe.pack(padx  = 15, pady   = 15, fill = tk.BOTH, expand = tk.TRUE)
      # frame.pack( padx   = 5, pady   = 5, expand = True, fill = tk.BOTH)

      # launch the GUI
      root.mainloop()

