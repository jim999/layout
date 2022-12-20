import ast
import time
import traceback
import threading
 
import java
import java.beans
import jmri

import layoutConfig
#import layoutGlobals
import layoutUtils as utils

from jmri_bindings import *

'''
#======================================================================================================================================
#
# Class      : layoutListeners
#
# sensor              : the sensor a listener has to be set up for
#
# train_name          : the name of the engine that the listenre has to be set up for
#
# speed               : if this is a speed sensor then this is the speed otherwise None
#
# key_Sequence        : if this is a key sensor then this is the sequence to be done when the sensor goes active. for example
#                       ('key_seq_2','key_seq_3') that are defined in the train profile.
#
#                       Note: the key sequences to use are defined in the route profile and the train profile. The route profiel defines
#                             the sequences to use and the train profile defines the the keys to be pressed
#
# listener_reference  :
#
# controller          : a ponter to the controller
#
# wait_time           : if this is a wait sensor being set up then this is the timr to wait when it goes active
#
#=======================================================================================================================================
'''
class layoutListeners(jmri.jmrit.automat.AbstractAutomaton):
    def __init__(self,caller=None):
       self.printMsg=utils.printMsg(caller="layoutListeners",controller=None)
       self.function_name=("f(__init__)")
       self.sensor_manager = sensors 
       
    def init(self):
        return
    def handle(self):
        return
    def setListener(self,caller=None,sensor=None,train_name='system',listener_reference=None,mode='ADD',key_sequence=None,controller=None,speed=None,wait_time=None):
        function_name      = "f(setListener)" 
         
        self.caller             = caller
        self.train_name         = train_name
        self.sensor             = sensor
        self.speed              = speed
        self.wait_time          = wait_time
        self.listener_reference = listener_reference
        self.controller         = controller
        self.mode               = mode
        self.key_sequence       = key_sequence
        
        try:
           
           self.new_listener=None
           #---------------------------------------------------------------------------------------------------------------------------------
           # If we have been here before delete the old listener and add the new one
           #---------------------------------------------------------------------------------------------------------------------------------
           try:
              for oldListener in sensor.getPropertyChangeListenersByReference(train_name):
                  if str(sensor.getListenerRef(oldListener)) == listener_reference :
                     
                     self.printMsg._print(function_name,"REMOVE_LISTENER",train_name,"Removing old listener for sensor {} ref({}) registered name {}, caller was {} "\
                         .format(self.sensor,listener_reference,train_name,self.caller)) 
                     
                     sensor.removePropertyChangeListener(oldListener)
                     
                            
              if mode.upper()=="ADD" :
                 self.printMsg._print(function_name,"ADD_LISTENER",train_name,"Adding new listener for sensor {} ref({}) registered name {},caller was {} )"\
                      .format(self.sensor,listener_reference,train_name,self.caller))
                 
                 listener=_LISTENER(train_name=train_name,sensor=self.sensor,speed=self.speed,wait_time=self.wait_time,\
                                    key_sequence=key_sequence,listener_reference=listener_reference,controller=controller)

                 sensor.addPropertyChangeListener(listener,train_name,listener_reference)
           
           except Exception as err:
              self.printMsg._print(function_name,"ERROR",train_name,"Adding new listener ref({}) for entity : {}, caller was for sensor {}"\
                  .format(str(listener_reference)+" "+str(train_name),train_name,self.caller,self.sensor))
              print(traceback.format_exc())    
              self.printMsg._print(function_name,"ERROR",train_name,"{}".format(traceback.format_exc()))
        except java.lang.Exception as err:
           print("Got java lang error")
           print(traceback.format_exc())
        except:
            print(traceback.format_exc())
           
'''
#======================================================================================================================================
# The actual jmri listener
#======================================================================================================================================
'''
class _LISTENER(java.beans.PropertyChangeListener,jmri.jmrit.automat.AbstractAutomaton):
    def __init__(self,train_name='system',sensor=None,key_sequence=None,listener_reference=None,controller=None,wait_time=None,speed=None):
        
        self.train_name         = train_name
        
        
        self.sensor             = sensor                                                            # the sensor we are for  
        self.sensor_manager     = sensors 
        self.controller         = controller
        self.listener_reference = listener_reference
        self.key_sequence       = key_sequence
        
        self.printMsg           = utils.printMsg(caller="_LISTENER",controller=self.controller)
        
        self.tcpBMClient        = utils.tcpClient(caller='_LISTENER',manager_type='bookingmanager')
        self.tcpCTRLClient      = utils.tcpClient(caller='_LISTENER',manager_type='controller')

        if self.train_name     != 'system':
           self.max_speed       = 0 
           self.speed           = speed                                                              # speed used when speed sensor activated
           self.wait_time       = wait_time                                                          # time in seconds used when a wait sensor is activated
           self.route_direction = 'UNKNOWN'

           self.route_instance  = self.controller.active_requests[self.train_name]['route_instance']
           self.train_instance  = self.controller.active_requests[self.train_name]['train_instance']
              
           self.throttle_num_long  = self.controller.active_requests[self.train_name]['train_instance'].throttleNumLong
           self.throttle_number    = self.controller.active_requests[self.train_name]['train_instance'].throttleNumber
           
           self.throttle      = self.controller.getThrottle(self.throttle_number,self.throttle_num_long,1)
    '''
    #======================================================================================================================================
    # If sensor changes state then do this
    #======================================================================================================================================
    '''
    def propertyChange(self, event):
        pc=processPropertyChange(event=event,propertyChange=self,controller=self.controller,sensor=self.sensor,key_sequence=self.key_sequence)
        pc.start()

class processPropertyChange(jmri.jmrit.automat.AbstractAutomaton):
    def __init__(self,event,propertyChange=None,controller=None,sensor=None,key_sequence=None):
        
        self.tcpBMClient                  = utils.tcpClient(caller='_LISTENER',manager_type='bookingmanager')
        
        self.event                        = event
        self.sensor                       = sensor
        self.propertyChange               = propertyChange
        self.controller                   = controller
        self.train_name                   = self.propertyChange.train_name
        
        self.listener_reference           = self.propertyChange.listener_reference
        self.sensor_manager               = self.propertyChange.sensor_manager
        
        self.wait_running_sensor_name     = "MS:IS:wait_running:{}".format(self.train_name)
        self.dispatcher_hold_sensor_name  = "MS:IS:dispatcher_hold:{}".format(self.train_name)
        self.printMsg                     = utils.printMsg(caller="processPChange",controller=self.controller)
        
        if self.train_name != 'system':
           self.throttle       = self.propertyChange.throttle
           self.speed          = self.propertyChange.speed
           self.wait_time      = self.propertyChange.wait_time
           self.train_instance = self.propertyChange.train_instance
           self.key_sequence   = self.propertyChange.key_sequence
        
    def init(self):
        return
    def handle(self):
        try: 
           function_name="f(propertyChange)"

           self.old_value = self.event.source.describeState(self.event.oldValue) 
           self.new_value = self.event.source.describeState(self.event.newValue)
           self.source    = self.event.source
           #====================================================================================================================
           # If this is a BLOCK_OCCUPIED_SENSOR change then let the booking manager know that a block state has changed
           #====================================================================================================================
           if self.listener_reference.upper()=='BLOCK_OCCUPIED_SENSOR':
              self.printMsg._print(function_name,'S_CHANGE_BLOCK','system',"detected property change event : oldValue {} newVAlue {} for {}".format(self.old_value,self.new_value,self.source))
              value=self.event.source.describeState(self.event.source.getKnownState())
              command="{{'cmd':'set_sensors','sensors':'{}','value':'{}' }}" .format(self.event.source,value)
              resp=self.tcpBMClient.sendData(data=command)
           #====================================================================================================================
           # Is this is Fade then either turn on or turn off the fade function key for the engine
           #====================================================================================================================
           elif self.listener_reference=='TRAIN_{}_sound_SENSOR'.format(self.train_name):
              self.printMsg._print(function_name,'S_CHANGE_sound','system',"detected property change event : oldValue {} newValue {} for {}".format(self.old_value,self.new_value,self.source))
              #
              # get the sound key from the train profile
              #
              try:
                sound_key=self.train_instance.sound
                if self.event.newValue==ACTIVE:
                   exec("self.throttle.set{}(True)".format(sound_key))
                else:
                   exec("self.throttle.set{}(False)".format(sound_key))
              except:
                self.printMsg._print(function_name,'WARNING',self.train_name,"sound requested but sound key is not defined in the train profile")    
           #====================================================================================================================
           # Is this is Fade then either turn on or turn off the fade function key for the engine
           #====================================================================================================================
           elif self.listener_reference=='TRAIN_{}_fade_SENSOR'.format(self.train_name):
              self.printMsg._print(function_name,'S_CHANGE_fade','system',"detected property change event : oldValue {} newValue {} for {}".format(self.old_value,self.new_value,self.source))
              #
              # get the fade key from the train profile
              #
              try:
                fade_key=self.train_instance.fade
                if self.event.newValue==ACTIVE:
                   exec("self.throttle.set{}(False)".format(fade_key))
                   self.waitMsec(1000)
                   exec("self.throttle.set{}(True)".format(fade_key))
                else:
                   exec("self.throttle.set{}(False)".format(fade_key))
              except:
                self.printMsg._print(function_name,'WARNING',self.train_name,"fade requested but fade key is not defined in the train profile")
           #====================================================================================================================
           # If the speed sensor changes state do this. If it goes active then save the speed in the active requests dictionary. 
           # If hold is not on and we are not waiting for a time to expire then set the speed.
           #
           # Note a speed sensor should only trigger once, so the property change listener is removed immediately.
           #
           #====================================================================================================================
           elif self.listener_reference=='TRAIN_{}_speed_SENSOR'.format(self.train_name):
              self.printMsg._print(function_name,'S_CHANGE_speed','system',"detected property change event : oldValue {} newValue {} for {}".format(self.old_value,self.new_value,self.source)) 
              if self.event.newValue==ACTIVE:
                  #
                  # A speed sensor should only trigger once so remove the property change listener
                  #
                  layoutListeners().setListener(caller=function_name+' speed_sensor',sensor=self.sensor,train_name=self.train_name,mode='remove',\
                                                 listener_reference='TRAIN_{}_speed_SENSOR'.format(self.train_name),controller=self.controller)

                  if layoutConfig.trace_active_requests_locks  :
                     self.printMsg._print(function_name,"LOCK",self.train_name,'speed requested active requests lock, thread {}'.format(threading.currentThread().getName()))
                  
                  with self.controller.active_requests[self.train_name]['speed_lock']:
                       self.controller.setActiveRequest(self.train_name,caller=function_name,speed=self.speed)
               
                       train_wait_state=self.sensor_manager.getSensor("MS:IS:hold:{}".format(self.train_name)).getKnownState()
                       train_hold_state=self.sensor_manager.getSensor("MS:IS:hold:{}".format(self.train_name)).getKnownState()
                       
                       if not (train_wait_state==ACTIVE or train_hold_state==ACTIVE):
                          self.throttle.setSpeedSetting(self.speed)
                          self.printMsg._print(function_name,'DRIVER_SP',self.train_name,"setting speed to {} (cause speed sensor)".format(self.speed)) 
                       
                       self.printMsg._print(function_name,'DRIVER',self.train_name,"saving new speed of {}".format(self.speed)) 
                       self.controller.setActiveRequest(self.train_name,caller=function_name,speed=self.speed)
                       
                  if layoutConfig.trace_active_requests_locks  :
                     self.printMsg._print(function_name,"LOCK",self.train_name,'speed releasing active requests lock, thread {}'.format(threading.currentThread().getName()))
           #====================================================================================================================
           # If the wait sensor changes state do this
           #====================================================================================================================
           elif self.listener_reference=='TRAIN_{}_wait_SENSOR'.format(self.train_name):
              
              self.printMsg._print(function_name,'S_CHANGE_wait','system',"detected property change event : oldValue {} newValue {} for {}".format(self.old_value,self.new_value,self.source)) 
              sensor_name="MS:IS:wait:{}".format(self.train_name)

              if self.event.newValue==ACTIVE:
                  #
                  # A wait sensor should only trigger once so remove the property change listener
                  #
                  layoutListeners().setListener(caller=function_name+' wait_sensor',sensor=self.sensor,train_name=self.train_name,mode='remove',\
                                                listener_reference='TRAIN_{}_wait_SENSOR'.format(self.train_name),controller=self.controller)
                  
                  if self.sensor_manager.getSensor(sensor_name).getKnownState() == ACTIVE:
                     if layoutConfig.trace_active_requests_locks  :
                         self.printMsg._print(function_name,"LOCK",self.train_name,'wait requested active requests lock, thread {}'.format(threading.currentThread().getName()))

                     with self.controller.active_requests[self.train_name]['speed_lock']:
                          self.controller.setActiveRequest(self.train_name,caller=function_name,status='wait',status_reason='wait sensor {} activated'.format(str(self.source))) 
                        
                          self.throttle.setSpeedSetting(0)
                      
                          self.printMsg._print(function_name,'DRIVER',self.train_name,'wait request received speed set to 0 and waiting for {} seconds'.format(self.wait_time),state='wait')
                          #
                          # let other functions know that we are in a wait loop
                          #
                          self.sensor_manager.getSensor(self.wait_running_sensor_name).setKnownState(ACTIVE)

                     if layoutConfig.trace_active_requests_locks  :self.printMsg._print(function_name,"LOCK",self.train_name,'wait releasing active requests lock, thread {}'.format(threading.currentThread().getName()))

                     count = 0

                     while count<self.wait_time:
                           self.waitMsec(1000)
                           if self.sensor_manager.getSensor(sensor_name).getKnownState()==INACTIVE :
                              break 
                           elif self.isTerminateSet(): break
                           else: count+=1
                           
                     if layoutConfig.trace_active_requests_locks  :
                        self.printMsg._print(function_name,"LOCK",self.train_name,'wait requested active requestslock, thread {}'.format(threading.currentThread().getName()))
                     
                     with self.controller.active_requests[self.train_name]['speed_lock']:
                          speed=self.controller.active_requests[self.train_name]['speed']
                          hold_sensor='MS:IS:hold:{}'.format(self.train_name)
                          if self.sensor_manager.getSensor(hold_sensor).getKnownState()==INACTIVE and\
                             self.sensor_manager.getSensor(self.dispatcher_hold_sensor_name).getKnownState()==INACTIVE:
                             
                             self.throttle.setSpeedSetting(speed)
                             
                             self.controller.setActiveRequest(self.train_name,caller=function_name,status='running',status_reason='wait time for sensor {} complete or wait sensor {} manually set to INACTIVE'.format(str(self.source),sensor_name))

                             self.printMsg._print(function_name,'DRIVER',self.train_name,'wait finished, speed set to {}'.format(speed),state='running')
                          
                          else:
                             self.printMsg._print(function_name,'DRIVER',self.train_name,'wait finished but hold or dispatcher hold ACTIVE ,remaining idle'.format(speed),state='hold')
                             
                             self.controller.setActiveRequest(self.train_name,caller=function_name,status='hold',status_reason='wait finished but hold sensor {} or dispatcher hold ACTIVE'.format(hold_sensor)) 
                          #
                          # let other functions know that wait is no longer running
                          #
                          self.sensor_manager.getSensor(self.wait_running_sensor_name).setKnownState(INACTIVE)
                          
                     if layoutConfig.trace_active_requests_locks  :
                        self.printMsg._print(function_name,"LOCK",self.train_name,'wait releasing active requests lock, thread {}'.format(threading.currentThread().getName()))
           #====================================================================================================================
           # If the hold sensor changes state do this
           #====================================================================================================================
           elif self.listener_reference=='TRAIN_{}_hold_SENSOR'.format(self.train_name):
              self.printMsg._print(function_name,'S_CHANGE_hold','system',"detected property change event : oldValue {} newValue {} for {}".format(self.old_value,self.new_value,self.source))
              
              if layoutConfig.trace_active_requests_locks  :
                 self.printMsg._print(function_name,"LOCK",self.train_name,'hold requested active requests lock, thread {}'.format(threading.currentThread().getName()))
              
              with self.controller.active_requests[self.train_name]['speed_lock']:
                   
                   self.speed=self.controller.active_requests[self.train_name]['speed']
                   
                   if self.event.newValue==ACTIVE:
                      self.throttle.setSpeedSetting(0) 
                      self.controller.setActiveRequest(self.train_name,caller=function_name,status='hold')
                      self.printMsg._print(function_name,'DRIVER',self.train_name,"hold request received, setting speed to 0.0 (cause hold sensor)")
                   else:
                      if self.sensor_manager.getSensor(self.wait_running_sensor_name).getKnownState()==INACTIVE and\
                         self.sensor_manager.getSensor(self.dispatcher_hold_sensor_name).getKnownState()==INACTIVE:
                         speed=self.controller.active_requests[self.train_name]['speed']
                         self.throttle.setSpeedSetting(speed) 
                         self.active_subroute=self.controller.active_requests[self.train_name]['active_subroute']
                         self.controller.setActiveRequest(self.train_name,caller=function_name,status='subroute running',status_reason=self.active_subroute)
                         self.printMsg._print(function_name,'DRIVER',self.train_name,"hold request released, setting speed to {} (cause hold sensor)".format(speed),state='running')
                      else:
                         self.printMsg._print(function_name,'DRIVER',self.train_name,"hold request released, but train still in wait state or dispatcher hold",state='wait') 
                  
              if layoutConfig.trace_active_requests_locks  :
                 self.printMsg._print(function_name,"LOCK",self.train_name,'hold releasing speed lock, thread {}'.format(threading.currentThread().getName()))
           #====================================================================================================================
           # if this is a train terminating 
           # 
           # Stop the train immediately, then delete any TRAIN listeners for example TRAIN_shunt8691_terminate_SENSOR
           # 
           #====================================================================================================================
           elif self.listener_reference=='TRAIN_{}_terminate_SENSOR'.format(self.train_name):
              self.printMsg._print(function_name,'S_CHANGE_terminate','system',"detected property change event : oldValue {} newValue {} for {}".format(self.old_value,self.new_value,self.source))
              
              if self.event.newValue==ACTIVE:

                 if self.train_name!='system':

                    self.throttle.setSpeedSetting(-1)  
                 
                    self.controller.setActiveRequest(self.train_name,caller=function_name,status='terminating')

                    self.sensor_manager.getSensor("MS:IS:running:{}".format(self.train_name)).setKnownState(INACTIVE)
                  
                    self.removeTrainListeners()
                    self.removeSubrouteListeners()
                    
                    if layoutConfig.trace_active_requests_locks  :
                       self.printMsg._print(function_name,"LOCK",self.train_name,'terminate requested active requests lock, thread {}'.format(threading.currentThread().getName()))
                    
                    with self.controller.active_requests[self.train_name]['speed_lock']:
                          self.controller.setActiveRequest(self.train_name,caller=function_name,status='terminated')
                    
                    if layoutConfig.trace_active_requests_locks  :
                       self.printMsg._print(function_name,"LOCK",self.train_name,'terminate releasing active requests lock, thread {}'.format(threading.currentThread().getName()))
                          
                    self.printMsg._print(function_name,'TERMINATED',self.train_name,'Request to terminate train {} complete '.format(self.train_name))    
           #====================================================================================================================
           # When the dispatcher detects that it is dispatching the last subroute in a loop it creates this listener to detect when either 
           # fwdCompleteSensor or revCompleteSensor is activated. When this happens it sets  train speed to 0 and sets the 
           # MS:IS:running:{} sensor inactive. The dispatcher is waiting on this and wakes up to process the next loop.
           #====================================================================================================================
           elif self.listener_reference=='TRAIN_{}_route_complete_SENSOR'.format(self.train_name):
              self.printMsg._print(function_name,'S_CHANGE_route_complete','system',"detected property change event : oldValue {} newValue {} for {}".format(self.old_value,self.new_value,self.source))
              
              if self.event.newValue==ACTIVE:
                 self.throttle.setSpeedSetting(0)
                 
                 if layoutConfig.trace_active_requests_locks  :
                    self.printMsg._print(function_name,"LOCK",self.train_name,'route_complete requested active reqests lock, thread {}'.format(threading.currentThread().getName()))
                    
                 with self.controller.active_requests[self.train_name]['speed_lock']: 
                      self.controller.setActiveRequest(self.train_name,caller=function_name,status='route complete')
                      loop_num=self.controller.active_requests[self.train_name]['active_loop']
                      self.removeSubrouteListeners()
                      self.removeTrainListeners()
                      
                 if layoutConfig.trace_active_requests_locks  :
                    self.printMsg._print(function_name,"LOCK",self.train_name,'route_complete releasing active_requests lock, thread {}'.format(threading.currentThread().getName()))
                 
                 self.sensor_manager.getSensor("MS:IS:running:{}".format(self.train_name)).setKnownState(INACTIVE)
                 route_direction=self.controller.active_requests[self.train_name]['route_direction']
                 self.printMsg._print(function_name,'DRIVER_C',self.train_name,'{} loop {} complete for {} '.format(route_direction,loop_num,self.train_name)) 
           #====================================================================================================================
           # If a key sensor is activated
           #====================================================================================================================
           elif self.listener_reference=='TRAIN_{}_keys_SENSOR'.format(self.train_name):
              self.printMsg._print(function_name,'S_CHANGE_keys','system',"detected property change event : oldValue {} newValue {} for {}".format(self.old_value,self.new_value,self.source)) 

              if self.event.newValue==ACTIVE:
                 #
                 # A key sensor should only trigger once so remove the property change listener
                 #
                 layoutListeners().setListener(caller=function_name+' key_sensor',sensor=self.sensor,train_name=self.train_name,mode='remove',\
                                               listener_reference='TRAIN_{}_key_SENSOR'.format(self.train_name),controller=self.controller)
                 #
                 # IF this is the MS:IS:keys:{} going active itself then ignore
                 #
                 if str(self.event.source).startswith("MS:IS:keys:") : return
                 #
                 # If the trains key_sensor is ACTIVE then do the key sequence
                 #
                 key_sensor="MS:IS:keys:{}".format(self.train_name)
                 if self.sensor_manager.getSensor(key_sensor).getKnownState()==ACTIVE:
                    for sequences in self.key_sequence:
                        exec("s=self.train_instance.{}".format(sequences))
                        for sequence in s:
                            for key,times in sequence.items():
                                delay=times[0]
                                duration=times[1]
                                #print("Pressing {} with a delay of {} and a duration of {}".format(key,delay,duration))
                                self.waitMsec(int(delay)*1000)
                                exec("self.throttle.set{}(True)".format(key))
                                self.waitMsec(int(duration)*1000)
                                if int(duration)>0:
                                   exec("self.throttle.set{}(False)".format(key))
           #====================================================================================================================
           # If the last_block_sensor changes state do this
           #====================================================================================================================
           elif self.listener_reference=='TRAIN_{}_last_block_SENSOR'.format(self.train_name):
              self.printMsg._print(function_name,'S_CHANGE_last_block','system',"detected property change event : oldValue {} newValue {} for {}".format(self.old_value,self.new_value,self.source)) 
              
              if self.event.newValue==ACTIVE:
                 #
                 # A last_block sensor should only trigger once so remove the property change listener
                 #
                 layoutListeners().setListener(caller=function_name+' last_block_sensor',sensor=self.sensor,train_name=self.train_name,mode='remove',\
                                               listener_reference='TRAIN_{}_last_block_SENSOR'.format(self.train_name),controller=self.controller)
                 
                 if layoutConfig.trace_active_requests_locks  :
                    self.printMsg._print(function_name,"LOCK",self.train_name,'last_block requested active requests lock, thread {}'.format(threading.currentThread().getName()))
                 
                 with self.controller.active_requests[self.train_name]['speed_lock']:
                      self.throttle.setSpeedSetting(0) 
                      #self.controller.setActiveRequest(self.train_name,caller=function_name,dispatcher_hold=True)
                      #self.waitMsec(100)
                      self.sensor_manager.getSensor('MS:IS:running:{}'.format(self.train_name)).setKnownState(INACTIVE)
                 
                 if layoutConfig.trace_active_requests_locks  :
                    self.printMsg._print(function_name,"LOCK",self.train_name,'last_block releasing active_requests lock, thread {}'.format(threading.currentThread().getName()))
           #====================================================================================================================
           # If this is an approach sensor that has been triggered then do this
           #====================================================================================================================
           elif self.listener_reference=='TRAIN_{}_approach_SENSOR'.format(self.train_name):
                self.printMsg._print(function_name,'S_CHANGE_approach','system',"detected property change event : oldValue {} newValue {} for {}".format(self.old_value,self.new_value,self.source)) 
                if self.event.newValue==ACTIVE:
                  self.throttle.setSpeedSetting(self.speed)
                  #
                  # A approach hold sensor should only trigger once so remove the property change listener
                  #
                  layoutListeners().setListener(caller=function_name+' approach_sensor',sensor=self.sensor,train_name=self.train_name,mode='remove',\
                                                listener_reference='TRAIN_{}_approach_SENSOR'.format(self.train_name),controller=self.controller)
                   
                  self.printMsg._print(function_name,'DRIVER_APP',self.train_name,"approach speed sensor {} triggered, setting speed to 0".format(self.sensor,self.speed),state='app_wait')
                  self.throttle.setSpeedSetting(0)
                  dispatch_hold_sensor=self.sensor_manager.getSensor('MS:IS:dispatcher_hold:{}'.format(self.train_name))
                  terminate_sensor=self.sensor_manager.getSensor('MS:IS:terminate:{}'.format(self.train_name))
                  while True:
                        self.waitChange((terminate_sensor,dispatch_hold_sensor))
                        if  terminate_sensor.getKnownState()==ACTIVE: return
                        elif dispatch_hold_sensor == INACTIVE: break
                  
                  self.printMsg._print(function_name,'DRIVER',self.train_name,"dispatcher hold released setting speed to {}".format(self.speed))
                  self.throttle.setSpeedSetting(self.speed)
           #====================================================================================================================
           # If the running sensor changes state do this
           #====================================================================================================================
           elif self.listener_reference=='TRAIN_{}_running_SENSOR'.format(self.train_name):
              self.printMsg._print(function_name,'S_CHANGE_running','system',"detected property change event : oldValue {} newValue {} for {}".format(self.old_value,self.new_value,self.source)) 
              
              if layoutConfig.trace_active_requests_locks  :
                 self.printMsg._print(function_name,"LOCK",self.train_name,'running requested active requests lock, thread {}'.format(threading.currentThread().getName()))
              with self.controller.active_requests[self.train_name]['speed_lock']:
                   if self.event.newValue==ACTIVE:
                       self.active_subroute=self.controller.active_requests[self.train_name]['active_subroute']
                      
                       self.loop_num           = self.controller.active_requests[self.train_name]['active_loop']
                       self.route_direction    = self.controller.active_requests[self.train_name]['route_direction']
                       self.throttle_direction = self.controller.active_requests[self.train_name]['throttle_direction']
                       self.speed              = self.controller.active_requests[self.train_name]['speed']
                       self.max_speed          = self.controller.active_requests[self.train_name]['max_speed']
                       if self.speed           > self.max_speed: self.speed=self.max_speed
                       
                       
                       if self.throttle_direction.upper() =='FORWARD': self.throttle.setIsForward(True)
                       else: self.throttle.setIsForward(False)
                       
                       hold_sensor_name="MS:IS:hold:{}".format(self.train_name)
                       hold_sensor=self.sensor_manager.getSensor(hold_sensor_name)
                       hold_sensor_state=hold_sensor.getKnownState()
                       
                       if hold_sensor_state!=ACTIVE:
                          self.printMsg._print(function_name,'DRIVER_SP',self.train_name,"loop {}, subroute {}, speed {}, route direction {}".format(self.loop_num,self.active_subroute,self.speed,self.route_direction),state='running')
                          self.controller.setActiveRequest(self.train_name,caller=function_name,active_loop=self.loop_num)
                          self.throttle.setSpeedSetting(self.speed)
                          #self.waitMsec(1000)
                       else:
                          self.printMsg._print(function_name,'DRIVER',self.train_name,"{} loop {} on {} delayed, hold sensor {} ACTIVE, train waiting".format(self.route_direction,self.loop_num,self.active_subroute,hold_sensor_name),state='hold')
                          self.waitMsec(500)
                          self.controller.setActiveRequest(self.train_name,caller=function_name,active_loop=self.loop_num,status='holding')  
              if layoutConfig.trace_active_requests_locks  :
                 self.printMsg._print(function_name,"LOCK",self.train_name,'running releasing active requests lock, thread {}'.format(threading.currentThread().getName()))
           #====================================================================================================================
           #
           #==================================================================================================================== 
           elif  self.listener_reference.upper()=='INTERNAL_SYSTEM_SENSOR':
               old_value=self.event.source.describeState(self.event.oldValue) 
               new_value=self.event.source.describeState(self.event.newValue)
               self.printMsg._print(function_name,'S_CHANGE_INTERNAL','system',"detected property change event : oldValue {} newValue {} for {}".format(self.old_value,self.new_value,self.source))
               value=self.event.source.describeState(self.event.source.getKnownState())
               
               print(">>>>>>>>>>>>>>>>>>>> INTERNAL_SYSTEM_SENSOR detected",self.event.source)
               
               if self.event.source.getSystemName().upper().startswith("MS:IS:TERMINATE"):
                  print("system wide termination") 
               elif self.event.source.getSystemName().upper().startswith("MS:IS:KEY:"):
                  print("system wide key activation")
               elif self.event.source.getSystemName().upper().startswith("MS:IS:WAIT:"):
                  print("system wide wait activation")
               elif self.event.source.getSystemName().upper().startswith("MS:IS:HOLD:"):
                  print("system wide hold activation")
               elif self.event.source.getSystemName().upper().startswith("MS:IS:FADE:"):
                  print("system wide fade activation")
               elif self.event.source.getSystemName().upper().startswith("MS:IS:STARTUP:"):
                  print("system wide startup activation")
        except Exception:
            print(traceback.format_exc())
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
    #======================================================================================================================================
    # Stop any train listeners - those defined in layoutConfig.command_sensors 
    # for example :
    #              TRAIN_shunt8691_terminate_SENSOR or TRAIN_shunt8691_hold_SENSOR etc.
    #======================================================================================================================================
    '''
    def removeTrainListeners(self):
        for sensor_type in layoutConfig.command_sensors:
            reference='TRAIN_{}_{}_SENSOR'.format(self.train_name,sensor_type)
            
            sensor=self.sensor_manager.getSensor("MS:IS:"+sensor_type+":"+self.train_name)
        
            layoutListeners().setListener(caller='removeTrainListeners',sensor=sensor,train_name=self.train_name,mode='remove',listener_reference=reference,controller=self.controller)
        #
        # Just in case a route complete sensor is set do this
        #
        
        route_complete_sensor_name=self.controller.active_requests[self.train_name]['route_complete_sensor_name']
        if route_complete_sensor_name !=None:
           route_complete_sensor     = self.sensor_manager.getSensor(route_complete_sensor_name)
           layoutListeners().setListener(caller='removeTrainListeners',sensor=route_complete_sensor,train_name=self.train_name,mode='remove',\
                                         listener_reference='TRAIN_{}_route_complete_SENSOR'.format(self.train_name),controller=self.controller)
    '''
    #======================================================================================================================================
    # Stop any subroute listeners - those defined dynamically for speed, wait, approach etc.  
    # for example :
    #              TRAIN_shunt8691_speed_SENSOR or TRAIN_shunt8691_wait_SENSOR etc.
    #======================================================================================================================================
    '''
    def removeSubrouteListeners(self):
        function_name='f(removeSubrouteListeners)'
        subroute_listeners=layoutConfig.subroute_listeners #('speed','wait','keys')
        
        for sensor_type in subroute_listeners:
            reference='TRAIN_{}_{}_SENSOR'.format(self.train_name,sensor_type)
            for sensor in self.sensor_manager.getNamedBeanSet().toArray():
                layoutListeners().setListener(caller='removeSubrouteListeners',sensor=sensor,train_name=self.train_name,mode='remove',listener_reference=reference,controller=self.controller)
        
        last_block_sensor_name=self.controller.active_requests[self.train_name]['last_block_sensor_name']
        
        if last_block_sensor_name !=None:
           last_block_sensor     = self.sensor_manager.getSensor(last_block_sensor_name)
           layoutListeners().setListener(caller='removeSubrouteListeners',sensor=last_block_sensor,train_name=self.train_name,mode='remove',\
                                         listener_reference='TRAIN_{}_last_block_SENSOR'.format(self.train_name),controller=self.controller) 
        return
