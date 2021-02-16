from time import sleep
from 	Dialog import *
from 	Mapping import *
from	NotePage import *

class Timelapse ( BasicNotepage ):
	def BuildPage ( self ):
		#------------------------Timings------------------------
		# f = ttk.LabelFrame(self,text='Timings',padding=(5,5,5,5))
		# f.grid(row=0,column=0,columnspan=4,sticky='NEWS',pady=5)
		# f.columnconfigure(2,weight=1)
		# f.columnconfigure(4,weight=1)

		# Label(f,text='The total number of images captured will depend on the').grid(row=0,column=0,sticky='W')
		# Label(f,text='interval between frames and total recording length.').grid(row=1,column=0,sticky='W')

		# self.DelayLabel = Label(f,text='Delay between Frames: ')
		# self.DelayLabel.grid(row=2,column=0,sticky='W')

		# self.TotalTimeLabel = Label(f,text='Total Recording Time: ', width=15)
		# self.TotalTimeLabel.grid(row=3,column=0,sticky='W')
		
		#------------------------Pathways------------------------
		# f = ttk.LabelFrame(self,text='Pathways',padding=(5,5,5,5))
		# f.grid(row=1,column=0,columnspan=4,sticky='NEWS',pady=5)
		# f.columnconfigure(2,weight=1)
		# f.columnconfigure(4,weight=1)

		# Label(f,text='Please backup any frames required for future use from the designated output').grid(row=0,column=0,sticky='E')
		# Label(f,text='folder because the \'Frammes dir\' will be wiped when a new timelapse is initiated.').grid(row=1,column=0,sticky='E')

		# self.FramesPathway = Label(f,text='Frames dir:', width=15)
		# self.FramesPathway.grid(row=2,column=0,sticky='W')

		# self.VideoPathway = Label(f,text='Frames dir:', width=15)
		# self.VideoPathway.grid(row=2,column=0,sticky='W')

		# self.LowLightCaptureButton.grid(row=2,column=0,sticky='W')


		# #------------------------Video output------------------------
		# f = ttk.LabelFrame(self,text='Video Output',padding=(5,5,5,5))
		# f.grid(row=1,column=0,columnspan=4,sticky='NEWS',pady=5)
		# f.columnconfigure(2,weight=1)
		# f.columnconfigure(4,weight=1)

		# Label(f,text='By default the video will be saved as an .mp4 file. Please ensure there is not').grid(row=0,column=0,sticky='E')
		# Label(f,text='another .mp4 file with the same desired name in the chosen output folder.').grid(row=1,column=0,sticky='E')

		# self.FramesPathway = Label(f,text='Frames dir:', width=15,)
		# self.FramesPathway.grid(row=2,column=0,sticky='W')

		# self.VideoPathway = Label(f,text='Video Output dir:', width=15)
		# self.VideoPathway.grid(row=3,column=0,sticky='W')

		# self.VideoPathway = Label(f,text='Video fps:', width=15)
		# self.VideoPathway.grid(row=4,column=0,sticky='W')


		# #----------------------Start Timelapse-----------------------
		# f = ttk.LabelFrame(self,text='Initiate Timelapse!',padding=(5,5,5,5))
		# f.grid(row=1,column=0,columnspan=4,sticky='NEWS',pady=5)
		# f.columnconfigure(2,weight=1)
		# f.columnconfigure(4,weight=1)

		# Label(f,text='Please check your settings and then press to begin!').grid(row=0,column=0,sticky='W')

		# self.StartTimelapseButton = Button(f,text='Start Timelapse!', width=15, 
		# command=self.StartTimelapse)
		# self.StartTimelapseButton.grid(row=2,column=0,sticky='W')

		
	
	#------------------------Functions------------------------

	def CaptureLowLight ( self ):
		self.camera.capture('foo.jpg')
		pass
	def StartDelayCapture ( self ):
		pass
	def Reset ( self ):
		pass

	def StartTimelapse ( self ):
		pass