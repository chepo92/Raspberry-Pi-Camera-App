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

class VerticalScrolledFrame(Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling

    """
    def __init__(self, parent, *args, **kw):
        Frame.__init__(self, parent, *args, **kw)
        
        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = Scrollbar(self, orient=VERTICAL)
        vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
        
        hscrollbar = Scrollbar(self, orient=HORIZONTAL)
        hscrollbar.pack(fill=X, side=BOTTOM, expand=FALSE)
        
        canvas = Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=vscrollbar.set,
                        xscrollcommand=hscrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        vscrollbar.config(command=canvas.yview)
        hscrollbar.config(command=canvas.xview)
        
        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)
        
        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=NW)
        
        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())
            interior.bind('<Configure>', _configure_interior)
                
        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
                canvas.bind('<Configure>', _configure_canvas)

class PiCameraApp(Frame):
    ExposureModeText = None
    def __init__(self, root, camera, title):
        Frame.__init__(self, root)
        
        #self.grid(padx=5,pady=5)
        self.CanvasMouseMove = None
        self.CanvasEnterLeave = None
        self.SetPreviewOn = None
        self.AlphaChanged = None
        self.PreviewOn = None
        self.ToggleVFlip = None
        self.ToggleHFlip = None
        self.RotateCamera = None
        self.SetPreviewLocation = None
        self.WindowSizeChanged = None
        
        self.root = root
        master = VerticalScrolledFrame(root)
        master.pack()

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
        frame1 = ttk.Frame(master.interior, padding=(5, 5, 5, 5))
        frame1.grid(row=0, column=0, sticky='NSEW')
        frame1.rowconfigure(2, weight=1)
        frame1.columnconfigure(0, weight=1)
        # txt = ttk.Label(frame1, text="Add things here !")
        
        # self.AlwaysPreview = False
        
        n = Notebook(frame1,padding=(5,5,5,5))
        n.grid(row=1,column=0,rowspan=2,sticky=(N,E,W,S))
        n.columnconfigure(0,weight=1)
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

        # ----------------------Paned Window ---------------------------
        # Start of Image Canvas preview, camera captures,
        #       Paned Window VERTICAL
        #               TopFrame
        #                       Preview ImageCanvas     row Weight=1
        #                       ButtonFrame
        #                               Preview Buttons
        #               BottomFrame
        #### TODO:      Add title to BottomFrame 'Captured Image/Video'
        #                       PanedWindow HORIZONTAL row 0, col 0
        #                               LeftFrame
        #                                       Camera setups, EXIF Text
        #### TODO:                      ButtonFrame
        #### TODO:                              Clear, Save as File, Save as Python
        #                               RightFrame
        #                                       Current Photo Canvas
        #                       ButtonFrame
        #                               Picture / Video buttons

        self.pw = ttk.PanedWindow(master.interior,orient=VERTICAL,style='TPanedwindow',
                                  takefocus=True)
        self.pw.grid(row=0,column=1,sticky="NSEW")
        self.pw.rowconfigure(0,weight=1)
        self.pw.columnconfigure(0,weight=1)
        
        self.TopFrame = ttk.Frame(self.pw,padding=(5,5,5,5))
        self.TopFrame.grid(row=0,column=0,sticky="NEWS")
        self.TopFrame.rowconfigure(0,weight=1)
        self.TopFrame.columnconfigure(1,weight=1)
        
        #### TODO: Create Canvas Class to handle generic cursors, etc
        self.ImageCanvas = Canvas(self.TopFrame,width=256,height=256,
                                  background=self.ControlMapping.FocusColor,cursor='diamond_cross')
        self.ImageCanvas.grid(row=0,column=0,columnspan=2,sticky="NEWS")
        self.ImageCanvas.itemconfigure('nopreview',state='hidden')
        self.ImageCanvas.bind("<Motion>",self.CanvasMouseMove)
        self.ImageCanvas.bind("<ButtonPress>",self.CanvasMouseMove)
        self.ImageCanvas.bind("<Enter>",self.CanvasEnterLeave)
        self.ImageCanvas.bind("<Leave>",self.CanvasEnterLeave)
        
        ButtonFrame = ttk.Frame(self.TopFrame,padding=(5,5,5,5),relief=SUNKEN)
        ButtonFrame.grid(row=1,column=0,columnspan=2,sticky="NEWS")
        
        self.PreviewOn = MyBooleanVar(True)
        self.enablePrev = ttk.Checkbutton(ButtonFrame,text='Preview',variable=self.PreviewOn,
                                          command=self.SetPreviewOn)
        self.enablePrev.grid(row=0,column=0,padx=5,sticky='W')
        ToolTip(self.enablePrev, msg=1)
        l2 = Label(ButtonFrame,text="Alpha:")
        l2.grid(column=1,row=0,sticky='W')
        self.alpha = ttk.Scale(ButtonFrame,from_=0,to=255,
                               command=self.AlphaChanged,orient='horizontal',length=75)
        self.alpha.grid(row=0,column=2,sticky='E')
        self.alpha.set(255)
        ToolTip(self.alpha, msg=2)
        
        self.VFlipState = False
        image = PIL.Image.open('Assets/flip.png')
        image1 = image.rotate(90)
        image1 = image1.resize((16,16))
        self.flipVgif = ImageTk.PhotoImage(image1)
        self.Vflip = ttk.Button(ButtonFrame,image=self.flipVgif,width=10,
                                command=self.ToggleVFlip,padding=(2,2,2,2))
        self.Vflip.grid(row=0,column=3,padx=5)
        ToolTip(self.Vflip, msg=3)
        
        self.HFlipState = False
        self.flipHgif = ImageTk.PhotoImage(image.resize((16,16)))
        self.Hflip = ttk.Button(ButtonFrame,image=self.flipHgif,width=10,
                                command=self.ToggleHFlip,padding=(2,2,2,2))
        self.Hflip.grid(row=0,column=4)
        ToolTip(self.Hflip, msg=4)
        
        image = PIL.Image.open('Assets/rotate.png')
        self.RotateImg = ImageTk.PhotoImage(image.resize((16,16)))
        self.Rotate = ttk.Button(ButtonFrame,image=self.RotateImg,width=10,
                                 command=self.RotateCamera,padding=(2,2,2,2))
        self.Rotate.grid(row=0,column=5)
        ToolTip(self.Rotate, msg=14)
        
        self.ShowOnScreen = MyBooleanVar(True)
        self.ShowOnMonitorButton = ttk.Checkbutton(ButtonFrame, \
                                                   text='Overlay',variable=self.ShowOnScreen, \
                                                   command=self.SetPreviewLocation)
        self.ShowOnMonitorButton.grid(row=0,column=6,padx=5,sticky='W')
        ToolTip(self.ShowOnMonitorButton, msg=5)
        
        l5 = Label(ButtonFrame,text="Size:")
        l5.grid(column=7,row=0,sticky='W')
        self.WindowSize = ttk.Scale(ButtonFrame,from_=100,to=800,
                                    command=self.WindowSizeChanged,orient='horizontal',length=75)
        self.WindowSize.grid(row=0,column=8,sticky='E')
        self.WindowSize.set(255)
        ToolTip(self.WindowSize, msg=6)
        
        
        #Packing everything
        #txt.pack(anchor='center', fill=tk.Y, expand=tk.Y)
        frame1.pack(padx=15, pady=15, fill=tk.BOTH, expand=tk.TRUE)
        #n.pack(padx=20, pady=20, fill=tk.BOTH, expand=tk.TRUE)
        #self.pw.pack(padx=10, pady=10, fill=tk.BOTH, expand=tk.TRUE)
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

