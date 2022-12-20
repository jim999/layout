import ast
import sys
import os

import layoutConfig
import traceback
import layoutReload
import layoutUtils as utils

if (sys.platform.startswith('java')):
    import jmri
    import layoutListeners
    import layoutJMRIUtils as jmriUtils
    from jmri_bindings import *

class jmriutils(jmri.jmrit.automat.AbstractAutomaton):

   def __init__(self,controller=None,sensor_manager=None,block_manager=None,turnout_manager=None,signal_manager=None,masts_manager=None):
       

       
       self.printMsg                 = utils.printMsg(caller='layoutController')
       self.tcpBMClient              = utils.tcpClient(caller='layoutController',manager_type='bookingmanager')
       
       self.controller               = controller
       self.utils                    = utils.utils(controller=controller)
       
       self.sensor_manager           = sensor_manager
       self.block_manager            = block_manager
       self.turnout_manager          = turnout_manager
       self.signal_manager           = signal_manager
       self.masts_manager            = masts_manager
       
       self.train_module_names       = layoutConfig.train_modules
       self.route_module_names       = layoutConfig.route_modules
         
       self.train_module_files =''
         
       for f in self.train_module_names:
           f=f.strip("'")
           f=f.strip('"')
           f=f.strip("'")
           self.train_module_files=self.train_module_files+f+" or "
             
       self.train_module_files        = self.train_module_files.rsplit(' ', 2)[0]
       
       self.route_module_files = ''
       
       for f in self.route_module_names:
           f=f.strip("'")
           f=f.strip('"')
           f=f.strip("'")
           self.route_module_files=self.route_module_files+f+" or "   
            
       self.route_module_files        = self.route_module_files.rsplit(' ', 2)[0]
       
       
   '''
   #====================================================================================================================
   # Add sensors. 
   #
   # dispatch is True if this is the dispatcher adding sensors. Therefore set all but the defined list to Inactive 
   #=====================================================================================================================
   '''
   def addSensorsAndListeners(self,train_name,flags_only=False):
       function_name='f(addSensorsAndListeners)'
       listener=layoutListeners.layoutListeners()
       for sensor_name in layoutConfig.command_sensors:
           if train_name=='system': reference='INTERNAL_SYSTEM_SENSOR'
           else: reference='TRAIN_{}_{}_SENSOR'.format(train_name,sensor_name)
           sn="MS:IS:"+sensor_name+":"+train_name

           sensor=self.sensor_manager.provideSensor(sn)
           sensor.setComment(train_name+" sensor")
           
           if train_name=='system' or sensor.getKnownState()==UNKNOWN or (sensor_name in layoutConfig.set_inactive) :
              sensor.setKnownState(INACTIVE)

           listener.setListener(caller='addSensorsAndListeners',sensor=sensor,mode='add',listener_reference=reference,train_name=train_name,controller=self.controller)
   '''
   #=========================================================================================================================================
   # start the booking manager - a python module that runs outside of jmri and jython.
   #=========================================================================================================================================
   '''
   def startBmgr(self):
       function_name="f(startBmgr)"

       self.stopBmgr()
      
       status=os.system(layoutConfig.booking_manager_program+"&")
       
       if status!=0:
          self.printMsg._print(function_name,"ERROR","system","failed to start {} ".format(layoutConfig.booking_manager_program))
          return False
       
       self.waitMsec(500)
       
       ok=False
       
       for _ in range(20):
          try:
             resp=self.tcpBMClient.sendData(data="{'cmd':'are_you_ready'}")
             try:
                resp=ast.literal_eval(resp)
                if resp['cmd_successful']: 
                   ok=True
                   break
             except:
                    pass
                    
          except:
             print(traceback.format_exc(),resp)
             ok=False 
             pass 
          self.waitMsec(100)
       
       self.printMsg._print(function_name,"BKMGR_STARTED","system","booking manager running ")
       return ok
   '''
   #=========================================================================================================================================
   # Stop the booking manager, quiet True will supress the connection refused error message. 
   #=========================================================================================================================================
   '''
   def stopBmgr(self):
       try:
          import os, signal
          for line in os.popen("ps ax | grep layoutBKManager | grep -v grep"):
              fields = line.split()
              pid = fields[0]
              os.kill(int(pid), signal.SIGKILL)
         
       except Exception as err:
           print(err)
   '''
   #-------------------------------------------------------------------------------------------------------
   # Set the power state
   #-------------------------------------------------------------------------------------------------------
   '''
   def togglePower(self):
       power = jmri.InstanceManager.getDefault(jmri.PowerManager).getPower() 
       if power==2:
          jmri.InstanceManager.getDefault(jmri.PowerManager).setPower(4)
          self.waitMsec(200)
          jmri.InstanceManager.getDefault(jmri.PowerManager).setPower(2)
       else:
          jmri.InstanceManager.getDefault(jmri.PowerManager).setPower(2)
          self.waitMsec(200)
          jmri.InstanceManager.getDefault(jmri.PowerManager).setPower(4)

   '''
   #==========================================================================================================================================
   # Check that all the resources needed to run the train are defined in the system some where (routes, sensors, turnouts etc)
   #
   # The request is a dictionary in the form {'manager': 'controller', 'route': 'testroute1', 'cmd': 'dispatch', 'train': 'shunt3026'}
   # and is the original request sent in from the user
   #
   #
   # 1. create an intial request entry
   # 2. get the train module from disk and validate it
   # 3. get the route module from disk and validate it
   # 4  check that the route is defined correctly
   # 5. hand over to the dispatcher to build the route and dispatch the train
   # 
   #==========================================================================================================================================
   '''
   def checkTrainRoute(self,request):
       try:
           function_name='f(checkTrainRoute)'
           train_instance = None
           route_instance = None
           resp={}
           #
           # Get a train module and route module from disk
           #    
           train_instance=self.utils.getModule(request['train'],self.train_module_names) 
           
           if train_instance!=None:
              cmd_successful=False
              error_code=4202                                                                     
              error_message='Route {} not found in {}'.format(request['route'],self.route_module_files) 
              route_instance=self.utils.getModule(request['route'],self.route_module_names)
           else:
              cmd_successful=False
              error_code=4201     
              error_message='Train {} not found in {}'.format(request['train'],self.train_module_files)  
           #
           # check that the route is defined correctly
           #
           if train_instance!=None and route_instance!=None:
               
              if 'wait' in request and (request['wait']=='True'       or request['wait']==True): wait=True
              else: wait=False
              if 'keys' in request and (request['keys']=='True'       or request['keys']==True): keys=True
              else: keys=False
              if 'fade' in request and (request['fade']=='True'       or request['fade']==True): fade=True
              else: fade=False
              if 'startup' in request and (request['startup']=='True' or request['startup']==True): startup=True
              else: startup=False
              if 'sound' in request and (request['sound']=='True'     or request['sound']==True): sound=True
              else: sound=False
              if 'hold' in request and (request['hold']=='True'       or request['hold']==True): hold=True
              else: hold=False
              
              if 'loops' in request : loops=int(request['loops'])
              else: loops=2
              if 'retrys' in request : retrys=int(request['retrys'])
              else: retrys=99999
              
              
              if 'look_ahead'in request: 
                  look_ahead = request['look_ahead'] 
              else: look_ahead = 1
              
              if 'route_direction' in request: route_direction  = request['route_direction']
              else: route_direction='FORWARD'
            
              if 'throttle_direction' in request: 
                 throttle_direction  = request['throttle_direction']
              else: throttle_direction='FORWARD'
              
              if 'mode'      in request: mode       = request['mode']
              else: mode = 'BACKANDFORTH'
              
              self.controller.setActiveRequest(request['train'],caller=function_name,train_instance=train_instance,route_instance=route_instance,\
                                                     status='validating',status_reason='route',retrys=retrys,\
                                                     loops=loops,fade=fade,wait=wait,keys=keys,startup=startup,sound=sound,\
                                                     hold=hold,look_ahead=look_ahead,mode=mode,route_direction=route_direction,throttle_direction=throttle_direction)
              
              self.printMsg._print(function_name,'VALIDATE',request['train'],'Validating dispatch request for train {} on route {}'.format(request['train'],route_instance),state='VALIDATING') 
              
              if not self.isRouteOK(request['train'],request['route'],route_instance):
                 cmd_successful=False
                 error_code=4204  
    
                 error_message='A component for route {} defined in {} is invalid or not found'.format(request['route'],str(route_instance)) 
                 resp={}
                 self.printMsg._print(function_name,'ERROR',request['train'],'Validating dispatch request for train {} on route {} failed'.format(request['train'],request['route']),state='V_FAIL') 
                 self.controller.setActiveRequest(request['train'],caller=function_name,status_reason="VALIDATION FAILED",status_code=6005)
              #
              # respond to the user
              #
              else:
                 self.controller.setActiveRequest(request['train'],caller=function_name,status='validated',status_reason='route',status_code=6001) 
                 self.printMsg._print(function_name,'VALIDATE',request['train'],'Request for train {} on route {} validated'.format(request['train'],request['route']),state='VALIDATED')
                 cmd_successful=True
                 error_code=0        
                 error_message='' 
                 resp=request
           else:
              self.controller.setActiveRequest(request['train'],caller=function_name,status='validate',status_reason='train or route not defined',status_code=6006) 
              self.printMsg._print(function_name,'ERROR',request['train'],'Request for train {} on route {} failed train or route not defined'.format(request['train'],request['route']),state='V_FAIL')
              cmd_successful=False
              resp=request 
           return cmd_successful,error_code,error_message,resp
       except:
          print(traceback.format_exc())
   '''
   #==========================================================================================================================================
   # check if a route is defined correctly
   #==========================================================================================================================================
   '''
   def isRouteOK(self,train,route,route_instance):
       try:
          function_name='f(isRouteOK)'
          defined_correctly=True
          #---------------------------------------------------------------------------------------------------------------
          # Check the forward and reverse complete sensors are defined for the route and exist in the jmri table
          #---------------------------------------------------------------------------------------------------------------
          try:
             if route_instance.fwdCompleteSensor and route_instance.revCompleteSensor:
                 s=self.sensor_manager.getSensor(route_instance.fwdCompleteSensor)
                 if s==None: 
                    self.printMsg._print(function_name,'WARNING',train,\
                                        "fwdCompleteSensor {} sensor is missing from the sensor table".format(route_instance.fwdCompleteSensor,state="DEF_ERROR"))
                    defined_correctly=False
                 s=self.sensor_manager.getSensor(route_instance.revCompleteSensor)
                 if s==None: 
                    self.printMsg._print(function_name,'WARNING',train,\
                                        "revCompleteSensor {} sensor is missing from the sensor table".format(route_instance.revCompleteSensor,state="DEF_ERROR"))
                    defined_correctly=False
          except Exception:
                print(traceback.format_exc())
                self.printMsg._print(function_name,'WARNING',train,\
                                    "fwdCompleteSensor {} or revCompleteSensor {} sensors are not defined in route {} or are missing from the sensor table".format(route_instance.fwdCompleteSensor,route_instance.revCompleteSensor,route,state="DEF_ERROR"))
                defined_correctly=False
          #------------------------------------------------------------------------------------------------------------
          # check that the default time and speed settings are defined for the route 
          #-------------------------------------------------------------------------------------------------------------
          for definition in ("fwdWaitTimeDefault"   , "revWaitTimeDefault",\
                             "revStartSpeedDefault" , "fwdStartSpeedDefault",\
                             "revAppSpeedDefault"   , "fwdAppSpeedDefault",\
                             "appSpeedDefault"      , "maxSpeed"):
             try:
                definitionToCheck=eval("route_instance.{}".format(definition))
                
                if not ((isinstance(definitionToCheck,int) or isinstance(definitionToCheck,float))): 
                   self.printMsg._print(function_name,"WARNING",train,"{} for route {} must be a float or int".format(definition,route),state='DEF_ERROR')
                   defined_correctly=False 
             except Exception as err:
                   self.printMsg._print(function_name,"ERROR",train,"{} not defined in {} {}".format(definition,route,err ),state='DEF_ERROR')
                   defined_correctly=False
          #------------------------------------------------------------------------------------------------------------
          # check all required blocks are defined in the jmri blocks table
          #------------------------------------------------------------------------------------------------------------
          for definition in ("routePathBlocks",):
             try:
                definitionToCheck=eval("route_instance.{}".format(definition))
                if not isinstance(definitionToCheck,tuple):
                  self.printMsg._print(function_name,"WARNING",train,"routePathBlocks in route file {} for route {} missing or not a tuple".format(routes_file,route),state='DEF_ERROR')
                  defined_correctly=False
                for block in definitionToCheck:
                    if not self.block_manager.getBlock(block):
                       self.printMsg._print(function_name,"WARNING",train,"block {} for route {} in route file {} is not defined in jmri block table".format(block,route,route_instance),state='DEF_ERROR')
                       defined_correctly=False
             except Exception as err:
                   self.printMsg._print(function_name,"ERROR",train,traceback.format_exc(),state='ERROR')
                   defined_correctly=False
          #---------------------------------------------------------------------------------
          # Test route path sensors exits in jmri sensors table
          #---------------------------------------------------------------------------------------
          for definition in ("routePathSensors",):
             try:
                definitionToCheck=eval("route_instance.{}".format(definition))
                if isinstance(definitionToCheck,tuple)==False:
                   self.printMsg._print(function_name,"WARNING",train,"{} in route file {} for route {} missing or not a tuple".format(definition,routes_file,route),state='DEF_ERROR')
                   defined_correctly=False
                for sensor in definitionToCheck:
                    if not self.sensor_manager.getSensor(sensor):
                      self.printMsg._print(function_name,"WARNING",train,"{} ({})  in route file {} for route {} not defined in jmri sensor table".format(definition,definitionToCheck,route_instance,route))
                      defined_correctly=False
             
             except Exception as err:
                   self.printMsg._print(function_name,"ERROR",train,"{}".format(traceback.format_exc()),state='ERROR')
                   defined_correctly=False
          #------------------------------------------------------
          # test turnouts. Note: turnouts are optional
          #------------------------------------------------------
          try:
             if not isinstance(route_instance.turnouts,dict):
                self.printMsg._print(function_name,"WARNING",train,"turnouts in route file {} for route {} missing or not a dict".format(route_instance,route),state='DEF_ERROR')
             for turnout_sensor,turnout_names in route_instance.turnouts.items():
                 if not self.sensor_manager.getSensor(turnout_sensor):
                    defined_correctly=False
                    self.printMsg._print(function_name,"WARNING",train,"turnout sensor {} for route {} in route file {} is not defined in jmri sensor table".format(turnout_sensor,route,route_instance),state='DEF_ERROR')
                 else:
                    for turnout_name in turnout_names:
                        if not self.turnout_manager.getTurnout(turnout_name):
                           defined_correctly=False
                           self.printMsg._print(function_name,"WARNING",train,"turnout {} for route {} in route file {} is not defined in jmri turnout table".format(turnout_name,route,route_instance),state='DEF_ERROR')
                        if turnout_names[turnout_name].upper() not in ("THROWN","CLOSED","OPEN"):
                           defined_correctly=False
                           self.printMsg._printMsg(function_name,"WARNING",train,"turnout {} defintion ({}) for route {} in route file {} needs to be OPEN, CLOSED, or THROWN".format(turnout_name,turnout_names[turnout_name],route,routes_file),state="DEF_ERROR")
          except Exception as err:
                self.printMsg._print(function_name,'ERROR',train,"{}".format(traceback.format_exc()),state='ERROR')
                defined_correctly=False
          #------------------------------------------------------------------------------------------
          # Test fwdWaitTimeByTrain,revWaitTimeByTrain,fwdStartTimeByTrain and revStartTimeByTrain
          # Note: this is optional - if not specided the defaultWaitTime will be used
          #------------------------------------------------------------------------------------------
          for definition in ("fwdWaitTimeByTrain","revWaitTimeByTrain","fwdStartSpeedByTrain","revStartSpeedByTrain"):
              try:
                 definitionToCheck=eval("route_instance.{}".format(definition))
                 if not isinstance(definitionToCheck,dict):
                    defined_ok=False
                    self.printMsg._print(function_name,"WARNING",train,"{} in route file {} for route {} missing or not a dict".format(definition,route_instance,route),state='DEF_ERROR')
                 if train in definitionToCheck:
                    if (isinstance(definitionToCheck[train],int) or isinstance(definitionToCheck[train],float)):
                        pass
                    else:
                       defined_correctly=False
                       self.printMsg._print(function_name,"WARNING",train,"{} ({}) in route file {} for route {} not a float or int".format(definition,definitionToCheck[train],route_instance,route),state='DEF_ERROR')
              except Exception as err:
                    defined_correctly=False
                    self.printMsg._print(function_name,"ERROR",train,"{}".format(traceback.format_exc()),state='ERROR')
          #---------------------------------------------------------------------------------------------------------
          #  fwdSpeedSensorsByTrain, revSpeedSensorsByTrain, fwdAppStopSensorsByTrain, fwdAppStopSensorsByTrain
          #  
          # For example if fwdSpeedSenosrByTrain is as follows
          #
          #  train        booked block       speed sesnor      speed
          #
          # {"shunt3026":{"MS:BS:BS01_4"  :{"MS:PS:PS01_14999" :0.10},
          #               "MS:BS:BS01_5"  :{"MS:BS:BS01_5"  :0.05},
          #               "MS:BS:BS01_12" :{"MS:BS:BS01_12" :0.15}
          #               }
          # }
          #
          # Note if not defined then the default approach speed will be used
          #
          #------------------------------------------------------------------------------------------------------------
          
          for definition in ("fwdSpeedSensorsByTrain"  , "revSpeedSensorsByTrain",\
                             "fwdAppStopSensorsByTrain", "revAppStopSensorsByTrain",\
                             "fwdWaitSensorsByTrain"   , "revWaitSensorsByTrain",\
                             "fwdKeySensorsByTrain"    , "revKeySensorsByTrain"):
                                 
              try:
                 definitionToCheck=eval("route_instance.{}".format(definition))
                 if not (isinstance(definitionToCheck,dict) or isinstance(definitionToCheck[train],dict)):
                    defined_correctly=False
                    self.printMsg._print(function_name,"WARNING",train,"{} in route file {} for route {} missing or not a dict".format(definition,route_instance,route),state='DEF_ERROR')
                 
                 if train not in definitionToCheck:
                    continue
                 
                 for booked_block in definitionToCheck[train]:
                     if not isinstance(definitionToCheck[train][booked_block],dict):
                        defined_correctly=False
                        self.printMsg._print(function_name,"WARNING",train,"{} booked block sensor {} in route file {} for route {} missing or not a dict".format(definition,booked_block,route_instance,route),state='DEF_ERROR')
                        
                     elif not self.sensor_manager.getSensor(booked_block):
                          defined_correctly=False
                          self.printMsg._print(function_name,"WARNING",train,"{} booked block sensor {} in route file {} for route {} is not defined in the JMRI sensor table".format(definition,booked_block,route_instance,route),state='DEF_ERROR')
                     else:
                          speed_sensor=definitionToCheck[train][booked_block]
                          if not isinstance(speed_sensor,dict):
                             defined_correctly=False
                             self.printMsg._print(function_name,"WARNING",train,"{} speed/approach sensor {} in route file {} for route {} missing or not a dict".format(definition,speed_sensor,route_instance,route),state='DEF_ERROR')
                          else:
                             for k,v in speed_sensor.items():
                                 if not self.sensor_manager.getSensor(k):
                                    defined_correctly=False
                                    self.printMsg._print(function_name,"WARNING",train,"{} speed/approach sensor {} in route file {} for route {} is not defined in th JMRI sensor table".format(definition,k,route_instance,route),state='DEF_ERROR')
                                    
                                 if definition in ("fwdSpeedSensorsByTrain"  , "revSpeedSensorsByTrain",\
                                                   "fwdAppStopSensorsByTrain", "revAppStopSensorsByTrain",\
                                                   "fwdWaitSensorsByTrain"   , "revWaitSensorsByTrain"):
                                    if not (isinstance(v,int) or isinstance(v,float)):
                                       defined_correctly=False
                                       self.printMsg._print(function_name,"WARNING",train,"{} speed {} for speed sensor {} in route file {} for route {} is not a float or int".format(definition,v,k,route_instance,route),state='DEF_ERROR')
                                 elif definition in ("fwdKeySensorsByTrain"   , "revKeySensorsByTrain"):
                                      if not (isinstance(v,tuple)):
                                         defined_correctly=False
                                         self.printMsg._print(function_name,"WARNING",train,"{} key sequence {} for sensor {} in route file {} for route {} is not a tuple".format(definition,v,k,route_instance,route),state='DEF_ERROR')
                                         for key_seq in v:
                                             if not isinstance(key_seq,str):
                                                 defined_correctly=False
                                                 self.printMsg._print(function_name,"WARNING",train,"{} key sequence {} for in {} in route file {} for route {} is not a tuple".format(definition,key_deq,v,route_instance,route),state='DEF_ERROR')
              except Exception as err:
                 defined_correctly=False
                 self.printMsg._print(function_name,"ERROR",train,"Exception detected {}".format(traceback.format_exc()),state='ERROR')
          #-------------------------------------------------------------
          # Test that all required forward signals are defined
          #--------------------------------------------------------------
          try:
             
             for route_signals in (route_instance.fwdSignals,route_instance.revSignals):
                 if not isinstance(route_signals,dict):
                    defined_correctly=False
                    self.printMsg._print(function_name,"WARNING",train,"signals in route file {} for route {} missing or not a dict".format(route_instance,route),state='DEF_ERROR')
                 
                 for booked_block_sensor_name,signal_mast_names in route_signals.items():
                     if not self.sensor_manager.getSensor(booked_block_sensor_name.strip()):
                        defined_correctly=False
                        self.printMsg._print(function_name,"WARNING",train,"signals block sensor {} for route {} in route file {} is not defined in jmri sensor table".format(booked_block_sensor_name,route,route_instance),state='DEF_ERROR')
                     
                     for signal_masts in signal_mast_names:
                         for signal_mast in signal_masts:
                             if not self.masts_manager.getSignalMast(signal_mast.strip()):
                                defined_correctly=False
                                self.printMsg._print(function_name,"WARNING",train,"signal mast {} for route {} in route file {} is not defined in jmri signal head table".format(signal_mast,route,route_instance),state='DEF_ERROR')
          
          except Exception as err:
               defined_correctly=False
               self.printMsg._print(function_name,"ERROR",train,"error in route file {} for route {} {}".format(route_instance,route,traceback.format_exc()),state='ERROR')
       except Exception as err:
         self.printMsg._print(function_name,"ERROR",train,"Exception detected {}".format(traceback.format_exc()),state='ERROR')
         defined_correctly=False
       return defined_correctly
       
       
       
       
       
       
       
       
       
       
       
       
                                            
       
       
       
       
       
       
       
