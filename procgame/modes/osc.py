# This is a modified version of OSC Mode that supports sending lamp updates to the graphical
# OSC client. This has been modified from an earlier version written by Brian Madden.  
# Unfortunately, this version has not been generated from Brian's latest version, and as 
# such some functionality from his latest is likely to be missing in this version.

# Coupled with the latest Graphical OSC 'switchMatrixClient' you can layout lamps on an 
# image of the playfield and  watch lamp updates during FakePinPROC (or live) machine testing.

# This version will respond to an OSC request of /lamps/get and it will return OSC messagess
# consisting for each of the lamps and their respective state (0=off, 1=on).  

# This is NOT an efficent way to do this.  I will, eventually, provide an OSC message to
# specify the lamp ordering so the reply message can be a single message with the state of
# all lamps (and drastically reduce overhead), but this is enough to get people started... I hope.

# This code is released under the MIT License.

# Portions unique to this version are Copyright (c) 2015 Michael Ocean

############

# An OSC-based interface for controlling pyprocgame with OSC devices
# for pyprocgame, a Python-based pinball software development framework
# for use with P-ROC written by Adam Preble and Gerry Stellenberg
# More information is avaible at http://pyprocgame.pindev.org/
# and http://pinballcontrollers.com/

# More info on OSC at http://opensoundcontrol.org/
# This OSC interface was written by Brian Madden
# Version ?.?.? - ??? 

# This code is released under the MIT License.

#The MIT License (MIT)

#Copyright (c) 2013-2014 Brian Madden

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.


# This code requires pyOSC, https://trac.v2.nl/wiki/pyOSC
# It was written for pyOSC 0.3.5b build 5394,
# though I would expect later versions should work

# It also requires that the "desktop" mode is enabled in pyprocgame,
# and it requires some changes to procgame/game/game.py
# See http://www.pinballcontrollers.com/forum for more information


import OSC
import socket
import threading
import pinproc
import procgame
from procgame.game import Mode 

OSC_INST = None

class OSC_Mode(Mode):
    """This is the awesome OSC interface. A few parameters:
    game - game object
    priority - game mode priority. It doesn't really matter for this mode.
    serverIP - the IP address the OSC server will listen on. If you don't pass it anything it will use the default IP address of your computer which should be fine
    serverPort - the UDP port the server will listen on. Default 9000
    clientIP - the IP address of the client you'd like to connect to. Leave it blank and it will automatically connect to the first client that contacts it
    clientPort - the client UDP port. Default is 8000
    closed_switches - a list of switch names that you'd like to have set "closed" by default. Good for troughs and stuff. Maybe use some logic here so they're only set to closed with fakepinproc?
    """
    def __init__(self, game, priority, serverIP=None, serverPort=9000, clientIP = None, clientPort = 8000, closed_switches=[]):
        super(OSC_Mode, self).__init__(game, priority)
        self.serverPort = serverPort
        self.clientPort = clientPort
        self.closed_switches = closed_switches
        if not serverIP:
            self.serverIP = socket.gethostbyname(socket.gethostname())
        else:
            self.serverIP = serverIP
        self.clientIP = clientIP
        self.client_needs_sync = False
        self.do_we_have_a_client = False
        global OSC_INST
        OSC_INST = self

    def mode_started(self):
        receive_address = (self.serverIP, self.serverPort)  # create a tuple from the IP & UDP port
        self.server = OSC.OSCServer(receive_address)
        self.server.addDefaultHandlers()
        self.server.addMsgHandler("/lamps/get", self.PROC_OSC_lamp_handler)
        self.server.addMsgHandler("default", self.PROC_OSC_message_handler)

        # start the OSC server
        self.game.logger.info("OSC Server listening on %s:%s", self.serverIP, self.serverPort)
        self.last_lamp_states = []
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.start()
        self.set_initial_switches()
        pass

    def dumpLamps(self):
        """ Return a list of changed lamps. """
        lamps = self.getLampStates()
        changedLamps = []
        
        if len(self.last_lamp_states) > 0:
            for i in range(0,len(lamps)):
                if lamps[i] != self.last_lamp_states[i]:
                    changedLamps += [(i,lamps[i])]
                        
        self.last_lamp_states = lamps
        #print("LAMPS: %s" % changedLamps)
        self.delay(name="printer", delay=.03, handler=self.dumpLamps)
        #return changedLamps
                
    def getLampStates(self):
        """ Gets the current state of the lamps. 
            Shamelessly ripped from the VPCOM project.
        """

        vplamps = [False]*90

        for i in range(0,64):
            vpNum = (((i/8)+1)*10) + (i%8) + 1
            vplamps[vpNum] = self.game.proc.drivers[i+80].curr_state
        return vplamps


    def mode_stopped(self):
        self.OSC_shutdown()
        
    def OSC_shutdown(self):
        """Shuts down the OSC Server thread. If you don't do this python will hang when you exit the game."""
        self.server.close()
        self.game.logger.info("Waiting for the OSC Server thread to finish")
        self.server_thread.join()
        self.game.logger.info("OSC Server thread is done.")


    def PROC_OSC_lamp_handler(self, addr, tags, data, client_address):
        #print("GOING THROUGH LAMP HANDLER %s " % addr)
        self.sync_client_lamps()

    def PROC_OSC_message_handler(self, addr, tags, data, client_address):
        """ receives OSC messages and acts on them by setting switches."""
        #print("GOING THROUGH DEFAULT HANDLER %s " % addr)
        # print("recvd OSC message " + str(addr) +" tags:"+ str(tags) +" data:"+ str(data))
        # need to add supprt for "sync" instruction which we'll call when switching tabs in touchOSC
        
        #strip out the switch name
        switchname = addr.split("/")[-1]  # This is the OSC address, not the IP address. Strip out the characters after the final "/"

        if switchname in self.game.switches:
            switch_number = self.game.switches[switchname].number
            #print("switch_number is local -> %d" % switch_number)
        else:
            switch_number = pinproc.decode(self.game.machine_type, switchname)
            #print("switch_number is lookedup -> %d" % switch_number)

        # I'm kind of cheating by using desktop.key_events here, but I guess this is ok?
        if data[0] == 1.0:  # close the switch
            self.game.desktop.key_events.append({'type': pinproc.EventTypeSwitchClosedDebounced, 'value': switch_number})
        elif data[0] == 0.0:  # open the switch
            self.game.desktop.key_events.append({'type': pinproc.EventTypeSwitchOpenDebounced, 'value': switch_number})

        # since we just got a message from a client, let's set up a connection to it
        if not self.do_we_have_a_client:
            if not self.clientIP:  # if a client IP wasn't specified, use the one that just communicated with us now
                self.clientIP = client_address[0]

            self.clientTuple = (self.clientIP, self.clientPort)
            # print(self.clientTuple)
            # print("OSC attempting connection back to client")
            self.OSC_client = OSC.OSCClient()
            self.OSC_client.connect(self.clientTuple)
            self.do_we_have_a_client = True
        else:
            # print("We do have a client...")
            pass

        if(self.do_we_have_a_client):
            # print("OSC sending back back to client")
            OSC_message = OSC.OSCMessage()
            OSC_message.setAddress(addr)
            OSC_message.append("OK")
            self.OSC_client.send(OSC_message)

    def sync_client(self, OSC_branch=1):
        """ Read through all the current switch states and updates the client to set the default states on the client.
        Since we don't know whether the client has momentary or toggle switches, we just have to update all of them.
        """

        for switch in self.game.switches:
            status = 0.0  # set the status to 'off'
            if switch.state:
                status = 1.0  # if the switch.state is 'True', the switch is closed
                
            self.update_client_switch(switch.name, status, OSC_branch)

        self.client_needs_sync = False  # since the sync is done we reset the flag

    def sync_client_lamps(self):
        """ Guess..
        """
        #print("===================sync_client_lamps===================")
        for lamps in self.game.lamps:
            status = 0.0  # set the status to 'off'
            if hasattr(self.game.proc.drivers[lamps.number], 'curr_state'):
                if self.game.proc.drivers[lamps.number].curr_state:
                    status = 1.0  # if the switch.state is 'True', the switch is closed
            elif self.game.proc.driver_get_state(lamps.number):
                #self.game.proc.drivers[lamps.number].state().state:
                status = 1.0
            #print("/lamps/%s/%d" % (lamps.name,status))
            self.update_client_switch(lamps.name,status,"lamps")
        
    def update_client_switch(self, switch_name, status, OSC_branch=1):
        """update the client switch states.
        
        Parameters
        swtich_name - the procgame switch name
        status - closed = 1, open = 0
        OSC_branch - what OSC branch do you want? For TouchOSC, this defaults to the "tab"
        The screen is the /1/ or /2/ or whatever part of the OSC address
        """
        if self.do_we_have_a_client:  # only do this if we have a client
            # Let's build a message. For example OSC address "/1/switchname" with data "1"
            self.OSC_message = OSC.OSCMessage()
            self.OSC_message.setAddress("/" + str(OSC_branch) + "/" + switch_name)
            self.OSC_message.append(status)
            self.OSC_client.send(self.OSC_message)
        else:  # we don't have a client?
            pass
            self.do_we_have_a_client = False
        #self.delay(name="printer", delay=.03, handler=self.sync_client)
        

        
    def set_initial_switches(self):
        """sets up the initial switches that should be closed, then marks the client to sync
        Should I add some logic here to only do this with fakepinproc?
        """
        if ('pinproc_class' in procgame.config.values and 
                procgame.config.values['pinproc_class'] == 'procgame.fakepinproc.FakePinPROC'):
                for switchname in self.closed_switches:  # run through the list of closed_switches passed to the mode as args
                    if switchname in self.game.switches:  # convert the names to switch numbers
                        switch_number = self.game.switches[switchname].number
                    else:
                        switch_number = pinproc.decode(self.game.machine_type, switchname)
                    self.game.desktop.key_events.append({'type': pinproc.EventTypeSwitchClosedDebounced, 'value': switch_number})  # add these switch close events to the queue
                    
                self.client_needs_sync = True  # Now that this is done we set the flag to sync the client
                # we use the flag because if we just did it now it's too fast. The game loop hasn't read in the new closures yet

    def mode_tick(self):
        """performs a client sync if we need it"""
        if self.do_we_have_a_client:  # only proceed if we've establish a connection with a client
            if self.client_needs_sync:  # if the client is out of sync, then sync it
                self.sync_client()
