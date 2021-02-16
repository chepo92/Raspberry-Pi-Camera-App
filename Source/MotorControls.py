#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
#  Timelapse.py
#
#  Copyright 2018  Bill Williams
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
'''
from time import sleep
from 	Dialog import *
from 	Mapping import *
from	NotePage import *

class MotorControls ( BasicNotepage ):
	def BuildPage ( self ):
		f = ttk.LabelFrame(self,text='Time lapse settings',padding=(5,5,5,5))
		f.grid(row=0,column=0,columnspan=4,sticky='NEWS',pady=5)
		f.columnconfigure(2,weight=1)
		f.columnconfigure(4,weight=1)

		Label(f,text='Default').grid(row=0,column=0,sticky='E')
		self.LowLightCaptureButton = Button(f,text='Low Light',width=15, \
			command=self.CaptureLowLight)
		self.LowLightCaptureButton.grid(row=1,column=0,sticky='W')
		self.StartDelayCaptureButton = Button(f,text='Delay Capture',width=15, \
			command=self.StartDelayCapture)
		self.StartDelayCaptureButton.grid(row=2,column=0,sticky='W')

	def CaptureLowLight ( self ):
		self.camera.capture('foo.jpg')
		pass
	def StartDelayCapture ( self ):
		pass
	#### TODO: Implement Reset NEEDS LOTS OF WORK!!
	def Reset ( self ):
		pass

