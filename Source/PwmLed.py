import RPi.GPIO as GPIO


class PwmLed ():
	def __init__ (self, pin, invert=True):
		self.pin = pin
		self.invert = invert
		self.bright = 100
		
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(self.pin, GPIO.OUT)
		self.pwm = GPIO.PWM(self.pin, 2000)
		duty = self.bright
		if (invert):
			duty = 100-duty
		self.pwm.start(duty)
	
	def __del__ (self):
		self.pwm.stop()
		# # turn off the LED
		# if (self.invert):
			# GPIO.output(18,GPIO.HIGH)
		# else:
			# GPIO.output(18,GPIO.LOW)
		GPIO.cleanup()
		
	def setBrightness (self, bright):
		if (bright != self.bright):
			self.bright = bright
			duty = bright
			if (self.invert):
				duty = 100-duty
			self.pwm.ChangeDutyCycle(duty)
