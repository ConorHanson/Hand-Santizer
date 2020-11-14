#modules have to be installed first
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime
import time
from gpiozero import Buzzer
import RPi.GPIO as GPIO
from example import weight


# initializations 
cred = credentials.Certificate('sanit.json')
firebase_admin.initialize_app(cred, {
'databaseURL' : 'https://sanitize-49e89.firebaseio.com/'
})
ref = db.reference('sanitizer')
sanitizer_id = "5"


#setting up all pins
GPIO.setmode(GPIO.BOARD)
GPIO.setup(35, GPIO.OUT)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(33, GPIO.OUT)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(32, GPIO.OUT)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(29, GPIO.OUT)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(31, GPIO.OUT)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(36, GPIO.OUT)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(12, GPIO.OUT)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(18, GPIO.OUT)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(37, GPIO.OUT)


#-----------------Hand sensor-----------------------#

# infinte loop that constantly checks levels for updates.
while True:

	GPIO.output(12, GPIO.LOW)
	GPIO.output(18, GPIO.LOW)
	#GETS THE RANGE IN CM
	GPIO.setmode(GPIO.BCM)
	#pins for hand sensors
	TRIG_PIN = 12
	ECHO_PIN = 22

	GPIO.setup(TRIG_PIN,GPIO.OUT)
	GPIO.setup(ECHO_PIN,GPIO.IN)
	GPIO.output(TRIG_PIN, True)
	time.sleep(0.00001)
	GPIO.output(TRIG_PIN, False)

	while GPIO.input(ECHO_PIN) == False:
	    start = time.time()
	while GPIO.input(ECHO_PIN) == True:
	    end = time.time()
	t = end-start
	#cm distance of hand from dispensor
	d_hand = t / 0.00006

	#-----------------proximity sensor-----------------------#

	GPIO.setmode(GPIO.BCM)
	#pins for proximity sensor
	TRIG_PIN = 13
	ECHO_PIN = 16
	GPIO.setup(TRIG_PIN,GPIO.OUT)
	GPIO.setup(ECHO_PIN,GPIO.IN)
	GPIO.output(TRIG_PIN, True)
	time.sleep(0.00001)
	GPIO.output(TRIG_PIN, False)

	while GPIO.input(ECHO_PIN) == False:
	    start = time.time()
	while GPIO.input(ECHO_PIN) == True:
	    end = time.time()
	t = end-start
	#cm distance of person from dispensor
	d_prox = t / 0.00006

#---------------------------------------------------#
	hand_sensor = d_hand
	proximity_sensor = d_prox


	#Turns on the dispenser
	#the three pins for the dispenser
	DIR = 29
	SLP = 31
	RST = 36
	GPIO.output(DIR, GPIO.HIGH)
	GPIO.output(SLP, GPIO.HIGH)
	GPIO.output(RST, GPIO.HIGH)
	buzzer = Buzzer(40)
	# buzzer on pin 40 will be user for the speaker (buzzer)

	

#calls the weight function w#ithin the example.py file.
#this file is part of the tutorial I followed, all files can be cloned and dowloaded here:
#https://tutorials-raspberrypi.com/digital-raspberry-pi-scale-weight-sensor-hx711/

#----if the weight is less than 200g turn red indicating the sanitizer needs a refiil---------
	if weight() < 200:
		GPIO.output(37, GPIO.LOW)
		GPIO.output(18, GPIO.HIGH)
#----otherwise, keep the green light swtiched on-----------------------
	else:
	    GPIO.output(18, GPIO.LOW)
	    GPIO.output(37, GPIO.HIGH)



	def proximity():
		#if someone is not in range
		if proximity_sensor > 200:
		    #the boolean return value tells the main function if / where to push it in the database
			return False
		else:
			GPIO.output(12, GPIO.HIGH) 
			#when someone is in range
			#activate attention grabbers for a few seconds
			GPIO.output(37, GPIO.LOW)
			GPIO.output(18, GPIO.HIGH)
			buzzer.on()
			time.sleep(0.5)
			GPIO.output(18, GPIO.LOW)
			GPIO.output(37, GPIO.HIGH)
			time.sleep(0.5)
			GPIO.output(37, GPIO.LOW)
			GPIO.output(18, GPIO.HIGH)
			time.sleep(0.5)
			GPIO.output(18, GPIO.LOW)
			GPIO.output(37, GPIO.HIGH)
			time.sleep(2)
			buzzer.off()
#the boolean return value tells the main function if / where to push it in the database
			return True

	#~~~~~~~~ Below dispenses the fluid from the sanitizer----------#

	def dispense():
		#when its not used (hand not in range)
		if d_hand > 20:
		    #the boolean return value tells the main function if / where to push it in the database
			return False
		else:
			#when its used
			#Pins all set the low indicate 1 full step.
			#M values can be adjusted to change the step length.
			#See here https://imgur.com/Smbscsg
			GPIO.output(35, GPIO.LOW)
			GPIO.output(33, GPIO.LOW)
			GPIO.output(32, GPIO.LOW)
			#the boolean return value tells the main function if / where to push it in the database
			return True

	# Below is an additional feature we've added to our API
	# THe ability the view all the data in an accessible manner using firebase.

	def create_db(num):
		i = 1
		while i <= num:
			#set amount of santizers to the integer in the while loop for. num = amount of sanitizers 
			#database init
			ref2 = ref.child(str(i))
			level_ref = ref2.child('Level')
			level_ref.set("100%")
			i = i + 1

#This update level function will update the database if the device is running low on santizer----

	def update_level(sanitizer_id, pressure):
		if pressure <= 200:
			ref2 = ref.child(sanitizer_id)
			level_ref = ref2.child('level')
			level_ref.set("Needs Refilling!")
		else:
			ref2 = ref.child(sanitizer_id)
			level_ref = ref2.child('Level')
			display_val = pressure // 10 
			level_ref.set(str(display_val) + "%")


	#This function will update the database if a person uses or doesnt use the santiizer.

	def main(sanitizer_id):
		#only update db with activity if someone is with 2metres of sensor
		while proximity_sensor <= 200:
			curr_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			#depending on certain cases, we will push the info to the databse 

			if proximity() == True and dispense() == True:
				ref2 = ref.child(sanitizer_id)
				level_ref = ref2.child('Activity').child('Use').push()
				level_ref.set(curr_time)
				update_level(sanitizer_id, weight())

			elif proximity() == True and dispense() == False:
				ref2 = ref.child(sanitizer_id)
				level_ref = ref2.child('Activity').child('No Use').push()
				level_ref.set(curr_time)
				update_level(sanitizer_id, weight())

			else:
				update_level(sanitizer_id, weight())


	create_db(8)
	main(sanitizer_id)
