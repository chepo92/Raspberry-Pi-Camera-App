PiCameraLoaded = True	
try:	
	import picamera
	from picamera import *
	import picamera.array
except ImportError as imp_err:
	raise ImportError("You do not seem to have PiCamera installed:\n {0}".format(imp_err))
	PiCameraLoaded = False
	
def OutputPythonScript ( camera ):
	# Open file
	# Loop through options and change
	

