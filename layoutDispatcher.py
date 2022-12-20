import ast
import threading
import traceback
import sys
import uuid

if (sys.platform.startswith('java')):
   import layoutListeners
   import jmri
   import layoutJMRIUtils as jmriUtils
   from jmri_bindings import *
   from java.lang import Exception
   
import layoutConfig
import layoutReload
import layoutUtils as utils

class layoutDispatcher(jmri.jmrit.automat.AbstractAutomaton):
      def __init__(self,controller,train_name):
          
          if layoutConfig.reload_modules: layoutReload.reloadModules()
          
          self.controller                  = controller
          self.panel_manager_queue         = self.controller.panel_manager_queue

          self.booking_wait_time           = 1                    # Time in seconds between attempts to book a subroute with the booking manager  

          self.train_name                  = train_name
          self.route_name                  = self.controller.active_requests[train_name]['route']
          
          self.sensor_manager              = sensors
          self.block_manager               = blocks
          self.turnout_manager             = turnouts
          self.signal_manager              = signals
          self.mast_manager                = masts
          
          
          self.running_threads             = {}
          
          self.route_instance              = self.controller.active_requests[train_name]['route_instance'] 
          self.train_instance              = self.controller.active_requests[train_name]['train_instance']
          
          self.printMsg                    = utils.printMsg(caller="layoutDispatcher",controller=self.controller)
          
          self.command_sensors             = layoutConfig.command_sensors
          
          self.active_request              = self.controller.active_requests[self.train_name]
          
          self.loops                       = self.active_request['loops']
          self.mode                        = self.active_request['mode']
          self.route_direction             = self.active_request['route_direction']
          self.throttle_direction          = self.active_request['throttle_direction']
          self.retrys                      = self.active_request['retrys']
          self.look_ahead                  = self.active_request['look_ahead']
          
          
          self.dispatch_hold_sensor        = None
          self.throttle                    = None
          
          self.jmriUTILS                   = jmriUtils.jmriutils(controller=self.controller,sensor_manager=self.sensor_manager,block_manager=self.block_manager,\
                                                                 turnout_manager=self.turnout_manager,signal_manager=self.signal_manager)
          
      def init(self):
          return
      def handle(self):
          try:
             self.dispatchTrain()
             self.releaseSubroute('all',owner=self.train_name,force=True)
             self.stopAllThreads()
             self.runStopSequence()
          except:
              print(traceback.format_exc())
          #finally:
             # self.controller.active_requests[self.train_name]['dispatcher_running']=False
      '''
      #=========================================================================================================================================
      # Dispatch A train on a route. The request is as defined in the layoutController.py file active_requests dictionary
      #
      # build all the subroutes for a train on a given route. Note. The train profile and route profile must have been validated before the
      # train is dispatched.
      #
      #==========================================================================================================================================
      '''
      def dispatchTrain(self):
          function_name='f(dispatchTrain)'
 
          try:
             self.throttle = self.controller.getMyThrottle(int(self.train_instance.throttleNumber),self.train_instance.throttleNumLong)
             
             if not self.throttle:
                self.controller.setActiveRequest(self.train_name,caller=function_name,status='terminating',\
                                                 status_code=6002,status_reason='failed to get throttle {}'.format(self.train_instance.throttleNumber))
                self.printMsg._print(function_name,"ERROR",self.train_name,"Failed to get throttle {}".format(self.train_instance.throttleNumber),state='NO_THROTTLE')
                return
             
             if not self.buildRoute():
                self.printMsg._print(function_name,"ERROR",self.train_name,"Failed to build route {}".format(self.route_name),state='F_ROUTE')
                self.controller.setActiveRequest(self.train_name,caller=function_name,status='terminating',\
                                                 status_code=6007,status_reason='failed to build route {}'.format(self.route_name))
                return
             #
             # For each loop to be executed get the subroute, book it and set the engine running
             #
             
             self.controller.setActiveRequest(self.train_name,caller=function_name,\
                                              mode=self.mode,max_speed=self.max_speed,\
                                              route_direction=self.route_direction,active_loop=0,\
                                              throttle_direction=self.throttle_direction,\
                                              status='running',status_code=6001,status_reason=''\
                                              )
             for loop in range(1,int(self.loops)+1):
                 
                 self.controller.setActiveRequest(self.train_name,caller=function_name,active_loop=loop)
                 if self.mode == 'BACKANDFORTH':
                    if loop>1:
                       if self.route_direction=='FORWARD':  self.route_direction='REVERSE'
                       else: self.route_direction='FORWARD'
                       
                       if self.throttle_direction=='FORWARD':  self.throttle_direction='REVERSE'
                       else: self.throttle_direction='FORWARD'
                 
                 if self.route_direction=='FORWARD': 
                     subroutes=self.fwd_subroutes
                     speed=self.fwd_start_speed
                 else: 
                     subroutes=self.rev_subroutes
                     speed=self.rev_start_speed
                     
                 self.setBlockTrainName(subroutes)
                 
                 self.controller.setActiveRequest(self.train_name,caller=function_name,subroutes=subroutes,num_subroutes=len(subroutes),speed=speed,
                                                  route_direction=self.route_direction,throttle_direction=self.throttle_direction)
                                                  
                 number_of_subroutes = len(subroutes) 
                 
                 for subroute_count,subroute in enumerate(subroutes):
                     self.controller.setActiveRequest(self.train_name,caller=function_name,active_subroute=subroute,\
                                                                      active_subroute_num=subroute_count,status='booking',status_reason='',status_code=6001)
                     booked=False 

                     if self.bookSubroute(subroute,subroute_count=subroute_count,owner=self.train_name,route_direction=self.route_direction):
                         booked=True
                         
                         self.controller.setActiveRequest(self.train_name,caller=function_name,status='booked',status_reason='',status_code=6001)
                         
                         if subroute_count==number_of_subroutes-1:
                            self.setRouteCompleteSensor(subroute)
                         else:
                             self.setLastBlockSensor(subroute)
                         
                         self.jmriUTILS.addSensorsAndListeners(self.train_name)
                         
                         if loop==1 and subroute_count==0:
                             self.setFlags()
                             #self.jmriUTILS.addSensorsAndListeners(self.train_name)
                             self.runStartupSequence() 
                             
                         self.setTrainTurnouts(subroute)
                         self.setTrainKeySensors(subroute)
                         self.setTrainSpeedSensors(subroute)
                         self.setTrainWaitSensors(subroute)
                         self.setTrainRunning(subroute=subroute,terminate=False)
                         self.waitOnSensors(subroute)
                         
                         if self.isTerminateSet(): return
                         
                         self.releaseSubroute(subroute,owner=self.train_name,subroute_count=subroute_count,force=False)
                    
                     if not booked:
                        break
                 
                 if not booked :
                     
                    self.printMsg._print(function_name,"ERROR",self.train_name,'booking sub route {} failed'.format(subroute),state='f_booking')
                    self.controller.setActiveRequest(self.train_name,caller=function_name,status='terminating',status_code=6003,status_reason='failed to book sub route {} '.format(subroute))
                    self.controller.setSensor(sensor_name='terminate',train_name=self.train_name,state=ACTIVE)
                    return False 
          except Exception as err:
             self.printMsg._print(function_name,'ERROR',self.train_name,traceback.format_exc(),state='ERROR')
          return
      '''
      #=========================================================================================================================================
      # Book a subroute
      #
      #    {'cmd': 'book_sensors', 'sensors': 'MS:BS:BS01_32,MS:BS:BS01_33,MS:BS:BS01_34', 'owner': 'shunt8691', 'force': 'False'}
      #
      #    assumptions : 
      #                  1.  The train being dispatched is physically located in the first block
      #
      #==========================================================================================================================================
      '''
      def bookSubroute(self,subroute,subroute_count=None,owner=None,route_direction=None):
          function_name='f(bookSubroute)'
          
          self.controller.setActiveRequest(self.train_name,caller=function_name,status='booking',status_reason='sub route {} '.format(subroute))
                                                      
          self.printMsg._print(function_name,"DISPATCHER",self.train_name,'booking sub route {}'.format(subroute),state='booking')
          booked = False
          held   = True
          #
          # Get a tcp client instance
          #
          tcpBMClient = utils.tcpClient(caller='layoutDispatcher',manager_type='bookingmanager')
          #
          # Retry to book the subroute a given number of times
          #
          if self.route_direction=='FORWARD': masts=self.fwd_not_booked_signals
          else: masts=self.rev_not_booked_signals

          for retry in range(self.retrys): 
                #
                # If this is the first subroute to be booked then even if the first block is active book it
                # Assume this is the engine we want to dispatch
                #
                if subroute_count==0: 
                    force='True'
                else: force = 'False'

                owner=owner
                cmd="{{'cmd': 'book_sensors', 'sensors': {}, 'owner': '{}', 'force': '{}'}}".format(subroute,owner,force)
                try:
                   resp=tcpBMClient.sendData(data=cmd)
                   
                   if self.isTerminateSet(): break
                   
                   elif resp!=None and resp!='None':  
                      resp=ast.literal_eval(resp)
                      if 'cmd_successful' in resp:
                         # 
                         # if we failed to book the subroute then set the approach sensors
                         # 
                         if not resp['cmd_successful'] :
                            if retry<1:
                               self.setDispatchHold(subroute,retry)
                               self.printMsg._print(function_name,'WARNING',self.train_name,"failed to book subroute {} will retry a possible {} times".format(subroute,self.retrys))
                               self.setSignals('Stop',subroute)
                            booked=False
                         else: 
                            self.releaseDispatchHold(subroute) 
                            booked=True
                   
                   self.controller.setActiveRequest(self.train_name,caller=function_name,retry_count=retry+1)
                   
                   if booked : break
                   
                   elif retry<self.retrys-1:
                      for _ in range(self.booking_wait_time*1000):
                          if not self.isTerminateSet(): 
                             self.waitMsec(self.booking_wait_time)
                          else:
                             booked=False
                             break
                      if self.isTerminateSet(): break       
                except:
                    print(traceback.format_exc())
                    
          if booked:
             print("Need to set {} {} to Clear".format(subroute,route_direction))
             self.setSignals('Clear',subroute)
             return True
          else:
             return False
      '''
      #=========================================================================================================================================
      # set a subroutes signal masts either clear or stop (Stop indicates next subroute could not getbooked, clear indicates next subroute booked)
      #
      #==========================================================================================================================================
      '''
      def setSignals(self,signal_state,subroute):
          if self.route_direction=="FORWARD": signal_masts_to_set=self.route_instance.fwdSignals
          else: signal_masts_to_set=self.route_instance.revSignals
          for block_sensor_name,signal_mast_names in signal_masts_to_set.items():
          
              green_signal_mast_names,red_signal_mast_names=signal_mast_names
              
              if signal_state.upper() == 'STOP' : alt_signal_state='Clear'
              
              else: alt_signal_state='Stop'
             
              if block_sensor_name in subroute:

                 for signal_mast_name in red_signal_mast_names:
                     self.mast_manager.getSignalMast(signal_mast_name).setAspect('Stop')
                     self.waitMsec(25)
                 for signal_mast_name in green_signal_mast_names:
                    self.mast_manager.getSignalMast(signal_mast_name).setAspect('Clear')
                    self.waitMsec(25)
          return
      '''
      #=========================================================================================================================================
      # Release a subroute
      #
      #    {'cmd': 'release_sensors', 'sensors': 'MS:BS:BS01_32,MS:BS:BS01_33,MS:BS:BS01_34', 'owner': 'shunt8691', 'force': 'False'}
      #
      #==========================================================================================================================================
      '''
      def _releaseSubroute(self,subroute,uuid=None,event=None,subroute_count=None,owner=None,force=False):
         try: 
            function_name='_releaseSubroute'
            if isinstance(subroute,list):
               cmd="{{'cmd': 'release_sensors', 'sensors': {}, 'owner': '{}', 'force': '{}'}}".format(subroute,owner,force)
            else:
               cmd="{{'cmd': 'release_sensors', 'sensors': '{}', 'owner': '{}', 'force': '{}'}}".format(subroute,owner,force)
            resp={}
            resp['cmd_successful']=False
            count=0
            tcpBMClient = utils.tcpClient(caller='layoutDispatcher',manager_type='bookingmanager')
            while not resp['cmd_successful']:
                  r=tcpBMClient.sendData(data=cmd,quiet=True)
                  if 'cmd_successful' in r: 
                      resp=ast.literal_eval(r)
                  if self.isTerminateSet(): break
                  if event.is_set(): break
                  self.waitMsec(1000)
         except :
             print(traceback.format_exc())
      
      def releaseSubroute(self,subroute,subroute_count=None,owner=None,force=False):
          function_name='f(releaseSubroute)'
          event=threading.Event()
          uid=str(uuid.uuid4())
          release_subroute_thread = threading.Thread(target=self._releaseSubroute,name=function_name,args=(subroute,),
                                                     kwargs={'uuid':uid,'event':event,'subroute_count':subroute_count,'owner':owner,'force':force})
          self.running_threads[uid]={'event':event,'thread':release_subroute_thread}
          release_subroute_thread.start()
          return
      '''
      #=========================================================================================================================================
      # If the train has been terminated then we must release any  block senosrs it has booked. 
      #
      #==========================================================================================================================================
      '''
      def stopAllThreads(self):
          for thread in self.running_threads:
              self.running_threads[thread]['event'].set()
          for thread in self.running_threads:
              self.running_threads[thread]['thread'].join()
          return
      '''
      #=========================================================================================================================================
      # Run the startup sequence
      #==========================================================================================================================================
      '''
      def runStartupSequence(self):
          function_name='f(runStartupSequence)'
          if self.sensor_manager.getSensor("MS:IS:startup:{}".format(self.train_name)).getKnownState()==ACTIVE:
             self.controller.setActiveRequest(self.train_name,caller=function_name,status='startup',\
                                                    status_code=6001,status_reason='running')
                                                    
                                                    
             startup_sequence=self.controller.active_requests[self.train_name]['train_instance'].startupSequence
             
             self.doSequence(startup_sequence)
                                                    
             self.controller.setActiveRequest(self.train_name,caller=function_name,status='startup',\
                                                    status_code=6001,status_reason='complete')
             return
          
      def doSequence(self,sequences):
          function_name='f(doSequence)'
          for sequence in sequences: 
              
              for key,times in sequence.items():
                  delay=times[0]
                  duration=times[1]
                  self.waitMsec(delay*1000)
                  print("Startup/Shutdown doing {}".format(key))
                  exec("self.throttle.set{}(True)".format(key))
                  self.waitMsec(int(duration)*1000)
                  if int(duration)>0:
                     exec("self.throttle.set{}(False)".format(key))
              
      '''
      #=========================================================================================================================================
      # Run the shutdown sequence
      #==========================================================================================================================================
      '''
      def runStopSequence(self):
          function_name='f(runStopSequence)'
          if self.sensor_manager.getSensor("MS:IS:startup:{}".format(self.train_name)).getKnownState()==ACTIVE:
             self.controller.setActiveRequest(self.train_name,caller=function_name,status='shutdown',\
                                                    status_code=6001,status_reason='running')
                                                    
             shutdown_sequence=self.controller.active_requests[self.train_name]['train_instance'].stopSequence
                                                    
             self.controller.setActiveRequest(self.train_name,caller=function_name,status='shutdown',\
                                                    status_code=6001,status_reason='complete')
             self.doSequence(shutdown_sequence)
             
             self.printMsg._print(function_name,"DISPATCHER",self.train_name,'Finished ',state='FINISHED')
          return
      '''
      #=========================================================================================================================================
      # Set any subroute turnouts as defined in the route profile
      #==========================================================================================================================================
      '''
      def setTrainTurnouts(self,subroute):
          for sensor in subroute:
              if sensor in self.route_instance.turnouts:
                  for turnout_name,value in self.route_instance.turnouts[sensor].items():
                      if  value.upper()  == "CLOSED": value=CLOSED
                      elif value.upper() == "THROWN"  or value.upper() =="OPEN" : value=THROWN
                      
                      self.turnout_manager.getTurnout(turnout_name).setState(value)
          return
      '''
      #========================================================================================================================================
      # process any flags we need to - should only be called on the first loop
      #=========================================================================================================================================
      '''
      def setFlags(self):
          flags=self.controller.active_requests[self.train_name]['flags']
          for flag in flags:
              if flag=='sound':
                 if flags['sound']==True or flags['sound']=='True':
                    self.sensor_manager.getSensor("MS:IS:sound:{}".format(self.train_name)).setKnownState(INACTIVE)
                    self.sensor_manager.getSensor("MS:IS:sound:{}".format(self.train_name)).setKnownState(ACTIVE)
                 else:
                    self.sensor_manager.getSensor("MS:IS:sound:{}".format(self.train_name)).setKnownState(INACTIVE)
              elif flag=='fade':
                   if flags['fade']==True or flags['fade']=='True':
                      self.sensor_manager.getSensor("MS:IS:fade:{}".format(self.train_name)).setKnownState(INACTIVE)
                      self.sensor_manager.getSensor("MS:IS:fade:{}".format(self.train_name)).setKnownState(ACTIVE)
                   else:
                      self.sensor_manager.getSensor("MS:IS:fade:{}".format(self.train_name)).setKnownState(INACTIVE) 
              elif flag=='hold':
                   if flags['hold']==True or flags['hold']=='True':
                      flag_state=ACTIVE
                   else:
                      flag_state=INACTIVE
                   self.sensor_manager.getSensor("MS:IS:hold:{}".format(self.train_name)).setKnownState(flag_state)    
              elif flag=='wait':
                   if flags['wait']==True or flags['wait']=='True':
                      flag_state=ACTIVE
                   else:
                      flag_state=INACTIVE
                   self.sensor_manager.getSensor("MS:IS:wait:{}".format(self.train_name)).setKnownState(flag_state)  
              elif flag=='keys':
                   if flags['keys']==True or flags['keys']=='True':
                      flag_state=ACTIVE
                   else:
                      flag_state=INACTIVE
                   self.sensor_manager.getSensor("MS:IS:keys:{}".format(self.train_name)).setKnownState(flag_state)
              elif flag=='startup':
                   if flags['startup']==True or flags['startup']=='True':
                      flag_state=ACTIVE
                   else:
                      flag_state=INACTIVE
                   self.sensor_manager.getSensor("MS:IS:startup:{}".format(self.train_name)).setKnownState(flag_state)      
      '''
      #=========================================================================================================================================
      # Set any subroute key sensors
      #
      # self.fwdKeySensorsByTrain     = {"shunt3026":{"MS:BS:BS01_35" :{"MS:PS:PS01_14" :("key_seq_1","K2"),
      #                                                                 "MS:PS:PS01_5"  :("key_seq_2",)},
      #                                               "MS:BS:BS01_33" :{"MS:PS:PS01_13" :("key_seq_1",)}
      #                                              },
      #                                  "engine4035":{"MS:BS:BS01_35":{"MS:BS:BS01_35" : ("key_seq_1",)}
      #                                               }
      #                                 } 
      #
      # self.revKeySensorsByTrain     = {"shunt8691":{"MS:BS:BS01_35" :{"MS:PS:PS01_14"  :("key_seq_3",),
      #                                                                 "MS:PS:PS01_13"  :("key_seq_2",)}
      #                                              }
      #                                 } 
      #
      # if this was shunt8691 this would would have been prepared during the buildRoute process and
      # key_sensors would look similar to 
      #
      #      {'MS:BS:BS01_35': {'MS:PS:PS01_13': ('key_seq_2',), 'MS:PS:PS01_14': ('key_seq_3',)}}
      #
      # and if the subroute was ('MS:BS:BS01_34','MS:BS:BS01_35')
      #
      # then because MS:BS:BS01_35 is booked we would set a key sensor up for MS:PS:PS01_13 and MS:PS:PS01_14
      #
      #      train_name   = shunt8691
      #      sensor       = MQTT sensor => MS:PS:PS01_13
      #      key_sequence = ('key_seq_2',)
      #
      # and
      #
      #      train_name   = shunt8691
      #      sensor       = MQTT sensor => MS:PS:PS01_14
      #      key_sequence = ('key_seq_3',)
      #
      #==========================================================================================================================================
      '''
      def setTrainKeySensors(self,subroute):
          if self.route_direction=='FORWARD': key_sensors = self.fwd_key_sensors
          else: key_sensors = self.rev_key_sensors
          for sensor in subroute:
              if sensor in key_sensors:
                 for key_sensor_name,key_sequence in key_sensors[sensor].items():
                     listener=layoutListeners.layoutListeners()
                     key_sensor=self.sensor_manager.provideSensor(key_sensor_name)
                     listener.setListener(caller='setTrainKeySensor',train_name=self.train_name,sensor=key_sensor,key_sequence=key_sequence,listener_reference="TRAIN_{}_keys_SENSOR".format(self.train_name),controller=self.controller)
          return
      '''    
      #--------------------------------------------------------------------------------------------------------
      # We will dispatch the train so clear its name form any block values and put its name in the start block
      #--------------------------------------------------------------------------------------------------------
      '''
      def setBlockTrainName(self,subroute):
          first_block_sensor_name=subroute[0][0]
          
          for block in self.block_manager.getNamedBeanSet():
              block_sensor = block.getSensor()
              #print(str(block_sensor),type(subroute[0]),subroute[0])
              if str(block_sensor)==first_block_sensor_name:
                    block.setValue(self.train_name)
              elif block.getValue()==self.train_name:
                   block.setValue("")
      '''
      #=========================================================================================================================================
      # Set any subroute approach sensors if the last block is active and we cannot book the next subroute
      #==========================================================================================================================================
      '''
      def setDispatchHold(self,subroute,retry):
          function_name='f(setDispatchHold)'
          with self.controller.active_requests[self.train_name]['speed_lock']:
               if self.route_direction=='FORWARD'  and len(self.route_instance.fwdAppStopSensorsByTrain)>0:
                  approach_sensors = self.route_instance.fwdAppStopSensorsByTrain
               else:
                  approach_sensors = self.route_instance.revAppStopSensorsByTrain
                  
               self.printMsg._print(function_name,"WARNING",self.train_name,"dispactcher hold applied while booking subroute {}".format(subroute))
               #
               # Set up a listener for the approach sensor going active
               #
               if self.train_name in approach_sensors:
                  if subroute[0] in approach_sensors[self.train_name] :
                     approach_sensor_dict=approach_sensors[self.train_name][subroute[0]]
                     self.throttle.setSpeedSetting(0)
                     for approach_sensor_name,approach_speed in approach_sensor_dict.items():
                         print(approach_sensor_name,approach_speed,self.route_direction)
                         self.throttle.setSpeedSetting(approach_speed)
                         speed=approach_speed
                         self.printMsg._print(function_name,'DISPATCHER',self.train_name,"forcing speed to apporach speed {} and settign upp approach listener {}".format(approach_speed,approach_sensor_name))
                         approach_sensor=self.sensor_manager.getSensor(approach_sensor_name)
                         self.dispatch_hold_sensor=approach_sensor
                         break
                     
                     listener=layoutListeners.layoutListeners()
                     
                     listener.setListener(caller='setDispatchHold',train_name=self.train_name,speed=approach_speed,sensor=approach_sensor,\
                                          listener_reference="TRAIN_{}_approach_SENSOR".format(self.train_name),controller=self.controller)
               else:
                  self.throttle.setSpeedSetting(0)
               self.sensor_manager.getSensor('MS:IS:dispatcher_hold:{}'.format(self.train_name)).setKnownState(ACTIVE)
          return
      
      def releaseDispatchHold(self,subroute):
          function_name='f(releaseDispatchHold)'
          with self.controller.active_requests[self.train_name]['speed_lock']:
               if self.sensor_manager.getSensor('MS:IS:dispatcher_hold:{}'.format(self.train_name)).getKnownState()==ACTIVE:
                  self.sensor_manager.getSensor('MS:IS:dispatcher_hold:{}'.format(self.train_name)).setKnownState(INACTIVE)
                  self.printMsg._print(function_name,"WARNING",self.train_name,"dispactcher hold removed for subroute {}".format(subroute))
               
      '''
      #=========================================================================================================================================
      # Turn on the route complete sensor
      #==========================================================================================================================================
      '''
      def setRouteCompleteSensor(self,subroute):
          function_name='f(setRouteCompleteSensor)' 
          if self.route_direction=='FORWARD':
             route_complete_sensor_name=self.fwd_complete_sensor
          else:
             route_complete_sensor_name=self.rev_complete_sensor
              
          self.controller.setActiveRequest(self.train_name,caller=function_name,route_complete_sensor_name=route_complete_sensor_name)
          
          jmri_sensor=self.sensor_manager.getSensor(route_complete_sensor_name)
          listener=layoutListeners.layoutListeners()
          listener.setListener(caller='setRouteComlpeteSensor',train_name=self.train_name,sensor=jmri_sensor,listener_reference="TRAIN_{}_route_complete_SENSOR".format(self.train_name),controller=self.controller)
          return
      '''
      #=========================================================================================================================================
      # Turn create the loop complete sensor. this is the laasst block sensor in the subroute
      #==========================================================================================================================================
      '''
      def setLastBlockSensor(self,subroute):
          function_name='f(setLastBlockSensor)'
          last_block_sensor_name=subroute[len(subroute)-1:][0]
          self.controller.setActiveRequest(self.train_name,caller=function_name,last_block_sensor_name=last_block_sensor_name)
          
          jmri_sensor=self.sensor_manager.getSensor(last_block_sensor_name)
          listener=layoutListeners.layoutListeners()
          listener.setListener(caller='setLastBlockListener',train_name=self.train_name,sensor=jmri_sensor,listener_reference="TRAIN_{}_last_block_SENSOR".format(self.train_name),controller=self.controller)
          return
      '''
      #=========================================================================================================================================
      # If any sensors or blocks trigger a change in speed as defined by 
      #==========================================================================================================================================
      '''
      def setTrainSpeedSensors(self,subroute,mode='add'):
          function_name='f(setTrainSpeedSensor)'
          if self.route_direction=='FORWARD': speed_sensors =  self.fwd_speed_sensors
          else: speed_sensors = self.rev_speed_sensors 
          
          for booked_block_sensor,speed_sensors_to_set in speed_sensors.items(): 
              if booked_block_sensor in subroute:
                 for speed_sensor,speed in speed_sensors_to_set.items():
                     listener=layoutListeners.layoutListeners()
                     jmri_sensor=self.sensor_manager.getSensor(speed_sensor)
                     listener.setListener(caller='setTrainSpeedSensor',train_name=self.train_name,sensor=jmri_sensor,speed=speed,mode=mode,\
                                           listener_reference="TRAIN_{}_speed_SENSOR".format(self.train_name),controller=self.controller)
          return
      '''
      #=========================================================================================================================================
      # If any sensors or blocks trigger a change in speed as defined by 
      #==========================================================================================================================================
      '''
      def setTrainWaitSensors(self,subroute,mode='add'):
          function_name='f(setTrainWaitSensor)'
          if self.route_direction=='FORWARD': wait_sensors =  self.fwd_wait_sensors
          else: wait_sensors = self.rev_wait_sensors 
          
          for booked_block_sensor,wait_sensors_to_set in wait_sensors.items(): 
              if booked_block_sensor in subroute:
                 for wait_sensor,wait_time in wait_sensors_to_set.items():
                     listener=layoutListeners.layoutListeners()
                     jmri_sensor=self.sensor_manager.getSensor(wait_sensor)
                     listener.setListener(caller='setTrainWaitSensors',train_name=self.train_name,sensor=jmri_sensor,wait_time=wait_time,mode=mode,\
                                          listener_reference="TRAIN_{}_wait_SENSOR".format(self.train_name),controller=self.controller)
          return
      '''
      #=========================================================================================================================================
      # Get a driver to move the engine along a subroute
      #==========================================================================================================================================
      '''
      def setTrainRunning(self,subroute='UNKNOWN',terminate=False):
          function_name='f(setTrainRunning)'
          if terminate:
             self.sensor_manager.getSensor("MS:IS:terminate:{}".format(self.train_name)).setKnownState(ACTIVE)
          else:
             self.sensor_manager.getSensor("MS:IS:terminate:{}".format(self.train_name)).setKnownState(INACTIVE)    

          self.sensor_manager.getSensor("MS:IS:running:{}".format(self.train_name)).setKnownState(ACTIVE)
          
          self.printMsg._print(function_name,"DISPATCHER",self.train_name,'cleared for subroute {}, {}'.format(subroute,self.route_direction),state='DISPATCHED')
          self.controller.setActiveRequest(self.train_name,caller=function_name,status="subroute running",status_reason=subroute,status_code=6001)
  
          return
      '''
      #=========================================================================================================================================
      # wait on the last block sensor in a subroute going active or terminate or route complete.
      #
      # If running goes inactive then this is either the end  of a subroute or the end of the entire run
      # if Terminate goe ACTIVE then we have been terminated
      # if it is the last blocksensor in a sub route going active then we should try and book the next subroute
      #==========================================================================================================================================
      '''
      def waitOnSensors(self,subroute):
          function_name='f(waitOnSensors)'
          last_sensor_of_subroute=subroute[len(subroute)-1]

          running_sensor       = self.sensor_manager.getSensor("MS:IS:running:{}".format(self.train_name))
          terminate_sensor     = self.sensor_manager.getSensor("MS:IS:terminate:{}".format(self.train_name))

          while True:          
                self.waitChange([terminate_sensor,running_sensor])
          
                if terminate_sensor.getKnownState()   == ACTIVE:   return 1
                if running_sensor.getKnownState()     == INACTIVE: return 2
      '''
      #=========================================================================================================================================
      # 
      #==========================================================================================================================================
      '''
      def isTerminateSet(self):
          sn="MS:IS:terminate:{}".format(self.train_name)
          sensor_state=self.sensor_manager.getSensor(sn).getKnownState()
          if sensor_state==ACTIVE: 
             return True
          else: return False
      '''
      #=========================================================================================================================================
      # 
      #==========================================================================================================================================
      '''
      def isRunningSet(self):
          sn="MS:IS:running:{}".format(self.train_name)
          sensor_state=self.sensor_manager.getSensor(sn).getKnownState()
          if sensor_state==ACTIVE: return True
          else: return False
      '''
      #=========================================================================================================================================
      # Dispatch A train on a route. The request is as defined in the layoutController.py file active_requests dictionary
      #
      # build all the subroutes for a train on a given route. Note. The train profile and route profile must have been validated before the
      # train is dispatched.
      #
      #==========================================================================================================================================
      '''
      def buildRoute(self):
          try:
             
             function_name='f(buildRoute)'
             
             self.printMsg._print(function_name,'BUILD',self.train_name,'building all subroutes for train {} on route {}'.format(self.train_name,self.route_name),state='BUILD') 
             
             self.controller.setActiveRequest(self.train_name,caller=function_name,status='building',status_reason='sub routes')

             if str(self.look_ahead).upper() == 'NONE': self.look_ahead = self.route_instance.lookAhead
             
             if str(self.loops).upper() == 'NONE': self.loops = self.route_instance.route_loops
             
             self.max_speed                  = self.route_instance.maxSpeed
             self.fwd_complete_sensor        = self.route_instance.fwdCompleteSensor
             self.rev_complete_sensor        = self.route_instance.revCompleteSensor
             self.fwd_app_speed_default      = self.route_instance.fwdAppSpeedDefault
             self.rev_app_speed_default      = self.route_instance.revAppSpeedDefault
             
             
             if self.train_name in self.route_instance.revWaitTimeByTrain:
                self.rev_wait_time=self.route_instance.revWaitTimeByTrain[self.train_name]
             else:
                self.rev_wait_time=self.route_instance.revWaitTimeDefault
           
             if self.train_name in self.route_instance.fwdWaitTimeByTrain:
                self.fwd_wait_time=self.route_instance.fwdWaitTimeByTrain[self.train_name]
             else:
                self.fwd_wait_time=self.route_instance.fwdWaitTimeDefault 
                
             #
             # Define the forward and reverse sub routes
             #
             self.fwd_subroutes=self.getSubRoutes(self.route_instance.routePathSensors)
    
             self.rev_subroutes=self.getSubRoutes(tuple(reversed(self.route_instance.routePathSensors)))
             
             #
             # Define the start speed sensors forward and reverse
             #         
             if self.train_name in self.route_instance.fwdStartSpeedByTrain:
                self.fwd_start_speed=self.route_instance.fwdStartSpeedByTrain[self.train_name]
             else:
                self.fwd_start_speed=self.route_instance.fwdStartSpeedDefault
           
             if self.train_name in self.route_instance.revStartSpeedByTrain:
                self.rev_start_speed=self.route_instance.revStartSpeedByTrain[self.train_name]
             else:
                self.rev_start_speed=self.route_instance.revStartSpeedDefault
             #
             # Define the forward and reverse speed sensors
             #   
             if self.train_name in self.route_instance.revSpeedSensorsByTrain:
                self.rev_speed_sensors=self.route_instance.revSpeedSensorsByTrain[self.train_name]
             else:
                self.rev_speed_sensors={}
             if self.train_name in self.route_instance.fwdSpeedSensorsByTrain:
                self.fwd_speed_sensors=self.route_instance.fwdSpeedSensorsByTrain[self.train_name]
             else:
                self.fwd_speed_sensors={}
             #
             # Set the approach speed sensors
             #
             if self.train_name in self.route_instance.revAppStopSensorsByTrain:
                self.rev_app_stop_sensors=self.route_instance.revAppStopSensorsByTrain[self.train_name]
             else:
                self.rev_app_stop_sensors={}
             if self.train_name in self.route_instance.fwdAppStopSensorsByTrain:
                self.fwd_app_stop_sensors=self.route_instance.fwdAppStopSensorsByTrain[self.train_name]
             else:
                self.fwd_app_stop_sensors={}
             #
             # Define the key sensors forward and reverse
             #   
             if self.train_name in self.route_instance.revKeySensorsByTrain:
                self.rev_key_sensors=self.route_instance.revKeySensorsByTrain[self.train_name]
             else:
                self.rev_key_sensors={}
             if self.train_name in self.route_instance.fwdKeySensorsByTrain:
                self.fwd_key_sensors=self.route_instance.fwdKeySensorsByTrain[self.train_name]
             else:
                self.fwd_key_sensors={}
             #
             # Define the wait sensors
             #
             if self.train_name in self.route_instance.fwdWaitSensorsByTrain:
                self.fwd_wait_sensors=self.route_instance.fwdWaitSensorsByTrain[self.train_name]
             else:
                 self.fwd_wait_sensors={}
             if self.train_name in self.route_instance.revWaitSensorsByTrain:
                self.rev_wait_sensors=self.route_instance.revWaitSensorsByTrain[self.train_name]
             else:
                 self.rev_wait_sensors={}
                    
                
             self.controller.setActiveRequest(self.train_name,caller=function_name,status='built',status_reason='sub routes')
             self.printMsg._print(function_name,'BUILD',self.train_name,'build of subroutes for train {} on route {} complete'.format(self.train_name,self.route_name),state='BUILT') 
             #
             # Define the signals when a block cannot be booked
             #
             self.fwd_not_booked_signals=self.route_instance.fwdSignals
             self.rev_not_booked_signals=self.route_instance.revSignals
          except:
              print(traceback.format_exc())
              return False
          return True

      """
      #--------------------------------------------------------------------------------------------
      # From the associated sensor path get the sub routes that the engine will travel along
      #--------------------------------------------------------------------------------------------
      """
      def getSubRoutes(self,sensor_path):
          try:
              subroutes=[]
              new_subroute=[]
              y=0
                
              while y<len(self.route_instance.routePathSensors):
                 x=0; 
                 new_subroute=[]
                 while x  <= int(self.look_ahead) :
                    if y<len(self.route_instance.routePathSensors):
                       new_subroute.append(sensor_path[y])
                    x+=1 ; y+=1
                 subroutes.append(new_subroute)
          except:
              print(traceback.format_exc()) 
          return subroutes
      """
      #------------------------------------------------------------------------------------------------
      # Print the route
      #------------------------------------------------------------------------------------------------
      """
      def printRoute(self):
          function_name='f(printRoute)'
          try:
               t=20                               # miliseconds
               self.printMsg._print(function_name,"ROUTE",self.train_name,"\n\n =====================================  description  ========================================");self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name," route name                    : {}".format(self.route_instance.routeName));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name," route description             : {}".format(self.route_instance.routeDescription));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name," route mode                    : {}".format(self.mode));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name," route route_direction         : {}".format(self.route_direction));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name," route loops                   : {}".format(self.route_loops));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name," look ahead..                  : {}".format(self.look_ahead));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name," =====================================  forward route  =======================================");self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name," blocks   fwd route            : {}".format(self.route_instance.routePathBlocks));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name," sensors  fwd route            : {}".format(self.route_instance.routePathSensors));self.waitMsec(t)
               #self.printMsg._print(function_name,"ROUTE",self.train_name," =====================================  reverse route =======================================");self.waitMsec(t)
               #self.printMsg._print(function_name,"ROUTE",self.train_name," blocks   rev route            : {}".format(self.route_instance.revRoutePathBlocks));self.waitMsec(t)
               #self.printMsg._print(function_name,"ROUTE",self.train_name," sensors  rev route            : {}".format(self.route_instance.revRoutePathSensors));self.waitMsec(t)
               #
               #
               # Do the forward sub routes and their turnouts
               #
               self.printMsg._print(function_name,"ROUTE",self.train_name," ===================================  forward sub routes  ===================================");self.waitMsec(t)
               
               for  x,subroute in enumerate(self.fwd_subroutes):
                  if len(self.fwd_subroutes)==1: pos="First"
                  elif x==0: pos="First"
                  elif x==len(self.fwd_subroutes)-1:
                     pos="Last "
                  else: pos=" "*5
                  self.printMsg._print(function_name,"ROUTE",self.train_name," {} route {:04d}              : {}".format(pos,x,subroute));self.waitMsec(t)
               #
               # Do the reverse sub routes and their turnouts
               #
               self.printMsg._print(function_name,"ROUTE",self.train_name," ===================================  reverse sub routes  ===================================");self.waitMsec(t)
               
               for  x,subroute in enumerate(self.rev_subroutes):
                  if len(self.rev_subroutes)==1: pos="First"
                  elif x==0: pos="First"
                  elif x==len(self.rev_subroutes)-1:
                     pos="Last "
                  else: pos=""
                  self.printMsg._print(function_name,"ROUTE",self.train_name," {} route {:04d}              : {}".format(pos,x,subroute));self.waitMsec(t)
                  for block_sensor in subroute:
                     if block_sensor in self.route_instance.turnouts:
                        self.printMsg._print(function_name,"ROUTE",self.train_name,"                               : requres turnouts {}".format(self.route_instance.turnouts[block_sensor]));self.waitMsec(t)
                     if block_sensor in self.route_instance.signals:
                        self.printMsg._print(function_name,"ROUTE",self.train_name,"                               : requres signals  {}".format(self.route_instance.signals[block_sensor]));self.waitMsec(t)
               
               if self.train_name in self.route_instance.fwdWaitSensorsByTrain:
                  self.fwd_wait_sensors=self.route_instance.fwdWaitSensorsByTrain[self.train_name]
           
               if self.train_name in self.route_instance.revWaitSensorsByTrain:
                  self.rev_wait_sensors=self.route_instance.revWaitSensorsByTrain[self.train_name]
                  
               self.printMsg._print(function_name,"ROUTE",self.train_name,"====================================  speed sensors  ======================================");self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"maximum speed                 : {}".format(self.max_speed));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"reverse start speed           : {}".format(self.rev_start_speed));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"forward start speed           : {}".format(self.fwd_start_speed));self.waitMsec(t) 
               self.printMsg._print(function_name,"ROUTE",self.train_name,"forward speed Sensors         : {}".format(self.fwd_speed_sensors));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"reverse speed Sensors         : {}".format(self.rev_speed_sensors));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"==================================== ==  key sensors  =====================================");self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"forward key Sensors           : {}".format(self.fwd_key_sensors));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"reverse key Sensors           : {}".format(self.rev_key_sensors)) ;self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"=================================  route complete sensors  ================================");self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"forward complete sensor       : {}".format(self.fwd_complete_sensor));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"reverse complete sensor       : {}".format(self.rev_complete_sensor));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"========================================  wait times ======================================");self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"reverse wait time             : {}".format(self.rev_wait_time));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"forward wait time             : {}".format(self.fwd_wait_time));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"========================================  wait sensors ======================================");self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"reverse wait sensors          : {}".format(self.rev_wait_sensors));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"forward wait sensors          : {}".format(self.fwd_wait_sensors));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"======================================  dynamic sensors  ==================================");self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"forward app speed default     : {}".format(self.rev_app_speed_default));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"reverse app speed default     : {}".format(self.fwd_app_speed_default));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"forward approach stop sensors : {}".format(self.fwd_app_stop_sensors));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"reverse approach stop sensors : {}".format(self.rev_app_stop_sensors));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"forward key sensors           : {}".format(self.fwd_key_sensors));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"reverse key sensors           : {}".format(self.rev_key_sensors));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"=========================================  turnouts  =====================================");self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"turnouts                      : {}".format(self.route_instance.turnouts));self.waitMsec(t)
               self.printMsg._print(function_name,"ROUTE",self.train_name,"==========================================================================================")
          except :
               print(traceback.format_exc())
           
