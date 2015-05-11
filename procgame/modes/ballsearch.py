from ..game import Mode
from .. import dmd

class BallSearch(Mode):
	"""Ball Search mode."""
	def __init__(self, game, priority, countdown_time, coils=[], reset_switches=[], stop_switches=[], enable_switch_names=[], special_handler_modes=[]):
		self.stop_switches = stop_switches
		self.countdown_time = countdown_time
		self.coils = coils
		self.special_handler_modes = special_handler_modes
		self.enabled = 0;
		self.completion_handler = None
		Mode.__init__(self, game, 8)
		for switch in reset_switches:
			self.add_switch_handler(name=str(switch), event_type=str(reset_switches[switch]), delay=None, handler=self.reset)
		# The disable_switch_names identify the switches that, when closed, 
		# keep the ball search from occuring.  This is typically done, 
		# for instance, when a ball is in the shooter lane or held on a flipper.
		for switch in stop_switches:
			self.add_switch_handler(name=str(switch), event_type=str(stop_switches[switch]), delay=None, handler=self.stop)

	#def sw_trough1_open_for_200ms(self, sw):
	#	if self.game.is_trough_full():
	#		for special_handler_mode in self.special_handler_modes:
	#			special_handler_mode.mode_stopped()
	#		self.stop(0)

	def enable(self):
		self.game.log("BallSearch: Enabled (waiting)")
		self.enabled = 1;
		self.reset('None')

	def disable(self):
		self.game.log("BallSearch: Disabled")
		self.stop(None)
		self.enabled = 0;

	def reset(self,sw):
		if self.enabled:
			# Stop delayed coil activations in case a ball search has
			# already started.
			for coil in self.coils:
				self.cancel_delayed('ball_search_coil1')
			self.cancel_delayed('start_special_handler_modes')
			self.cancel_delayed
			schedule_search = 1
			for switch in self.stop_switches:

				# Don't restart the search countdown if a ball
				# is resting on a stop_switch.  First,
				# build the appropriate function call into
				# the switch, and then call it using getattr()
				stop_sw = self.game.switches[str(switch)]
				state_str = str(self.stop_switches[switch])
				m = getattr(stop_sw, 'is_%s' % (state_str))
				if m():
					schedule_search = 0

			if schedule_search:
				self.cancel_delayed(name='ball_search_countdown');
				self.delay(name='ball_search_countdown', event_type=None, delay=self.countdown_time, handler=self.perform_search, param=0)
				self.game.logger.info("BallSearch: RESET via '%s'; will search in %ds." % (sw, self.countdown_time))
			else:
				self.game.logger.info("BallSearch: RESET via '%s'; next search is unscheduled due to stopswitch %s." % (sw.name, stop_sw.name))

	def stop(self,sw):
		self.game.logger.info("BallSearch: countdown STOPPED via '%s'" % ("" if sw is None else sw.name))
		self.cancel_delayed(name='ball_search_countdown');

	def perform_search(self, completion_wait_time, completion_handler = None, silent=False):
		self.game.log("BallSearch: perform_search(completion_wait_time=%d)" % completion_wait_time)
		if (completion_wait_time != 0):
			self.game.log("BallSearch: BALLS MISSING!!")
			if(silent is False):
				self.game.set_status("Balls Missing") # Replace with permanent message
		self.completion_handler = completion_handler
		delay = .150
		for coil in self.coils:
			self.delay(name='ball_search_coil1', event_type=None, delay=delay, handler=self.pop_coil, param=str(coil))
			delay = delay + .150
		self.delay(name='start_special_handler_modes', event_type=None, delay=delay, handler=self.start_special_handler_modes)

		if (completion_wait_time != 0):
			pass
		else: # completion wait time is zero; schedule the next ball search now
			self.cancel_delayed(name='ball_search_countdown');
			self.delay(name='ball_search_countdown', event_type=None, delay=self.countdown_time, handler=self.perform_search, param=0)
	
	def pop_coil(self,coil):
		self.game.log("BallSearch: FIRING '%s'" % coil)
		self.game.coils[coil].pulse()

	def start_special_handler_modes(self):
		d = 0
		for special_handler_mode in self.special_handler_modes:
			self.game.modes.add(special_handler_mode)
			self.delay(name='remove_special_handler_mode', event_type=None, delay=d, handler=self.remove_special_handler_mode, param=special_handler_mode)
			d+=3
		if(self.completion_handler is not None):
			self.delay(name='completion_handler', event_type=None, delay=d, handler=self.completion_handler)

	def remove_special_handler_mode(self,special_handler_mode):
		self.game.modes.remove(special_handler_mode)

