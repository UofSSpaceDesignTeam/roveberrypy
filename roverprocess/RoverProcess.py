# Copyright 2016 University of Saskatchewan Space Design Team Licensed under the
# Educational Community License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may
# obtain a copy of the License at
#
# https://opensource.org/licenses/ecl2.php
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied. See the License for the specific language governing
# permissions and limitations under the License.

from multiprocessing import Process, BoundedSemaphore, Queue, Manager
import threading
import sys
import time

class RoverProcess(Process):
	class SubscriberThread(threading.Thread):
		def __init__(self, subscriber, parent):
			threading.Thread.__init__(self)
			self.subscriber = subscriber
			self._parent = parent
			self.quit = False
			self.daemon = True

		def run(self):
			while not self.quit:
				data = self.subscriber.get()
				self._parent.addSubscriber(data[0],data[1])
						
	class ReceiverThread(threading.Thread):
		def __init__(self, downlink, parent):
			threading.Thread.__init__(self)
			self.downlink = downlink
			self._parent = parent
			self.quit = False
			self.daemon = True

		def run(self):
			while not self.quit:				
				data = self.downlink.get()
				assert isinstance(data, dict)
				for key in data.keys():
					if hasattr(self._parent, "on_" + key):
						#call trigger method
						getattr(self._parent, "on_" + key)(data[key])
					else:
						self._parent.messageTrigger(data)

	def __init__(self, **kwargs):
		Process.__init__(self)
		if kwargs["ProcessName"] is "StateManager":
			self.stateSem = BoundedSemaphore()
			self.subscriberMap = dict() # maps message names to
		self.uplink = kwargs["uplink"]
		self.downlink = kwargs["downlink"]
		self.name = kwargs["ProcessName"]
		self.subQueue = kwargs["subQueue"]	
		self._args = kwargs
		self.load = True
		self.quit = False
		self.receiver = RoverProcess.ReceiverThread(self.downlink, self)
		if kwargs["ProcessName"] is "StateManager":
			self.subscriber = RoverProcess.SubscriberThread(self.subQueue, self)
		else:
			self.subscriber = None
	def getSubscribed(self):
		return ["quit"]

	def run(self):
		
		self.receiver.start()
		try:
			self.setup(self._args)
			
			if self.subscriber is not None:
				self.subscriber.start()
			while not self.quit:
				try:
					self.loop()
				except KeyboardInterrupt:
					self.quit = True
			self.cleanup()
		except KeyboardInterrupt:
			self.quit = True
			self.cleanup()
		except:
			self.cleanup()
			raise

	def setup(self, args):
		for msg_key in self.getSubscribed():
			self.subQueue.put([msg_key, self.name])

	def loop(self):
		try:
			time.sleep(1)
		except KeyboardInterrupt:
			pass

	def messageTrigger(self, message):
		pass

	def on_quit(self, message):
		self.cleanup()
		sys.exit(0)

	def publish(self, key, value):
		self.uplink.put({key:value})

	def cleanup(self):
		try:
			if self.receiver != threading.current_thread():
				print(self.__class__.__name__ + " shutting down")
				self.receiver.quit = True
				self.receiver.join(0.01)  # receiver is blocked by call to queue.get()
			else: # cleanup was called from a message: cannot join current_thread
				self.quit = True
		except KeyboardInterrupt:
			pass

